"""Default stopped graph to explicit consent; real DB, synthetic SDK and ACK loss."""
import json
import os
from uuid import uuid4

import pytest
from sqlalchemy import select

from tests.test_initialized_preflight import _assert_reaped, _NativeContext
from tests.test_native_recorder_spawn import callback_fixture_child, fixture_child
from tests.test_recovery_fingerprint import inputs
from tests.test_supervised_native_graph import NativeFixtureEngine
from tradingagents.contracts import ArtifactKind, JobStatus
from tradingagents.platform.analysis import initialized_preflight, supervision
from tradingagents.platform.analysis.accounting import load_accounting_evidence
from tradingagents.platform.analysis.checkpoint_store import (
    CheckpointDatabaseError,
    PrivateCheckpointStore,
)
from tradingagents.platform.analysis.continuation import ContinuationConsentError
from tradingagents.platform.analysis.engine import AnalysisEngine
from tradingagents.platform.analysis.linked_execution import LinkedExecutionStore
from tradingagents.platform.analysis.linked_factory import build_linked_recorded_engine
from tradingagents.platform.analysis.linked_publication import LinkedPublicationContext
from tradingagents.platform.analysis.linked_recording import LinkedOriginalResearch
from tradingagents.platform.analysis.linked_results import LinkedResultPublisher
from tradingagents.platform.analysis.observer import STAGES, ResearchObserver
from tradingagents.platform.analysis.recording import SnapshotRecorder
from tradingagents.platform.analysis.snapshots import AnalysisSnapshot
from tradingagents.platform.analysis.supervision import RESULT_FIELDS, SupervisedAnalysisEngine
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
    ResearchCheckpointRow,
    ResearchExecutionCompletionRow,
    ResearchExecutionDispatchRow,
    RunEventRow,
)


def restored_default_child(connection, base_config, request_data, engine_factory, checkpoint_options,
                           recording_data, restore_checkpoint):
    fixture_child(connection, base_config, request_data, engine_factory, checkpoint_options, recording_data,
                  callbacks=True, restore_checkpoint=restore_checkpoint)


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


@pytest.mark.parametrize("driver_mode", ["manual", "worker"])
@pytest.mark.parametrize("language", ["en", "vi", "en-vi"])
def test_default_stopped_job_to_authenticated_consent(tmp_path, monkeypatch, language, isolated_database_url, driver_mode):
    args = inputs()
    args["base_config"]["backend_url"] = "https://example.test/v1/" + uuid4().hex
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
    prepared = prepare_terminal_continuation(database=database, artifact_store=store, run_id=run.run_id,
        base_config={**args["base_config"], "data_cache_dir": str(store.root / "worker-runtime" / "cache"),
                     "results_dir": str(store.root / "worker-runtime" / "reports")},
        session_token=issued.token, csrf_token=issued.csrf_token)
    consents = prepared.consents
    assert consents.codec is not captured["codec"]
    assert consents.codec.fingerprint == captured["codec"].fingerprint
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
    executions = LinkedExecutionStore(consents)
    executions.allocate(execution_id=consent.execution_id, session_token=issued.token, csrf_token=issued.csrf_token)
    if driver_mode == "worker":
        from tradingagents.platform.analysis.terminal_preparation import load_terminal_inputs
        from tradingagents.platform.jobs.linked_worker import execute_reserved_continuation
        from tradingagents.platform.persistence.models import OwnerSessionRow

        with database.session() as session:
            _, request, _, _ = load_terminal_inputs(session=session, artifact_store=store,
                                                   run_id=run.run_id, owner_id=run.owner_id)
            # Durable consent does not require storing or keeping browser login alive.
            for login in session.scalars(select(OwnerSessionRow)):
                login.revoked_at = consents.clock()
        baseline_request = request.model_copy(update={"execution_observer": ResearchObserver(
            check_cancelled=lambda: None, emit=lambda *args: None)})
        baseline_config = {**args["base_config"],
            "data_cache_dir": str(store.root / "worker-runtime" / "cache"),
            "results_dir": str(store.root / "worker-runtime" / "reports")}
        baseline = NativeFixtureEngine(base_config={**baseline_config, "_fixture_callbacks": True})
        baseline.snapshot_recorder = SnapshotRecorder(owner_id=run.owner_id, run=run,
            expected_fingerprint=captured["codec"].fingerprint, commit=lambda raw: None)
        expected = baseline.analyze(baseline_request, fixture_execution=lambda options:
            AnalysisEngine(base_config=options).analyze(baseline_request))
        monkeypatch.setattr(supervision, "_child", restored_default_child)
        result = runtime.run_worker(runtime.WorkerSettings(url, store.root), once=True,
                                    continuations=True, worker_id="native-linked-worker")
        suffix = json.loads((store.root / "worker-runtime" / "reports.fixture-trace.json").read_text())
        assert trace["trace"] + suffix["trace"] == json.loads(json.dumps(baseline.model_trace))
        assert suffix["pid"] != trace["pid"] and suffix["closed_clients"] == 2
        with pytest.raises(ProcessLookupError):
            os.kill(suffix["pid"], 0)
        assert set(baseline_request.execution_observer.completed) == STAGES
        expected_data = expected.model_dump()
        expected_data["final_state"] = {key: value for key, value in expected_data["final_state"].items()
                                       if key in RESULT_FIELDS}
        for key in ("investment_debate_state", "risk_debate_state"):
            expected_data["final_state"][key] = {"history": expected_data["final_state"][key].get("history", "")}
        assert result.model_dump() == expected_data
        from fastapi.testclient import TestClient

        from tradingagents.platform.api import ApiSettings, create_app

        with database.session() as session:
            new_login = OwnerAuth(session).login("stopped-default@example.test", "synthetic fixture password")
        app = create_app(ApiSettings(database_url=url, artifact_root=store.root,
                                    allowed_origin="http://testserver", secure_cookies=False))
        with TestClient(app) as client:
            client.cookies.set("ta_session", new_login.token)
            client.cookies.set("ta_csrf", new_login.csrf_token)
            path = f"/api/v1/runs/{run.run_id}/continuations/{consent.execution_id}"
            state = client.get(path)
            assert state.status_code == 200, state.text
            assert state.json()["status"] == "completed"
            assert state.json()["preparation_requires_review"] is False
            headers = {"Origin": "http://testserver", "X-CSRF-Token": new_login.csrf_token}
            assert client.post(path + "/cancel", headers=headers).status_code == 409
        with database.session() as session:
            aggregate = load_accounting_evidence(session=session, owner_id=run.owner_id, run_id=run.run_id)
            assert aggregate.attempts == (1, 2)
            assert aggregate.started_calls == len(baseline.model_trace)
            assert aggregate.reported_total_tokens == len(baseline.model_trace) * 15
            assert aggregate.elapsed_upper_bound >= accounting.elapsed_upper_bound
            assert PlatformRepository(session).get_run(run.run_id, run.owner_id) == retained
            assert DurableJobQueue(session).get(completed.job_id, run.owner_id) == completed
            rows = session.scalars(select(ResearchCheckpointRow).where(
                ResearchCheckpointRow.run_id == run.run_id).order_by(ResearchCheckpointRow.sequence)).all()
            assert [(row.record_id, row.content_hash, row.payload) for row in rows[:len(old_rows)]] == old_rows
            completion = session.get(ResearchExecutionCompletionRow, consent.execution_id)
            assert completion is not None and completion.checkpoint_record_id == rows[-1].record_id
            repo = PlatformRepository(session, artifact_store=store)
            candidate = repo.get_decision(completion.decision_id, run.owner_id)
            assert candidate.requires_human_approval is True and candidate.status.value == "review"
            report = json.loads(ArtifactService(store, repo).read(completion.report_artifact_id, run.owner_id)[1])
            assert report["linked_execution"]["original_run_status"] == "failed"
            assert report["linked_execution"]["accounting"]["reported_total_tokens"] == aggregate.reported_total_tokens
        before = len(native.children)
        with pytest.raises(ValueError, match="linked worker execution requires review"):
            execute_reserved_continuation(database=database, artifact_store=store,
                execution_id=consent.execution_id, base_config=baseline_config, worker_id="second-worker")
        assert len(native.children) == before
        _assert_reaped(native)
        database.dispose()
        return
    lease = executions.claim(execution_id=consent.execution_id, worker_id="default-linked-factory")
    publisher = LinkedResultPublisher(store)
    linked = LinkedPublicationContext.prepare(executions, lease, save_stage=publisher.save_stage)
    original = LinkedOriginalResearch.load(context=linked, artifact_store=store)
    publisher.bind(linked, original)
    template = SupervisedAnalysisEngine(base_config={**args["base_config"],
        "data_cache_dir": str(store.root / "worker-runtime" / "cache"),
        "results_dir": str(store.root / "worker-runtime" / "reports")})
    engine = build_linked_recorded_engine(template=template, context=linked, original=original)
    assert engine.checkpoint_codec is prepared.consents.codec
    assert engine.restore_checkpoint == original.restore_checkpoint
    assert engine.recording_inputs is original.recording_inputs
    assert engine.linked_context is linked
    assert original.request.execution_observer is linked.observer
    assert linked.observer._retained_started_calls == 1
    assert linked.observer.started_calls == 0
    assert original.recording_inputs.read().run == retained
    with database.session() as session:
        assert session.get(ResearchExecutionDispatchRow, consent.execution_id) is None
        assert DurableJobQueue(session).get(completed.job_id, run.owner_id) == completed
        assert PlatformRepository(session).get_run(run.run_id, run.owner_id) == retained
    assert json.loads((store.root / "worker-runtime" / "reports.fixture-trace.json").read_text()) == trace
    with pytest.raises(ValueError, match="linked recording setup requires review"):
        build_linked_recorded_engine(template=template, context=object(), original=original)
    with monkeypatch.context() as changed:
        changed.setattr(linked, "_result_publisher", None)
        with pytest.raises(ValueError, match="linked recording publisher requires review"):
            build_linked_recorded_engine(template=template, context=linked, original=original)
    changed_config = {**template.base_config,
                      "max_debate_rounds": template.base_config["max_debate_rounds"] + 1}
    with pytest.raises(ValueError, match="linked recording identity requires review"):
        build_linked_recorded_engine(template=SupervisedAnalysisEngine(base_config=changed_config),
                                     context=linked, original=original)
    assert linked.observer.started_calls == 0 and linked.observer._retained_started_calls == 1
    with database.session() as session:
        assert session.get(ResearchExecutionDispatchRow, consent.execution_id) is None
    baseline_request = original.request.model_copy(update={"execution_observer": ResearchObserver(
        check_cancelled=lambda: None, emit=lambda *args: None)})
    baseline = NativeFixtureEngine(base_config={**template.base_config, "_fixture_callbacks": True})
    baseline.snapshot_recorder = SnapshotRecorder(owner_id=run.owner_id, run=run,
        expected_fingerprint=captured["codec"].fingerprint, commit=lambda raw: None)
    expected = baseline.analyze(baseline_request, fixture_execution=lambda options:
        AnalysisEngine(base_config=options).analyze(baseline_request))
    monkeypatch.setattr(supervision, "_child", restored_default_child)
    result = engine.analyze(original.request)
    suffix = json.loads((store.root / "worker-runtime" / "reports.fixture-trace.json").read_text())
    assert trace["trace"] + suffix["trace"] == json.loads(json.dumps(baseline.model_trace))
    assert suffix["pid"] != trace["pid"] and suffix["closed_clients"] == 2
    with pytest.raises(ProcessLookupError):
        os.kill(suffix["pid"], 0)
    assert set(baseline_request.execution_observer.completed) == STAGES
    expected_data = expected.model_dump()
    expected_data["final_state"] = {key: value for key, value in expected_data["final_state"].items()
                                   if key in RESULT_FIELDS}
    for key in ("investment_debate_state", "risk_debate_state"):
        expected_data["final_state"][key] = {"history": expected_data["final_state"][key].get("history", "")}
    assert result.model_dump() == expected_data
    with database.session() as session:
        aggregate = load_accounting_evidence(session=session, owner_id=run.owner_id, run_id=run.run_id)
        assert aggregate.attempts == (1, 2)
        assert aggregate.started_calls == len(baseline.model_trace)
        assert aggregate.reported_total_tokens == len(baseline.model_trace) * 15
        assert aggregate.elapsed_upper_bound >= accounting.elapsed_upper_bound
        assert PlatformRepository(session).get_run(run.run_id, run.owner_id) == retained
        assert DurableJobQueue(session).get(completed.job_id, run.owner_id) == completed
        rows = session.scalars(select(ResearchCheckpointRow).where(
            ResearchCheckpointRow.run_id == run.run_id).order_by(ResearchCheckpointRow.sequence)).all()
        assert [(row.record_id, row.content_hash, row.payload) for row in rows[:len(old_rows)]] == old_rows
        completion = session.get(ResearchExecutionCompletionRow, consent.execution_id)
        assert completion is not None and completion.checkpoint_record_id == rows[-1].record_id
        repo = PlatformRepository(session, artifact_store=store)
        candidate = repo.get_decision(completion.decision_id, run.owner_id)
        assert candidate.requires_human_approval is True and candidate.status.value == "review"
        report = json.loads(ArtifactService(store, repo).read(completion.report_artifact_id, run.owner_id)[1])
        assert report["linked_execution"]["original_run_status"] == "failed"
        assert report["linked_execution"]["accounting"]["reported_total_tokens"] == aggregate.reported_total_tokens
    _assert_reaped(native)
    database.dispose()
