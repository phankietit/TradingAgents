"""Original native LangGraph through spawn; synthetic models, no provider calls."""

import hashlib
import json
from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage, RemoveMessage
from langgraph.checkpoint.memory import InMemorySaver
from sqlalchemy import select

from tests.test_analysis_engine import _instrument
from tests.test_durable_jobs import _database, _enqueue
from tests.test_risk_engine import NOW
from tests.test_snapshot_analysis import context
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph import trading_graph
from tradingagents.platform.analysis import AnalysisEngine, AnalysisRequest
from tradingagents.platform.analysis.checkpoint_codec import SnapshotCheckpointCodec
from tradingagents.platform.analysis.checkpoint_saver import CommittedSnapshotSaver
from tradingagents.platform.analysis.checkpoint_store import PrivateCheckpointStore
from tradingagents.platform.analysis.observer import STAGES, ResearchObserver
from tradingagents.platform.analysis.snapshots import AnalysisSnapshot
from tradingagents.platform.analysis.supervision import SupervisedAnalysisEngine
from tradingagents.platform.jobs import DurableJobQueue
from tradingagents.platform.jobs.worker import JobExecutionContext
from tradingagents.platform.persistence.models import ResearchCheckpointRow


class NativeFixtureEngine:
    supports_checkpoint_bridge = True  # Fixture-only explicit recording hook.
    def __init__(self, *, base_config=None):
        self.config = base_config
        self.model_trace = []
        self.resume_evidence = None
        self.encoded_checkpoints = []
        self.checkpoint_commit = None
        self.checkpoint_read = None

    def analyze(self, request):
        source_id = str(request.snapshot_context.by_analyst["market"][0].manifest.snapshot_id)
        options = []
        repairs = []
        invalid_translation = self.config.get("_fixture_invalid_translation", False)
        interrupted_node = self.config.get("_fixture_interrupt_after")
        original_propagate = trading_graph.TradingAgentsGraph.propagate_snapshots

        def trace(kind, prompt):
            # Compare actual downstream inputs, not merely a constant fake result.
            content = prompt if isinstance(prompt, str) else [
                item.content if hasattr(item, "content") else item for item in prompt]
            self.model_trace.append((kind, content))

        def resume_without_messages(graph, *args, **kwargs):
            codec = SnapshotCheckpointCodec(fingerprint="a" * 64, nodes=graph.workflow.nodes)

            def new_saver():
                return (CommittedSnapshotSaver(codec=codec, commit=self.checkpoint_commit)
                        if self.checkpoint_commit else InMemorySaver())

            saver = new_saver()
            graph.graph = graph.workflow.compile(checkpointer=saver,
                                                 interrupt_after=[interrupted_node])
            graph_args = graph.propagator.get_graph_args(
                callbacks=[graph.execution_observer] if graph.execution_observer else None)
            thread_id = self.config.get("_fixture_thread_id", "synthetic-resume")
            graph_args["config"]["configurable"] = {"thread_id": thread_id}
            if self.checkpoint_commit:
                graph_args["durability"] = "sync"
            invoke = graph.graph.invoke

            def initial_invoke(state, **unused):
                return invoke(state, **graph_args)

            with patch.object(graph.graph, "invoke", initial_invoke):
                original_propagate(graph, *args, **kwargs)
            before = graph.graph.get_state(graph_args["config"])
            assert before.next, "fixture must interrupt before graph completion"
            calls_before = len(self.model_trace)
            if self.config.get("_fixture_json_checkpoint"):
                # Every version is reviewed, including initial/pending writes;
                # never serialize the entire InMemorySaver object.
                self.encoded_checkpoints = [codec.encode(item) for item in saver.list(graph_args["config"])]
                pending = self.config.get("_fixture_pending_checkpoint", False)
                raw = self.encoded_checkpoints[1 if pending else 0]
                if self.checkpoint_read:
                    raw = self.checkpoint_read(raw)
                restored = codec.decode(raw)
                if pending:
                    assert restored.pending_writes, "fixture must restore completed pending writes"
                saver = new_saver()
                saved_config = saver.put(restored.parent_config or {"configurable": {
                    "thread_id": thread_id, "checkpoint_ns": ""}}, restored.checkpoint,
                    restored.metadata, restored.checkpoint["channel_versions"])
                grouped = {}
                for task, channel, value in restored.pending_writes:
                    grouped.setdefault(task, []).append((channel, value))
                for task, writes in grouped.items():
                    saver.put_writes(saved_config, writes, task)
                graph.graph = graph.workflow.compile(checkpointer=saver)
            else:
                graph.graph.update_state(graph_args["config"], {
                    "messages": [RemoveMessage(id=item.id) for item in before.values["messages"]]},
                    as_node=interrupted_node)
            clean = graph.graph.get_state(graph_args["config"])
            assert clean.values["messages"] == []
            if not self.config.get("_fixture_pending_checkpoint"):
                assert clean.next == before.next
            # Recompile the original workflow with the same saver and no interrupt.
            graph.graph = graph.workflow.compile(checkpointer=saver)
            with graph.config_scope():
                final = graph.graph.invoke(None, **graph_args)
            self.resume_evidence = (before.next, calls_before)
            structured = final.get("structured_decision")
            return final, structured.get("rating", "REVIEW") if structured else "REVIEW"

        def translate(prompt):
            blocks = json.loads(prompt.split("<translation_blocks>\n", 1)[1]
                                .split("\n</translation_blocks>", 1)[0])
            wording = {"Research only": "Chỉ phục vụ nghiên cứu",
                "Snapshot thesis": "Luận điểm từ dữ liệu đã lưu", "Coverage risk": "Rủi ro phạm vi dữ liệu",
                "New information": "Thông tin mới"}
            result = [{"block_id": block["block_id"], "vi": wording.get(block["en"],
                       block["en"].replace("months", "tháng"))} for block in blocks]
            if invalid_translation:
                result[0]["vi"] += " 25%"
            return {"blocks": result}

        def committed_without_resume(graph, *args, **kwargs):
            bridge = request.execution_observer
            codec = SnapshotCheckpointCodec(fingerprint=bridge.checkpoint_options["fingerprint"],
                                            nodes=graph.workflow.nodes)
            saver = CommittedSnapshotSaver(codec=codec, commit=bridge.commit_checkpoint)
            return original_propagate(graph, *args, **kwargs,
                checkpoint_saver=saver,
                checkpoint_thread_id=bridge.checkpoint_options["thread_id"])

        class Model:
            def invoke(self, prompt):
                trace("plain", prompt)
                if isinstance(prompt, str) and "FORMAT REPAIR:" in prompt:
                    repairs.append(1)
                    return AIMessage(content=json.dumps(translate(prompt), ensure_ascii=False))
                return AIMessage(content="Synthetic analysis; coverage remains uncertain.")

            def with_structured_output(self, schema):
                if schema.__name__ == "ReportTranslation":
                    def translated(prompt):
                        trace(schema.__name__, prompt)
                        return schema.model_validate(translate(prompt))
                    return SimpleNamespace(invoke=translated)
                claims = [{"claim": claim, "snapshot_ids": [source_id]}
                          for claim in ("Snapshot thesis", "Coverage risk", "New information")]
                values = {
                    "SentimentReport": {"overall_band": "Mixed", "overall_score": 5,
                        "confidence": "low", "narrative": "Synthetic limited source sentiment."},
                    "ResearchPlan": {"recommendation": "Hold", "rationale": "Snapshot evidence",
                        "strategic_actions": "Review"},
                    "TraderProposal": {"action": "Hold", "reasoning": "Research only"},
                    "PortfolioDecision": {"rating": "Hold", "executive_summary": "Research only",
                        "investment_thesis": "Snapshot thesis", "confidence": .5,
                        "risks": ["Coverage risk"], "invalidation_conditions": ["New information"],
                        "evidence_claims": claims, "time_horizon": "3–6 months"},
                }
                if "quantity_bindings" in schema.model_fields:
                    payload = values["PortfolioDecision"]
                    payload.pop("evidence_claims")
                    payload.update(investment_thesis=[claims[0]], risks=[claims[1]],
                                   invalidation_conditions=[claims[2]])
                def structured(prompt):
                    trace(schema.__name__, prompt)
                    return schema.model_validate(values[schema.__name__])
                return SimpleNamespace(invoke=structured)

        def client(**kwargs):
            options.append(kwargs)
            return SimpleNamespace(get_llm=lambda: Model())

        def forbidden(*args, **kwargs):
            raise AssertionError("native snapshot graph accessed a legacy write/tool/memory path")

        with ExitStack() as patches:
            if interrupted_node:
                patches.enter_context(patch.object(trading_graph.TradingAgentsGraph,
                    "propagate_snapshots", resume_without_messages))
            elif getattr(request.execution_observer, "checkpoint_options", None) is not None:
                patches.enter_context(patch.object(trading_graph.TradingAgentsGraph,
                    "propagate_snapshots", committed_without_resume))
            patches.enter_context(patch.object(trading_graph, "create_llm_client", client))
            patches.enter_context(patch.object(trading_graph, "TradingMemoryLog", forbidden))
            for name in ("_create_tool_nodes", "resolve_instrument_context", "_resolve_pending_entries",
                         "record_decision", "_log_state", "begin_checkpoint"):
                patches.enter_context(patch.object(trading_graph.TradingAgentsGraph, name, forbidden))
            result = AnalysisEngine(base_config=self.config).analyze(request)
        assert all(item["timeout"] == 600 and item["max_retries"] == 1 for item in options)
        assert len(repairs) == (1 if invalid_translation else 0)
        return result


@pytest.mark.parametrize("language,invalid", [("English", False), ("Vietnamese", False),
    ("English and Vietnamese", False), ("English and Vietnamese", True)])
@pytest.mark.parametrize("committed_bridge", [False, True])
def test_all_fourteen_native_stages_survive_spawn_bridge_and_original_gates(tmp_path, language, invalid, committed_bridge):
    instrument = _instrument()
    inputs = context(instrument)
    analysts = ("market", "social", "news", "fundamentals")
    original = inputs.by_analyst["market"][0]
    extras = {role: (AnalysisSnapshot(manifest=original.manifest.model_copy(update={
        "snapshot_id": uuid4(), "dataset": role}), payload=original.payload),)
        for role in analysts if role != "market"}
    inputs = inputs.model_copy(update={"by_analyst": {**inputs.by_analyst, **extras},
                                      "source_max_age_seconds": dict.fromkeys(analysts, 0)})
    captures, events = [], []
    observer = ResearchObserver(check_cancelled=lambda: None, emit=lambda *args: events.append(args),
        max_seconds=60, save_stage=lambda stage, outputs: captures.append((stage, outputs)) or uuid4())
    config = {**DEFAULT_CONFIG, "data_cache_dir": str(tmp_path / "cache"),
        "results_dir": str(tmp_path / "reports"), "max_debate_rounds": 1,
        "max_risk_discuss_rounds": 1, "output_language": language,
        "_fixture_invalid_translation": invalid}
    database = None
    bridge_options = {}
    if committed_bridge:
        from datetime import timedelta

        database, owner, run = _database(tmp_path / "parent-checkpoints")
        _enqueue(database, owner, run)
        with database.session() as session:
            job = DurableJobQueue(session).claim("fixture", lease_for=timedelta(minutes=5), now=NOW)
        job_context = JobExecutionContext(database, job.job_id, "fixture", timedelta(minutes=5), lambda: NOW)
        nodes = STAGES | {"Msg Clear Market", "Msg Clear Sentiment", "Msg Clear News", "Msg Clear Fundamentals"}
        codec = SnapshotCheckpointCodec(fingerprint="a" * 64, nodes=nodes)
        store = PrivateCheckpointStore(codec=codec)
        bridge_options = {"checkpoint_codec": codec, "checkpoint_thread_id": str(run.run_id),
                          "checkpoint_commit": lambda raw: store.commit(context=job_context,
                              owner_id=owner, run_id=run.run_id, raw=raw)}
    result = SupervisedAnalysisEngine(base_config=config, engine_factory=NativeFixtureEngine,
                                     **bridge_options).analyze(
        AnalysisRequest(instrument=instrument, analysis_date=NOW.date(), selected_analysts=analysts,
                        snapshot_context=inputs, execution_observer=observer))
    expected = ["Market Analyst", "Sentiment Analyst", "News Analyst", "Fundamentals Analyst",
        "Bull Researcher", "Bear Researcher", "Research Manager", "Trader", "Aggressive Analyst",
        "Conservative Analyst", "Neutral Analyst", "Portfolio Manager", "Financial validation",
        "Report presentation"]
    assert observer.completed == expected and set(expected) == STAGES
    assert [payload["stage"] for kind, payload in events if kind == "stage.completed"] == expected
    assert result.selected_analysts == analysts
    if invalid:
        assert result.decision_payload is None
        assert "report_translation_unavailable" in result.validation_issues
        assert result.final_state["structured_decision"].get("localized_report") is None
        assert len([item for item in result.final_state["structured_diagnostics"]
                    if item["agent"] == "Report translation"]) == 2
    else:
        assert result.decision_payload.thesis == "Snapshot thesis"
        if language != "English":
            localized = result.final_state["structured_decision"]["localized_report"]
            assert "Chỉ phục vụ nghiên cứu" in localized["vi"]
            assert "3–6 tháng" in localized["vi"] and "3–6 months" in localized["en"]
            assert result.final_state["structured_decision"]["investment_thesis"] == "Snapshot thesis"
            presentation = dict(captures)["Report presentation"]["structured_decision"]["localized_report"]
            assert presentation == localized
    assert result.narrative_signal == "Hold"
    assert observer.receipt()["supervision_mode"] == "spawned_process"
    assert observer.receipt()["usage"]["status"] == "incomplete"  # Fake model, not provider usage proof.
    assert "messages" not in result.final_state
    assert all("messages" not in outputs for _, outputs in captures)
    assert list((tmp_path / "reports").iterdir()) == []
    if database is not None:
        with database.session() as session:
            rows = session.scalars(select(ResearchCheckpointRow)).all()
            assert len(rows) > 17
            assert all(row.owner_id == owner and row.run_id == run.run_id for row in rows)
            assert store.load_latest(session=session, owner_id=owner, run_id=run.run_id) is not None
        database.dispose()


@pytest.mark.parametrize("json_checkpoint,pending_checkpoint,committed", [
    (False, False, False), (True, False, False), (True, True, False),
    (True, False, True), (True, True, True)])
@pytest.mark.parametrize("language,invalid", [("English", False), ("Vietnamese", False),
    ("English and Vietnamese", False), ("English and Vietnamese", True)])
@pytest.mark.parametrize("boundary", ["Market Analyst", "Msg Clear Market", "Sentiment Analyst",
    "Msg Clear Sentiment", "News Analyst", "Msg Clear News", "Fundamentals Analyst",
    "Msg Clear Fundamentals", "Bull Researcher", "Bear Researcher",
    "Research Manager", "Trader", "Aggressive Analyst", "Conservative Analyst", "Neutral Analyst",
    "Portfolio Manager", "Financial validation"])
def test_native_resume_message_removal_preserves_prompts_and_results(tmp_path, boundary, json_checkpoint, pending_checkpoint, committed, language, invalid):
    """Characterization only; not a production checkpoint or authorized paid replay."""
    instrument = _instrument()
    inputs = context(instrument)
    analysts = ("market", "social", "news", "fundamentals")
    original = inputs.by_analyst["market"][0]
    extras = {role: (AnalysisSnapshot(manifest=original.manifest.model_copy(update={
        "snapshot_id": uuid4(), "dataset": role}), payload=original.payload),)
        for role in analysts if role != "market"}
    inputs = inputs.model_copy(update={"by_analyst": {**inputs.by_analyst, **extras},
                                      "source_max_age_seconds": dict.fromkeys(analysts, 0)})
    config = {**DEFAULT_CONFIG, "data_cache_dir": str(tmp_path / "cache"),
        "results_dir": str(tmp_path / "reports"), "max_debate_rounds": 2,
        "max_risk_discuss_rounds": 2, "output_language": language,
        "_fixture_invalid_translation": invalid}
    database = None
    if committed:
        from datetime import timedelta

        database, owner, run = _database(tmp_path / "private-checkpoints")
        _enqueue(database, owner, run)
        with database.session() as session:
            job = DurableJobQueue(session).claim("fixture", lease_for=timedelta(minutes=5), now=NOW)
        job_context = JobExecutionContext(database, job.job_id, "fixture", timedelta(minutes=5), lambda: NOW)
        # Reviewed native node set; synthetic fingerprint only, not consent.
        nodes = {"Market Analyst", "Msg Clear Market", "Sentiment Analyst", "Msg Clear Sentiment",
            "News Analyst", "Msg Clear News", "Fundamentals Analyst", "Msg Clear Fundamentals",
            "Bull Researcher", "Bear Researcher", "Research Manager", "Trader", "Aggressive Analyst",
            "Conservative Analyst", "Neutral Analyst", "Portfolio Manager", "Financial validation",
            "Report presentation"}
        store = PrivateCheckpointStore(codec=SnapshotCheckpointCodec(fingerprint="a" * 64, nodes=nodes))
        config["_fixture_thread_id"] = str(run.run_id)
    results, traces, completions = [], [], []
    for interruption in (None, boundary):
        observer = ResearchObserver(check_cancelled=lambda: None, emit=lambda *args: None,
                                    max_seconds=60)
        engine = NativeFixtureEngine(base_config={**config, "_fixture_interrupt_after": interruption,
            "_fixture_json_checkpoint": json_checkpoint, "_fixture_pending_checkpoint": pending_checkpoint})
        if committed and interruption:
            engine.checkpoint_commit = lambda raw: store.commit(context=job_context,
                owner_id=owner, run_id=run.run_id, raw=raw)

            def read_committed(raw):
                # Reopen a DB session and restore actual committed bytes, not
                # just the checkpoint held by the old in-memory saver.
                with database.session() as session:
                    row = session.scalar(select(ResearchCheckpointRow).where(
                        ResearchCheckpointRow.owner_id == owner,
                        ResearchCheckpointRow.run_id == run.run_id,
                        ResearchCheckpointRow.content_hash == hashlib.sha256(raw).hexdigest()))
                    assert row is not None and row.payload == raw
                    return row.payload

            engine.checkpoint_read = read_committed
        result = engine.analyze(AnalysisRequest(instrument=instrument, analysis_date=NOW.date(),
            selected_analysts=analysts, snapshot_context=inputs, execution_observer=observer))
        assert (result.decision_payload is None) == invalid
        if invalid:
            assert "report_translation_unavailable" in result.validation_issues
        public_result = result.model_dump(mode="json")
        public_result["final_state"].pop("messages", None)
        results.append(public_result)
        traces.append(engine.model_trace)
        completions.append(observer.completed)
        if interruption:
            assert engine.resume_evidence[1] > 0
            if json_checkpoint:
                assert engine.encoded_checkpoints
                for raw in engine.encoded_checkpoints:
                    envelope = json.loads(raw)
                    assert codec_messages_empty(envelope["checkpoint"]["channel_values"])
                    for _, channel, value in envelope["pending_writes"]:
                        assert channel != "messages" or value == []
                        assert codec_messages_empty(value)
    assert results[0] == results[1]
    assert traces[0] == traces[1]  # No repeated model call; no changed prompt after restoration.
    if database is not None:
        with database.session() as session:
            assert store.load_latest(session=session, owner_id=owner, run_id=run.run_id) is not None
        database.dispose()
    assert completions[0] == completions[1]  # Includes repeated rounds, validation and presentation.


def codec_messages_empty(value):
    if isinstance(value, dict):
        return all((key != "messages" or item == []) and codec_messages_empty(item)
                   for key, item in value.items())
    if isinstance(value, list):
        return all(codec_messages_empty(item) for item in value)
    return True
