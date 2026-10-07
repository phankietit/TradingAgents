"""Staged default runtime proof: canonical payload, real graph/DB, synthetic SDK."""
import json
import os
from uuid import uuid4

import pytest
from sqlalchemy import select

from tests.test_initialized_preflight import _assert_reaped, _NativeContext
from tests.test_native_recorder_spawn import fixture_child
from tests.test_recovery_fingerprint import inputs
from tradingagents.contracts import ArtifactKind, JobStatus
from tradingagents.platform.analysis import initialized_preflight, supervision
from tradingagents.platform.analysis.observer import STAGES
from tradingagents.platform.analysis.snapshots import AnalysisSnapshot
from tradingagents.platform.artifacts import ArtifactService, LocalArtifactStore
from tradingagents.platform.jobs import DurableJobQueue, runtime
from tradingagents.platform.persistence import Database, PlatformRepository, upgrade_database
from tradingagents.platform.persistence.models import ResearchCheckpointRow, RunEventRow


@pytest.mark.parametrize("dialect", ["sqlite", "postgresql"])
@pytest.mark.parametrize("language", ["en", "vi", "en-vi"])
def test_default_runtime_records_original_full_graph_without_engine_injection(tmp_path, monkeypatch, language, dialect):
    args = inputs()
    instrument = args["request"].instrument
    run = args["run"]
    source = args["request"].snapshot_context.by_analyst["market"][0]
    roles = ("market", "social", "news", "fundamentals")
    sources = {"market": (source,)}
    for role in roles[1:]:
        sources[role] = (AnalysisSnapshot(manifest=source.manifest.model_copy(update={
            "snapshot_id": uuid4(), "dataset": role}), payload=source.payload),)
    declared = run.decision_inputs.model_copy(update={
        "snapshots_by_analyst": {role: tuple(item.manifest.snapshot_id for item in group)
                                for role, group in sources.items()},
        "source_max_age_seconds": dict.fromkeys(roles, 0)})
    run = type(run).model_validate(run.model_copy(update={"selected_analysts": roles,
        "decision_inputs": declared, "snapshot_ids": declared.snapshot_ids(),
        "report_language": language}).model_dump())
    if dialect == "postgresql":
        url = os.environ.get("TEST_POSTGRES_URL")
        if not url or os.environ.get("TA_ALLOW_TEST_DB_RESET") != "1":
            pytest.skip("isolated PostgreSQL helper prerequisite absent")
    else:
        url = "sqlite:///" + str(tmp_path / "default.db")
    symbol = "QA" + uuid4().hex[:8].upper()
    instrument = instrument.model_copy(update={"symbol": symbol, "canonical_symbol": symbol})
    upgrade_database(url)
    database = Database(url)
    store = LocalArtifactStore(tmp_path / "artifacts")
    with database.session() as session:
        repo = PlatformRepository(session, artifact_store=store)
        repo.add_instrument(instrument)
        repo.save_run(run)
        artifacts = ArtifactService(store, repo)
        for group in sources.values():
            for item in group:
                repo.add_snapshot(item.manifest)
                artifacts.create(owner_id=run.owner_id, kind=ArtifactKind.SNAPSHOT_PAYLOAD,
                    media_type="application/json", content=item.payload.encode(),
                    instrument_id=instrument.instrument_id, snapshot_id=item.manifest.snapshot_id,
                    created_at=run.created_at, expected_hash=item.manifest.content_hash)
        payload = {"instrument_id": str(run.instrument_id),
            "analysis_as_of": run.analysis_as_of.isoformat(), "selected_analysts": list(roles),
            "config_hash": run.config_hash, "decision_inputs": declared.model_dump(mode="json"),
            "report_language": language, "execution_limits": run.execution_limits.model_dump(mode="json")}
        original_job = DurableJobQueue(session).enqueue(owner_id=run.owner_id, run_id=run.run_id,
            idempotency_key="default-native:" + str(run.run_id), payload=payload, now=run.created_at)
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-only")
    monkeypatch.setattr(runtime, "DEFAULT_CONFIG", args["base_config"])
    native = _NativeContext("success")
    monkeypatch.setattr(initialized_preflight, "get_context", lambda mode: native)
    monkeypatch.setattr(supervision, "_child", fixture_child)
    # No injected engine: the actual default runtime/handler/factory owns setup.
    completed = runtime.run_worker(runtime.WorkerSettings(url, store.root), once=True,
                                   worker_id="default-native-worker")
    assert completed.job_id == original_job.job_id
    assert completed.status is JobStatus.SUCCEEDED
    with database.session() as session:
        repo = PlatformRepository(session, artifact_store=store)
        retained = repo.get_run(run.run_id, run.owner_id)
        assert retained.decision_inputs == run.decision_inputs
        assert retained.selected_analysts == roles
        assert retained.execution_limits == run.execution_limits
        rows = session.scalars(select(ResearchCheckpointRow).where(
            ResearchCheckpointRow.run_id == run.run_id)).all()
        stages = session.scalars(select(RunEventRow).where(
            RunEventRow.run_id == run.run_id, RunEventRow.event_type == "stage.completed")).all()
        assert {event.payload["stage"] for event in stages} == STAGES
        assert len(rows) > 10
        assert all(row.job_id == original_job.job_id and row.attempt == 1 for row in rows)
        reports = [ArtifactService(store, repo).read(identity, run.owner_id)
                   for identity in completed.output_artifact_ids]
        assert any(manifest.kind is ArtifactKind.ANALYSIS_REPORT for manifest, raw in reports)
    trace_path = store.root / "worker-runtime" / "reports.fixture-trace.json"
    trace = json.loads(trace_path.read_text())
    assert trace["closed_clients"] == 2
    with pytest.raises(ProcessLookupError):
        os.kill(trace["pid"], 0)
    assert len(trace["trace"]) > 10
    _assert_reaped(native)
    database.dispose()
