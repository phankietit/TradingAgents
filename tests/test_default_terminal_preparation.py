"""Default stopped graph to explicit consent; real DB, synthetic SDK and ACK loss."""
import json
import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
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
from tradingagents.platform.analysis.terminal_preparation import prepare_terminal_continuation
from tradingagents.platform.artifacts import ArtifactService, LocalArtifactStore
from tradingagents.platform.auth import OwnerAuth
from tradingagents.platform.jobs import DurableJobQueue, runtime
from tradingagents.platform.persistence import (
    Database,
    PlatformRepository,
    downgrade_database,
    upgrade_database,
)
from tradingagents.platform.persistence.models import (
    OwnerSessionRow,
    ResearchCheckpointRow,
    ResearchContinuationRow,
    ResearchExecutionRow,
    RunEventRow,
)


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
    # Existing codec is observed for comparison only, never passed to preparation.
    fixture_consents = ContinuationConsentStore(database, codec=captured["codec"])
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
        observation = fixture_consents.observe(session=session, owner_id=run.owner_id, run_id=run.run_id)
    settings = {**args["base_config"],
        "data_cache_dir": str(store.root / "worker-runtime" / "cache"),
        "results_dir": str(store.root / "worker-runtime" / "reports")}
    prepare_values = {"database": database, "artifact_store": store, "run_id": run.run_id,
                      "base_config": settings, "session_token": issued.token, "csrf_token": issued.csrf_token}
    with database.session() as session:
        original_seen = session.scalar(select(OwnerSessionRow.last_seen_at))
    count = len(native.children)
    for changed in ({"session_token": "invalid"}, {"csrf_token": "invalid"}, {"run_id": uuid4()}):
        with pytest.raises(ValueError, match="terminal continuation preparation requires review"):
            prepare_terminal_continuation(**{**prepare_values, **changed})
        assert len(native.children) == count
    prepared = prepare_terminal_continuation(**prepare_values)
    with database.session() as session:
        assert session.scalar(select(OwnerSessionRow.last_seen_at)) == original_seen
        assert not session.scalars(select(ResearchContinuationRow)).all()
        assert not session.scalars(select(ResearchExecutionRow)).all()
    changed_config = {**settings, "max_debate_rounds": settings["max_debate_rounds"] + 1}
    with pytest.raises(ValueError, match="terminal continuation preparation requires review"):
        prepare_terminal_continuation(**{**prepare_values, "base_config": changed_config})
    assert prepared.observation == observation
    assert prepared.consents.codec is not captured["codec"]
    assert prepared.consents.codec.fingerprint == captured["codec"].fingerprint
    assert prepared.consents.codec.nodes == captured["codec"].nodes
    consents = prepared.consents
    values = {"session_token": issued.token, "csrf_token": issued.csrf_token,
              "expected_observation": observation, "idempotency_key": uuid4(), "confirm_continue": True}
    with pytest.raises(ContinuationConsentError):
        consents.record(**{**values, "confirm_continue": False})
    with pytest.raises(ContinuationConsentError):
        consents.record(**{**values, "csrf_token": "invalid"})
    # Actual browser routes derive their own codec; no supplied preparation seam.
    from tradingagents.platform.api import ApiSettings, continuation_routes, create_app

    monkeypatch.setattr(continuation_routes, "DEFAULT_CONFIG", args["base_config"])
    app = create_app(ApiSettings(database_url=url, artifact_root=store.root,
                                allowed_origin="http://testserver", secure_cookies=False))
    with TestClient(app) as client:
        path = f"/api/v1/runs/{run.run_id}/continuation/prepare"
        headers = {"Origin": "http://testserver", "X-CSRF-Token": issued.csrf_token}
        before = len(native.children)
        assert client.post(path, headers=headers).status_code == 401
        client.cookies.set("ta_session", issued.token)
        client.cookies.set("ta_csrf", issued.csrf_token)
        assert client.post(path, headers={**headers, "Origin": "http://evil.test"}).status_code == 403
        assert client.post(path, headers={**headers, "X-CSRF-Token": "invalid"}).status_code == 403
        assert client.post(f"/api/v1/runs/{uuid4()}/continuation/prepare", headers=headers).status_code == 404
        assert len(native.children) == before
        response = client.post(path, headers=headers)
        assert response.status_code == 200, response.text
        ready = response.json()
        assert ready["dispatch_enabled"] is False
        assert ready["remaining_model_calls"] == accounting.original_model_calls - 1
        assert ready["remaining_wall_seconds"] == accounting.original_wall_seconds - accounting.elapsed_upper_bound
        body = {"observation_hash": ready["observation_hash"],
                "idempotency_key": str(values["idempotency_key"]), "confirm_continue": True,
                "acknowledge_original_allowance": True, "acknowledge_unknown_provider_cost": True,
                "acknowledge_unvalidated_prior_research": True}
        reserve_path = f"/api/v1/runs/{run.run_id}/continuations"
        before = len(native.children)
        for changed in ({"confirm_continue": False}, {"confirm_continue": 1},
                        {"acknowledge_unknown_provider_cost": False}, {"codec": "forbidden"}):
            assert client.post(reserve_path, headers=headers, json={**body, **changed}).status_code == 422
        assert len(native.children) == before
        response = client.post(reserve_path, headers=headers, json={**body, "observation_hash": "0" * 64})
        assert response.status_code == 409
        with database.session() as session:
            assert not session.scalars(select(ResearchContinuationRow)).all()
            assert not session.scalars(select(ResearchExecutionRow)).all()
        response = client.post(reserve_path, headers=headers, json=body)
        assert response.status_code == 200, response.text
        reserved = response.json()
        assert reserved["dispatch_enabled"] is False and reserved["status"] == "reserved"
        assert client.post(reserve_path, headers=headers, json=body).json() == reserved
    consent = consents.record(**values)
    assert str(consent.execution_id) == reserved["execution_id"]
    assert consents.record(**values) == consent
    with database.session() as session:
        assert session.scalar(select(OwnerSessionRow.last_seen_at)) == original_seen
        assert len(session.scalars(select(ResearchContinuationRow)).all()) == 1
        execution = session.scalars(select(ResearchExecutionRow)).one()
        assert execution.status == "reserved"
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
