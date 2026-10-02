"""Actual engine/recorder/native graph, synthetic responses and disposable DB."""

import asyncio
from datetime import timedelta
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import select

from tests.test_durable_jobs import _database, _enqueue
from tests.test_risk_engine import NOW
from tests.test_snapshot_analysis import context
from tests.test_supervised_native_graph import NativeFixtureEngine
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.platform.analysis import AnalysisRequest
from tradingagents.platform.analysis.checkpoint_codec import SnapshotCheckpointCodec
from tradingagents.platform.analysis.checkpoint_store import PrivateCheckpointStore
from tradingagents.platform.analysis.client_binding import build_initialized_graph_fingerprint
from tradingagents.platform.analysis.observer import STAGES, ResearchObserver
from tradingagents.platform.analysis.recording import SnapshotRecorder
from tradingagents.platform.analysis.snapshots import AnalysisSnapshot
from tradingagents.platform.jobs import DurableJobQueue
from tradingagents.platform.jobs.worker import JobExecutionContext
from tradingagents.platform.persistence import PlatformRepository
from tradingagents.platform.persistence.models import ResearchCheckpointRow


@pytest.mark.parametrize("language,invalid", [("English", False), ("Vietnamese", False),
    ("English and Vietnamese", False), ("English and Vietnamese", True)])
def test_actual_recorder_runs_all_native_stages_and_reopens_private_bytes(tmp_path, monkeypatch, language, invalid):
    def forbidden(*args, **kwargs):
        raise AssertionError("native recording fixture attempted provider/network request")

    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-NEVER_ECHO")
    monkeypatch.setattr(httpx.Client, "send", forbidden)
    monkeypatch.setattr(httpx.AsyncClient, "send", forbidden)
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
        # Revalidate copied nested input before writing only this fresh fixture.
        run = type(original).model_validate(run.model_dump())
        with database.session() as session:
            PlatformRepository(session).save_run(run)
        _enqueue(database, owner, run)
        with database.session() as session:
            job = DurableJobQueue(session).claim("fixture", lease_for=timedelta(minutes=5), now=NOW)
        job_context = JobExecutionContext(database, job.job_id, "fixture", timedelta(minutes=5), lambda: NOW)
        events = []
        observer = ResearchObserver(check_cancelled=job_context.raise_if_cancelled,
            emit=lambda *args: events.append(args))
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
        store = PrivateCheckpointStore(codec=SnapshotCheckpointCodec(fingerprint=fingerprint, nodes=graph.workflow.nodes))
        engine = NativeFixtureEngine(base_config={**config, "_fixture_invalid_translation": invalid})
        engine.snapshot_recorder = SnapshotRecorder(owner_id=owner, run=run, expected_fingerprint=fingerprint,
            commit=lambda raw: store.commit(context=job_context, owner_id=owner, run_id=run.run_id, raw=raw))
        result = engine.analyze(request)
        baseline_observer = ResearchObserver(check_cancelled=job_context.raise_if_cancelled,
            emit=lambda *args: None)
        baseline_engine = NativeFixtureEngine(base_config={**config, "_fixture_invalid_translation": invalid})
        baseline = baseline_engine.analyze(request.model_copy(update={"execution_observer": baseline_observer}))
        assert engine.model_trace == baseline_engine.model_trace
        assert observer.completed == baseline_observer.completed
        recorded_result = result.model_dump()
        baseline_result = baseline.model_dump()
        recorded_result["final_state"].pop("messages", None)
        baseline_result["final_state"].pop("messages", None)
        assert recorded_result == baseline_result
        assert set(observer.completed) == STAGES
        assert observer.completed.count("Bull Researcher") == 2
        assert observer.completed.count("Aggressive Analyst") == 2
        assert observer.started == started
        assert observer.receipt()["usage"]["status"] == "incomplete"  # Synthetic methods bypass SDK callback accounting.
        if invalid:
            assert result.decision_payload is None
            assert "report_translation_unavailable" in result.validation_issues
        else:
            assert result.decision_payload.thesis == "Snapshot thesis"
        with database.session() as session:
            rows = session.scalars(select(ResearchCheckpointRow).order_by(ResearchCheckpointRow.sequence)).all()
            assert len(rows) > 17
            assert all(row.owner_id == owner and row.run_id == run.run_id and row.fingerprint == fingerprint for row in rows)
            assert [row.sequence for row in rows] == list(range(1, len(rows) + 1))
            assert all(b"synthetic-NEVER_ECHO" not in row.payload and b"PRIVATE_NATIVE_REASONING" not in row.payload for row in rows)
            # Native channel-version metadata can name messages; only actual
            # message values must be empty/removed. Strict codec checks nested
            # start state and pending writes too, without weakening schema.
            for row in rows:
                value = store.codec.decode(row.payload)
                assert value.checkpoint["channel_values"].get("messages", []) == []
            assert store.load_latest(session=session, owner_id=owner, run_id=run.run_id) is not None
            assert PlatformRepository(session).get_run(original.run_id, owner).decision_inputs is None
        assert list((tmp_path / "results").iterdir()) == []
    finally:
        if graph is not None:
            for llm in (graph.quick_thinking_llm, graph.deep_thinking_llm):
                llm.root_client.close()
                asyncio.run(llm.root_async_client.close())
        database.dispose()
