"""Exact production child/engine/recorder/native graph with synthetic SDK responses."""

import asyncio
import json
import os
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import select

from tests.test_durable_jobs import _database, _enqueue
from tests.test_risk_engine import NOW
from tests.test_snapshot_analysis import context
from tests.test_supervised_native_graph import NativeFixtureEngine
from tradingagents.contracts import RunEventType
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.platform.analysis import AnalysisEngine, AnalysisRequest
from tradingagents.platform.analysis.checkpoint_codec import SnapshotCheckpointCodec
from tradingagents.platform.analysis.checkpoint_store import PrivateCheckpointStore
from tradingagents.platform.analysis.client_binding import build_initialized_graph_fingerprint
from tradingagents.platform.analysis.observer import (
    STAGES,
    ResearchBudgetExceeded,
    ResearchObserver,
)
from tradingagents.platform.analysis.recording import SnapshotRecorder
from tradingagents.platform.analysis.recording_context import SnapshotRecordingInputs
from tradingagents.platform.analysis.snapshots import AnalysisSnapshot
from tradingagents.platform.analysis.supervision import (
    RESULT_FIELDS,
    SupervisedAnalysisEngine,
    _child as original_child,
)
from tradingagents.platform.events import RunEventStore
from tradingagents.platform.jobs import DurableJobQueue
from tradingagents.platform.jobs.worker import JobExecutionContext
from tradingagents.platform.persistence import PlatformRepository
from tradingagents.platform.persistence.models import ResearchCheckpointRow


def fixture_child(connection, base_config, request_data, engine_factory, checkpoint_options, recording_data,
                  *, invalid=False, callbacks=False):
    """Only install synthetic SDK responses; do not replace engine or graph hooks."""
    assert engine_factory is AnalysisEngine
    os.environ["OPENAI_API_KEY"] = "synthetic-NEVER_ECHO"
    inputs = SnapshotRecordingInputs(recording_data).read()
    request = AnalysisRequest.model_validate(request_data)
    fixture = NativeFixtureEngine(base_config={**base_config, "_fixture_invalid_translation": invalid,
                                              "_fixture_callbacks": callbacks})
    # Enable reviewed actual SDK construction in the reusable fixture. This
    # sentinel is never used by production child, which builds its own recorder.
    fixture.snapshot_recorder = SnapshotRecorder(owner_id=inputs.owner_id, run=inputs.run,
        expected_fingerprint=inputs.expected_fingerprint, commit=lambda raw: None)

    def forbidden(*args, **kwargs):
        raise AssertionError("native-spawn fixture attempted network/provider invocation")

    with patch.object(httpx.Client, "send", forbidden), patch.object(httpx.AsyncClient, "send", forbidden):
        fixture.analyze(request, fixture_execution=lambda config: original_child(
            connection, config, request_data, engine_factory, checkpoint_options, recording_data))
    assert len(fixture.initialized_clients) == 2
    assert all(llm.root_client.is_closed() and llm.root_async_client.is_closed()
               for llm in fixture.initialized_clients)
    Path(base_config["results_dir"] + ".fixture-trace.json").write_text(json.dumps({
        "pid": os.getpid(), "trace": fixture.model_trace, "closed_clients": 2}), encoding="utf-8")


def invalid_fixture_child(connection, base_config, request_data, engine_factory, checkpoint_options, recording_data):
    fixture_child(connection, base_config, request_data, engine_factory, checkpoint_options, recording_data,
                  invalid=True)


def callback_fixture_child(connection, base_config, request_data, engine_factory, checkpoint_options, recording_data):
    fixture_child(connection, base_config, request_data, engine_factory, checkpoint_options, recording_data,
                  callbacks=True)


def invalid_callback_fixture_child(connection, base_config, request_data, engine_factory, checkpoint_options, recording_data):
    fixture_child(connection, base_config, request_data, engine_factory, checkpoint_options, recording_data,
                  callbacks=True, invalid=True)


@pytest.mark.parametrize("language,invalid", [("English", False), ("Vietnamese", False),
    ("English and Vietnamese", False), ("English and Vietnamese", True)])
@pytest.mark.parametrize("callbacks", [False, True, "exhausted"])
def test_exact_engine_native_spawn_recorder_with_parent_persistence(tmp_path, monkeypatch, language, invalid, callbacks):
    def forbidden(*args, **kwargs):
        raise AssertionError("parent fixture attempted provider/network invocation")

    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-NEVER_ECHO")
    monkeypatch.setattr(httpx.Client, "send", forbidden)
    monkeypatch.setattr(httpx.AsyncClient, "send", forbidden)
    exhausted = callbacks == "exhausted"
    child = ({False: fixture_child, True: invalid_fixture_child} if not callbacks else
             {False: callback_fixture_child, True: invalid_callback_fixture_child})[invalid and not exhausted]
    monkeypatch.setattr("tradingagents.platform.analysis.supervision._child", child)
    database, owner, original = _database(tmp_path / "db")
    graph = None
    try:
        with database.session() as session:
            instrument = PlatformRepository(session).get_instrument(original.instrument_id)
        analysts = ("market", "social", "news", "fundamentals")
        sources = context(instrument)
        first = sources.by_analyst["market"][0]
        extras = {role: (AnalysisSnapshot(manifest=first.manifest.model_copy(update={
            "snapshot_id": uuid4(), "dataset": role}), payload=first.payload),)
            for role in analysts if role != "market"}
        sources = sources.model_copy(update={"by_analyst": {**sources.by_analyst, **extras},
            "source_max_age_seconds": dict.fromkeys(analysts, 0)})
        run = original.model_copy(update={"run_id": uuid4(), "analysis_as_of": NOW, "selected_analysts": analysts,
            "report_language": {"English": "en", "Vietnamese": "vi", "English and Vietnamese": "en-vi"}[language],
            "snapshot_ids": tuple(source.manifest.snapshot_id for group in sources.by_analyst.values() for source in group),
            "decision_inputs": {"snapshots_by_analyst": {role: tuple(source.manifest.snapshot_id for source in group)
                for role, group in sources.by_analyst.items()}, "source_max_age_seconds": dict.fromkeys(analysts, 0)}})
        run = type(original).model_validate(run.model_dump())
        if exhausted:
            run = type(original).model_validate(run.model_copy(update={
                "execution_limits": {"wall_seconds": 1800, "model_calls": 1}}).model_dump())
        with database.session() as session:
            PlatformRepository(session).save_run(run)
        _enqueue(database, owner, run)
        with database.session() as session:
            job = DurableJobQueue(session).claim("fixture", lease_for=timedelta(minutes=5), now=NOW)
        job_context = JobExecutionContext(database, job.job_id, "fixture", timedelta(minutes=5), lambda: NOW)
        events = []
        def emit(kind, payload):
            with job_context.publication_session() as session:
                RunEventStore(session).append(owner_id=owner, run_id=run.run_id,
                    event_type=RunEventType(kind), occurred_at=NOW, payload={**payload, "attempt": job.attempt})
            events.append((kind, payload))

        observer = ResearchObserver(check_cancelled=job_context.raise_if_cancelled,
            emit=emit, max_calls=1 if exhausted else 128)
        started = observer.started
        request = AnalysisRequest(instrument=instrument, analysis_date=NOW.date(), selected_analysts=analysts,
            snapshot_context=sources, execution_observer=observer)
        config = {**DEFAULT_CONFIG, "llm_provider": "openai", "quick_think_llm": "quick", "deep_think_llm": "deep",
            "backend_url": "https://example.test/v1", "data_cache_dir": str(tmp_path / "cache"),
            "results_dir": str(tmp_path / "results"), "output_language": language,
            "max_debate_rounds": 2, "max_risk_discuss_rounds": 2}
        graph = TradingAgentsGraph(config=config, selected_analysts=analysts,
            snapshot_reports=sources.reports(instrument.instrument_id, analysts))
        fingerprint = build_initialized_graph_fingerprint(graph=graph, owner_id=owner, run=run,
            request=request, base_config=config)
        codec = SnapshotCheckpointCodec(fingerprint=fingerprint, nodes=graph.workflow.nodes)
        store = PrivateCheckpointStore(codec=codec)
        commit_pids = []

        def commit(raw):
            commit_pids.append(os.getpid())
            return store.commit(context=job_context, owner_id=owner, run_id=run.run_id, raw=raw)

        recording = SnapshotRecordingInputs.create(owner_id=owner, run=run, expected_fingerprint=fingerprint)
        supervised = SupervisedAnalysisEngine(base_config=config, recording_inputs=recording,
            checkpoint_codec=codec, checkpoint_thread_id=str(run.run_id),
            checkpoint_commit=commit)
        if exhausted:
            with pytest.raises(ResearchBudgetExceeded, match="research model-call budget exhausted"):
                supervised.analyze(request)
            usage = observer.receipt()["usage"]
            assert observer.started == started and observer.max_calls == 1
            assert observer.started_calls == usage["model_calls"] == usage["calls_with_usage"] == 1
            assert usage["input_tokens"] == 10 and usage["output_tokens"] == 5 and usage["total_tokens"] == 15
            assert usage["failed_calls"] == 0 and usage["cost"] is None
            assert [data["usage"]["total_tokens"] for kind, data in events if kind == "model.usage"] == [0, 15]
            assert observer.completed == ["Market Analyst"]
            assert commit_pids and set(commit_pids) == {os.getpid()}
            with database.session() as session:
                rows = session.scalars(select(ResearchCheckpointRow)).all()
                assert rows and all(row.owner_id == owner and row.run_id == run.run_id for row in rows)
                for row in rows:
                    codec.decode(row.payload)
                usage_events = [event for event in RunEventStore(session).list_after(owner, run.run_id, limit=500)
                                if event.event_type is RunEventType.MODEL_USAGE]
                assert len(usage_events) == 2
                assert usage_events[0].payload["usage"]["started_model_calls"] == 1
                assert usage_events[0].payload["usage"]["model_calls"] == 0
                assert usage_events[0].payload["usage"]["status"] == "incomplete"
                assert usage_events[1].payload["usage"] == usage
                assert all(event.payload["attempt"] == job.attempt for event in usage_events)
                assert PlatformRepository(session).get_run(original.run_id, owner).decision_inputs is None
            return
        result = supervised.analyze(request)
        trace = json.loads(Path(config["results_dir"] + ".fixture-trace.json").read_text())
        assert trace["pid"] != os.getpid() and trace["closed_clients"] == 2
        with pytest.raises(ProcessLookupError):
            os.kill(trace["pid"], 0)  # Parent supervision reaped the completed child.
        assert commit_pids and set(commit_pids) == {os.getpid()}
        baseline = NativeFixtureEngine(base_config={**config, "_fixture_invalid_translation": invalid,
                                                   "_fixture_callbacks": callbacks})
        baseline_observer = ResearchObserver(check_cancelled=lambda: None, emit=lambda *args: None)
        baseline_request = request.model_copy(update={"execution_observer": baseline_observer})
        if callbacks:
            # Construct actual SDKs but run baseline without a saver/recorder.
            baseline.snapshot_recorder = SnapshotRecorder(owner_id=owner, run=run,
                expected_fingerprint=fingerprint, commit=lambda raw: None)
            expected = baseline.analyze(baseline_request, fixture_execution=lambda options:
                AnalysisEngine(base_config=options).analyze(baseline_request))
        else:
            expected = baseline.analyze(baseline_request)
        assert trace["trace"] == json.loads(json.dumps(baseline.model_trace))
        actual_data, expected_data = result.model_dump(), expected.model_dump()
        expected_data["final_state"] = {key: value for key, value in expected_data["final_state"].items()
                                        if key in RESULT_FIELDS}
        # Supervisor intentionally publishes only debate history, not internal counters.
        for key in ("investment_debate_state", "risk_debate_state"):
            expected_data["final_state"][key] = {"history": expected_data["final_state"][key].get("history", "")}
        assert actual_data == expected_data
        assert observer.completed == baseline_observer.completed
        assert set(observer.completed) == STAGES
        assert observer.completed.count("Bull Researcher") == 2
        assert observer.completed.count("Aggressive Analyst") == 2
        assert observer.started == started
        assert observer.max_seconds == 1800 and observer.max_calls == 128
        assert observer.receipt()["supervision_mode"] == "spawned_process"
        usage = observer.receipt()["usage"]
        if callbacks:
            calls = len(trace["trace"])
            assert calls > 14
            assert observer.started_calls == calls == baseline_observer.started_calls
            assert usage == baseline_observer.receipt()["usage"]
            assert usage["model_calls"] == usage["calls_with_usage"] == calls
            assert usage["input_tokens"] == 10 * calls and usage["output_tokens"] == 5 * calls
            assert usage["total_tokens"] == 15 * calls and usage["status"] == "reported"
            assert usage["cost"] is None and usage["provider_request_attempts"] is None
        else:
            assert usage["status"] == "incomplete"  # Synthetic invoke bypasses callbacks.
        if invalid:
            assert result.decision_payload is None
            assert "report_translation_unavailable" in result.validation_issues
        else:
            assert result.decision_payload.thesis == "Snapshot thesis"
        with database.session() as session:
            rows = session.scalars(select(ResearchCheckpointRow).order_by(ResearchCheckpointRow.sequence)).all()
            assert len(rows) > 17
            assert [row.sequence for row in rows] == list(range(1, len(rows) + 1))
            assert all(row.owner_id == owner and row.run_id == run.run_id and row.fingerprint == fingerprint for row in rows)
            assert all(b"synthetic-NEVER_ECHO" not in row.payload and b"PRIVATE_NATIVE_REASONING" not in row.payload for row in rows)
            for row in rows:
                assert codec.decode(row.payload).checkpoint["channel_values"].get("messages", []) == []
            assert store.load_latest(session=session, owner_id=owner, run_id=run.run_id) is not None
            if callbacks:
                usage_events = [event for event in RunEventStore(session).list_after(owner, run.run_id, limit=500)
                                if event.event_type is RunEventType.MODEL_USAGE]
                assert len(usage_events) == 2 * calls
                assert usage_events[-1].payload["usage"] == usage
                assert all(event.payload["execution_limits"] == {"wall_seconds": 1800, "model_calls": 128}
                           and event.payload["elapsed_seconds"] >= 0
                           and event.payload["attempt"] == job.attempt for event in usage_events)
            assert PlatformRepository(session).get_run(original.run_id, owner).decision_inputs is None
        assert list((tmp_path / "results").iterdir()) == []
    finally:
        if graph is not None:
            for llm in (graph.quick_thinking_llm, graph.deep_thinking_llm):
                llm.root_client.close()
                asyncio.run(llm.root_async_client.close())
        database.dispose()
