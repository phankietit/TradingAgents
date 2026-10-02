"""Private checkpoint durability and current publication-lease fences."""

from contextlib import contextmanager
from datetime import timedelta
from uuid import uuid4

import pytest
from sqlalchemy import inspect, select

from tests.test_durable_jobs import NOW, _database, _enqueue
from tests.test_snapshot_checkpoint_codec import checkpoint
from tradingagents.platform.analysis.checkpoint_codec import (
    CheckpointCodecError,
    SnapshotCheckpointCodec,
)
from tradingagents.platform.analysis.checkpoint_store import (
    CheckpointStoreError,
    PrivateCheckpointStore,
)
from tradingagents.platform.jobs import DurableJobQueue, JobLeaseError
from tradingagents.platform.jobs.worker import JobCancellationRequested, JobExecutionContext
from tradingagents.platform.persistence import Database, downgrade_database, upgrade_database
from tradingagents.platform.persistence.models import ArtifactRow, ResearchCheckpointRow


@pytest.fixture
def setup(tmp_path):
    database, owner, run = _database(tmp_path)
    job = _enqueue(database, owner, run)
    with database.session() as session:
        job = DurableJobQueue(session).claim("fixture-worker", lease_for=timedelta(minutes=5), now=NOW)
    context = JobExecutionContext(database, job.job_id, "fixture-worker", timedelta(minutes=5), lambda: NOW)
    codec = SnapshotCheckpointCodec(fingerprint="a" * 64, nodes={"Market Analyst"})
    store = PrivateCheckpointStore(codec=codec)
    value = checkpoint()
    value.config["configurable"]["thread_id"] = str(run.run_id)
    value.metadata["thread_id"] = str(run.run_id)
    raw = codec.encode(value)
    yield database, owner, run, context, store, raw
    database.dispose()


def save(items, **changes):
    database, owner, run, context, store, raw = items
    return store.commit(context=context, owner_id=changes.get("owner_id", owner),
                        run_id=changes.get("run_id", run.run_id), raw=changes.get("raw", raw))


def test_commit_survives_database_reopen_and_never_is_artifact(setup):
    database, owner, run, context, store, raw = setup
    first = save(setup)
    assert save(setup) == first
    with database.session() as session:
        assert session.scalar(select(ArtifactRow)) is None
        row = session.scalar(select(ResearchCheckpointRow))
        assert row.sequence == 1 and row.attempt == 1 and row.job_id == context.job_id
        assert b"PRIVATE_RAW_MESSAGE" not in row.payload and b"PRIVATE_REASONING" not in row.payload
    reopened = Database(str(database.engine.url))
    try:
        with reopened.session() as session:
            value = store.load_latest(session=session, owner_id=owner, run_id=run.run_id)
            assert value == store.codec.decode(raw)
    finally:
        reopened.dispose()


def test_owner_and_thread_mismatch_cannot_write_or_read(setup):
    database, owner, run, context, store, raw = setup
    with pytest.raises(CheckpointStoreError):
        save(setup, owner_id=uuid4())
    with pytest.raises(CheckpointStoreError):
        save(setup, run_id=uuid4())
    save(setup)
    with database.session() as session, pytest.raises(CheckpointStoreError):
        store.load_latest(session=session, owner_id=uuid4(), run_id=run.run_id)


@pytest.mark.parametrize("fence", ["expired", "worker", "cancelled", "heartbeat_failure"])
def test_fenced_write_does_not_ack_or_persist(setup, fence):
    database, owner, run, context, store, raw = setup
    expected = JobLeaseError
    if fence == "expired":
        context.clock = lambda: NOW + timedelta(minutes=6)
    elif fence == "worker":
        context.worker_id = "not-owner"
    elif fence == "heartbeat_failure":
        context._lease_error = RuntimeError("fixture heartbeat stopped")
    else:
        with database.session() as session:
            DurableJobQueue(session).request_cancel(context.job_id, owner_id=owner, now=NOW)
        expected = JobCancellationRequested
    with pytest.raises(expected):
        save(setup)
    with database.session() as session:
        assert session.scalar(select(ResearchCheckpointRow)) is None


def test_transaction_failure_after_flush_has_no_ack_and_rolls_back(setup, monkeypatch):
    database, owner, run, context, store, raw = setup
    original = context.publication_session

    @contextmanager
    def failed_commit():
        with original() as session:
            yield session
            raise RuntimeError("simulated commit failure")

    monkeypatch.setattr(context, "publication_session", failed_commit)
    with pytest.raises(RuntimeError, match="simulated commit failure"):
        save(setup)
    with database.session() as session:
        assert session.scalar(select(ResearchCheckpointRow)) is None


def test_append_pending_revision_retains_old_bytes_and_rejects_corrupt_latest(setup):
    database, owner, run, context, store, raw = setup
    save(setup)
    value = store.codec.decode(raw)
    value.pending_writes.append((str(uuid4()), "market_report", "Completed pending output"))
    changed = store.codec.encode(value)
    assert save(setup, raw=changed).sequence == 2
    with database.session() as session:
        rows = session.scalars(select(ResearchCheckpointRow).order_by(ResearchCheckpointRow.sequence)).all()
        assert rows[0].payload == raw and rows[1].payload == changed
        rows[1].payload = b"corrupt fixture"
    with database.session() as session, pytest.raises(CheckpointStoreError):
        store.load_latest(session=session, owner_id=owner, run_id=run.run_id)


def test_incompatible_fingerprint_never_returns_old_checkpoint(setup):
    database, owner, run, context, store, raw = setup
    save(setup)
    changed = PrivateCheckpointStore(codec=SnapshotCheckpointCodec(
        fingerprint="b" * 64, nodes={"Market Analyst"}))
    with database.session() as session, pytest.raises(CheckpointStoreError):
        changed.load_latest(session=session, owner_id=owner, run_id=run.run_id)


def test_empty_checkpoint_not_backfilled(setup):
    database, owner, run, context, store, raw = setup
    with database.session() as session:
        assert store.load_latest(session=session, owner_id=owner, run_id=run.run_id) is None


def test_invalid_json_rejected_before_lease_or_storage(setup, monkeypatch):
    database, owner, run, context, store, raw = setup

    def forbidden():
        raise AssertionError("invalid checkpoint entered publication transaction")

    monkeypatch.setattr(context, "publication_session", forbidden)
    with pytest.raises(CheckpointCodecError):
        save(setup, raw=b'{"private_key":"NEVER_ECHO"}')
    with database.session() as session:
        assert session.scalar(select(ResearchCheckpointRow)) is None


def test_checkpoint_identity_column_corruption_is_not_accepted(setup):
    database, owner, run, context, store, raw = setup
    save(setup)
    with database.session() as session:
        session.scalar(select(ResearchCheckpointRow)).checkpoint_id = uuid4()
    with database.session() as session, pytest.raises(CheckpointStoreError):
        store.load_latest(session=session, owner_id=owner, run_id=run.run_id)


def test_new_table_migration_roundtrip_preserves_existing_run(setup):
    database, owner, run, context, store, raw = setup
    url = str(database.engine.url)
    # Fixture only, never an existing owner database or real checkpoint history.
    downgrade_database(url, "0010_owner_watchlist")
    assert "research_checkpoints" not in inspect(database.engine).get_table_names()
    upgrade_database(url)
    assert "research_checkpoints" in inspect(database.engine).get_table_names()
    save(setup)
