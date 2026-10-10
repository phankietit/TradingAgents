"""Default stopped graph to explicit consent; real DB, synthetic SDK and ACK loss."""
import json
import os
from uuid import uuid4

import pytest
from sqlalchemy import select

from tests.test_initialized_preflight import _assert_reaped, _NativeContext
from tests.test_native_recorder_spawn import callback_fixture_child
from tests.test_recovery_fingerprint import inputs
from tradingagents.contracts import ArtifactKind, JobStatus
from tradingagents.platform.analysis import initialized_preflight, supervision
from tradingagents.platform.analysis.accounting import load_accounting_evidence
from tradingagents.platform.analysis.checkpoint_store import (
    CheckpointDatabaseError,
    PrivateCheckpointStore,
)
from tradingagents.platform.analysis.continuation import (
    ContinuationConsentError,
    ContinuationConsentStore,
)
from tradingagents.platform.analysis.snapshots import AnalysisSnapshot
from tradingagents.platform.artifacts import ArtifactService, LocalArtifactStore
from tradingagents.platform.auth import OwnerAuth
from tradingagents.platform.jobs import DurableJobQueue, runtime
from tradingagents.platform.persistence import (
    Database,
    PlatformRepository,
    downgrade_database,
    upgrade_database,
)
from tradingagents.platform.persistence.models import ResearchCheckpointRow, RunEventRow


@pytest.fixture(params=["sqlite", "postgresql"])
def isolated_database_url(tmp_path, request):
    if request.param == "postgresql":
        url = os.environ.get("TEST_POSTGRES_URL")
        if not url or os.environ.get("TA_ALLOW_TEST_DB_RESET") != "1":
            pytest.skip("isolated PostgreSQL helper prerequisite absent")
        # Explicit disposable helper DB only. Each case owns its owner bootstrap.
        downgrade_database(url)
    else:
        url = "sqlite:///" + str(tmp_path / "default.db")
    try:
        yield url
    finally:
        if request.param == "postgresql":
            downgrade_database(url)


@pytest.mark.parametrize("language", ["en", "vi", "en-vi"])
def test_default_stopped_job_to_authenticated_consent(tmp_path, monkeypatch, language, isolated_database_url):
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
    url = isolated_database_url
    symbol = "QA" + uuid4().hex[:8].upper()
    instrument = instrument.model_copy(update={"symbol": symbol, "canonical_symbol": symbol})
    upgrade_database(url)
    database = Database(url)
    store = LocalArtifactStore(tmp_path / "artifacts")
    with database.session() as session:
        repo = PlatformRepository(session, artifact_store=store)
        auth = OwnerAuth(session)
        auth.bootstrap_owner("stopped-default@example.test", "synthetic fixture password", owner_id=run.owner_id)
        issued = auth.login("stopped-default@example.test", "synthetic fixture password")
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
    monkeypatch.setattr(supervision, "_child", callback_fixture_child)

    original_commit = PrivateCheckpointStore.commit
    captured = {}
    def uncertain_ack(self, **kwargs):
        receipt = original_commit(self, **kwargs)
        value = self.codec.decode(kwargs["raw"])
        if not captured and any(channel == "market_report" and payload
                                for _, channel, payload in value.pending_writes):
            captured["codec"] = self.codec
            raise CheckpointDatabaseError("synthetic committed checkpoint ACK loss")
        return receipt
    monkeypatch.setattr(PrivateCheckpointStore, "commit", uncertain_ack)
    # No injected engine: the actual default runtime/handler/factory owns setup.
    completed = runtime.run_worker(runtime.WorkerSettings(url, store.root), once=True,
                                   worker_id="default-native-worker")
    assert completed.job_id == original_job.job_id

    assert completed.status is JobStatus.FAILED
    assert completed.error_code == "RESEARCH_EXECUTION_FAILED"
    assert captured and not completed.output_artifact_ids
    consents = ContinuationConsentStore(database, codec=captured["codec"])
    with database.session() as session:
        retained = PlatformRepository(session).get_run(run.run_id, run.owner_id)
        assert retained.decision_inputs == run.decision_inputs
        assert retained.execution_limits == run.execution_limits
        rows = session.scalars(select(ResearchCheckpointRow).where(
            ResearchCheckpointRow.run_id == run.run_id).order_by(ResearchCheckpointRow.sequence)).all()
        old_rows = [(row.record_id, row.content_hash, row.payload) for row in rows]
        saved = PrivateCheckpointStore(codec=captured["codec"]).load_latest(
            session=session, owner_id=run.owner_id, run_id=run.run_id)
        assert any(channel == "market_report" and payload
                   for _, channel, payload in saved.pending_writes)
        old_events = [(row.event_id, row.payload) for row in session.scalars(select(RunEventRow).where(
            RunEventRow.run_id == run.run_id).order_by(RunEventRow.sequence))]
        accounting = load_accounting_evidence(session=session, owner_id=run.owner_id, run_id=run.run_id)
        assert accounting.evidence_status == "PASS"
        assert accounting.started_calls == 1 and accounting.reported_total_tokens == 15
        assert accounting.elapsed_upper_bound is not None
        observation = consents.observe(session=session, owner_id=run.owner_id, run_id=run.run_id)
    values = {"session_token": issued.token, "csrf_token": issued.csrf_token,
              "expected_observation": observation, "idempotency_key": uuid4(), "confirm_continue": True}
    with pytest.raises(ContinuationConsentError):
        consents.record(**{**values, "confirm_continue": False})
    with pytest.raises(ContinuationConsentError):
        consents.record(**{**values, "csrf_token": "invalid"})
    consent = consents.record(**values)
    assert consents.record(**values) == consent
    with database.session() as session:
        assert PlatformRepository(session).get_run(run.run_id, run.owner_id) == retained
        assert DurableJobQueue(session).get(completed.job_id, run.owner_id) == completed
        assert load_accounting_evidence(session=session, owner_id=run.owner_id, run_id=run.run_id) == accounting
        rows = session.scalars(select(ResearchCheckpointRow).where(
            ResearchCheckpointRow.run_id == run.run_id).order_by(ResearchCheckpointRow.sequence)).all()
        assert [(row.record_id, row.content_hash, row.payload) for row in rows] == old_rows
        events = session.scalars(select(RunEventRow).where(
            RunEventRow.run_id == run.run_id).order_by(RunEventRow.sequence)).all()
        assert [(row.event_id, row.payload) for row in events] == old_events
    trace = json.loads((store.root / "worker-runtime" / "reports.fixture-trace.json").read_text())
    assert len(trace["trace"]) == 1 and trace["closed_clients"] is None
    with pytest.raises(ProcessLookupError):
        os.kill(trace["pid"], 0)
    _assert_reaped(native)
    database.dispose()
