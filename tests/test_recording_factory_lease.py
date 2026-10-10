"""Factory with real DB/lease/ACK; fixture checkpoint, not graph replay."""

import os
from datetime import timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select

from tests.test_initialized_preflight import _assert_reaped, _NativeContext
from tests.test_recovery_fingerprint import inputs
from tests.test_snapshot_checkpoint_codec import checkpoint
from tradingagents.contracts import ArtifactKind
from tradingagents.platform.analysis import initialized_preflight, recording_factory as factory
from tradingagents.platform.analysis.checkpoint_store import PrivateCheckpointStore
from tradingagents.platform.analysis.observer import ResearchObserver
from tradingagents.platform.analysis.snapshots import load_snapshot_context
from tradingagents.platform.analysis.supervision import SupervisedAnalysisEngine
from tradingagents.platform.artifacts import ArtifactService, LocalArtifactStore
from tradingagents.platform.jobs import DurableJobQueue, JobLeaseError
from tradingagents.platform.jobs.worker import JobCancellationRequested, JobExecutionContext
from tradingagents.platform.persistence import Database, PlatformRepository, upgrade_database
from tradingagents.platform.persistence.models import ResearchCheckpointRow


@pytest.fixture(params=["sqlite", "postgresql"])
def setup(request, tmp_path, monkeypatch):
    if request.param == "postgresql":
        url = os.environ.get("TEST_POSTGRES_URL")
        if not url or os.environ.get("TA_ALLOW_TEST_DB_RESET") != "1":
            pytest.skip("isolated PostgreSQL helper prerequisite absent")
    else:
        url = "sqlite:///" + str(tmp_path / "recorded-lease.db")
    upgrade_database(url)
    database = Database(url)
    store = LocalArtifactStore(tmp_path / "artifacts")
    args = inputs()
    run = args["run"]
    now = run.analysis_as_of
    source = args["request"].snapshot_context.by_analyst["market"][0]
    symbol = "QA" + uuid4().hex[:8].upper()
    instrument = args["request"].instrument.model_copy(update={"symbol": symbol, "canonical_symbol": symbol})
    with database.session() as session:
        repo = PlatformRepository(session, artifact_store=store)
        repo.add_instrument(instrument)
        repo.add_snapshot(source.manifest)
        repo.save_run(run)
        ArtifactService(store, repo).create(owner_id=run.owner_id, kind=ArtifactKind.SNAPSHOT_PAYLOAD,
            media_type="application/json", content=source.payload.encode(),
            snapshot_id=source.manifest.snapshot_id, instrument_id=instrument.instrument_id)
        job = DurableJobQueue(session).enqueue(owner_id=run.owner_id, run_id=run.run_id,
            idempotency_key="original:" + str(run.run_id), payload={"fixture": True}, now=now)
        claimed = DurableJobQueue(session).claim("fixture-worker", lease_for=timedelta(minutes=5), now=now)
        assert claimed.job_id == job.job_id
    context = JobExecutionContext(database, job.job_id, "fixture-worker", timedelta(minutes=5), lambda: now)
    observer = ResearchObserver(check_cancelled=context.raise_if_cancelled, emit=lambda *args: None)
    with database.session() as session:
        repo = PlatformRepository(session, artifact_store=store)
        saved_run = repo.get_run(run.run_id, run.owner_id)
        loaded = load_snapshot_context(ArtifactService(store, repo), saved_run,
                                       saved_run.decision_inputs.snapshots_by_analyst)
    analysis_request = args["request"].model_copy(update={"instrument": instrument,
        "snapshot_context": loaded, "execution_observer": observer})
    config = args["base_config"]
    config.update(data_cache_dir=str(tmp_path / "cache"), results_dir=str(tmp_path / "results"))
    template = SupervisedAnalysisEngine(base_config=config)
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-only")
    native = _NativeContext("success")
    monkeypatch.setattr(initialized_preflight, "get_context", lambda mode: native)
    engine = factory.build_recorded_engine(template=template, context=context, run=saved_run,
        request=analysis_request, observer=observer)
    value = checkpoint()
    value.config["configurable"]["thread_id"] = str(run.run_id)
    value.metadata["thread_id"] = str(run.run_id)
    raw = engine.checkpoint_codec.encode(value)
    try:
        yield database, context, engine, saved_run, observer, raw
    finally:
        _assert_reaped(native)
        database.dispose()


def test_real_factory_ack_reopen_and_idempotency_preserve_original_run(setup):
    database, context, engine, run, observer, raw = setup
    first = engine.checkpoint_commit(raw)
    assert engine.checkpoint_commit(raw) == first
    with database.session() as session:
        rows = session.scalars(select(ResearchCheckpointRow).where(ResearchCheckpointRow.run_id == run.run_id)).all()
        assert len(rows) == 1 and rows[0].job_id == context.job_id and rows[0].attempt == 1
        assert rows[0].payload == raw and b"PRIVATE_RAW_MESSAGE" not in raw
        assert PlatformRepository(session).get_run(run.run_id, run.owner_id) == run
    # SQLAlchemy's str(URL) masks the disposable QA password. Reuse the same
    # configured URL in memory only; never print or persist credentials.
    reopened = Database(database.engine.url.render_as_string(hide_password=False))
    try:
        with reopened.session() as session:
            recovered = PrivateCheckpointStore(codec=engine.checkpoint_codec).load_latest(
                session=session, owner_id=run.owner_id, run_id=run.run_id)
            assert recovered == engine.checkpoint_codec.decode(raw)
    finally:
        reopened.dispose()
    assert observer.started_calls == 0 and not any(observer.usage.values())


@pytest.mark.parametrize("fence", ["expired", "worker", "cancelled", "heartbeat_failure"])
def test_real_factory_checkpoint_refuses_lost_fence_without_ack_or_row(setup, fence):
    database, context, engine, run, observer, raw = setup
    expected = JobLeaseError
    if fence == "expired":
        context.clock = lambda: run.analysis_as_of + timedelta(minutes=6)
    elif fence == "worker":
        context.worker_id = "other-worker"
    elif fence == "heartbeat_failure":
        context._lease_error = RuntimeError("synthetic lease failure")
    else:
        with database.session() as session:
            DurableJobQueue(session).request_cancel(context.job_id, owner_id=run.owner_id, now=run.analysis_as_of)
        expected = JobCancellationRequested
    with pytest.raises(expected):
        engine.checkpoint_commit(raw)
    with database.session() as session:
        assert session.scalar(select(ResearchCheckpointRow).where(ResearchCheckpointRow.run_id == run.run_id)) is None
        assert PlatformRepository(session).get_run(run.run_id, run.owner_id) == run
    assert observer.started_calls == 0
