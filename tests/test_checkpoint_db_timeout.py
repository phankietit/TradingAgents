"""Real local lock contention; no existing owner DB, network or model calls."""

import sqlite3
from datetime import timedelta
from time import monotonic

import pytest
from sqlalchemy import select, text

from tests.test_durable_jobs import NOW, _database, _enqueue
from tests.test_snapshot_checkpoint_codec import checkpoint
from tradingagents.platform.analysis.checkpoint_codec import SnapshotCheckpointCodec
from tradingagents.platform.analysis.checkpoint_store import (
    CheckpointDatabaseError,
    PrivateCheckpointStore,
    _checkpoint_session,
)
from tradingagents.platform.jobs import DurableJobQueue
from tradingagents.platform.jobs.worker import JobExecutionContext
from tradingagents.platform.persistence.models import ResearchCheckpointRow


@pytest.mark.parametrize("lock_phase", ["writer", "commit"])
def test_sqlite_checkpoint_writer_lock_is_bounded_rollback_and_pool_setting_restored(tmp_path, lock_phase):
    database, owner, run = _database(tmp_path)
    _enqueue(database, owner, run)
    with database.session() as session:
        job = DurableJobQueue(session).claim("fixture", lease_for=timedelta(minutes=5), now=NOW)
    context = JobExecutionContext(database, job.job_id, "fixture", timedelta(minutes=5), lambda: NOW)
    codec = SnapshotCheckpointCodec(fingerprint="a" * 64, nodes={"Market Analyst"})
    value = checkpoint()
    value.config["configurable"]["thread_id"] = str(run.run_id)
    value.metadata["thread_id"] = str(run.run_id)
    raw = codec.encode(value)
    store = PrivateCheckpointStore(codec=codec)
    with database.session() as session:
        old = session.execute(text("PRAGMA busy_timeout")).scalar_one()
    locker = sqlite3.connect(tmp_path / "jobs.db")
    try:
        if lock_phase == "writer":
            locker.execute("BEGIN IMMEDIATE")
        else:
            locker.execute("BEGIN")
            locker.execute("SELECT * FROM analysis_jobs").fetchall()
        start = monotonic()
        with pytest.raises(CheckpointDatabaseError) as raised:
            store.commit(context=context, owner_id=owner, run_id=run.run_id,
                         raw=raw, lock_timeout_seconds=.05)
        assert monotonic() - start < 1.5
        assert str(raised.value) == "checkpoint database commit requires review"
        assert raised.value.__cause__ is None
        locker.rollback()
        with database.session() as session:
            assert session.scalar(select(ResearchCheckpointRow)) is None
            assert session.execute(text("PRAGMA busy_timeout")).scalar_one() == old
        receipt = store.commit(context=context, owner_id=owner, run_id=run.run_id, raw=raw)
        assert receipt.sequence == 1
        with database.session() as session:
            assert session.execute(text("PRAGMA busy_timeout")).scalar_one() == old
    finally:
        locker.close()
        database.dispose()


def test_bounded_setting_restored_after_body_exception_and_default_session_unchanged(tmp_path):
    database, owner, run = _database(tmp_path)
    try:
        with database.session() as session:
            old = session.execute(text("PRAGMA busy_timeout")).scalar_one()
        with pytest.raises(RuntimeError), database.session(lock_timeout_seconds=.012) as session:
            assert session.execute(text("PRAGMA busy_timeout")).scalar_one() == 12
            raise RuntimeError("fixture rollback")
        with database.session() as session:
            assert session.execute(text("PRAGMA busy_timeout")).scalar_one() == old
    finally:
        database.dispose()


@pytest.mark.parametrize("timeout", [True, False, 0, -1, float("nan"), float("inf"), 61, "NEVER_ECHO"])
def test_invalid_lock_budget_rejected_before_transaction(tmp_path, timeout):
    database, _, _ = _database(tmp_path)
    try:
        with pytest.raises(ValueError) as raised, database.session(lock_timeout_seconds=timeout):
            pytest.fail("invalid timeout entered transaction")
        assert str(raised.value) == "invalid transaction lock timeout"
    finally:
        database.dispose()


def test_checkpoint_cannot_explicitly_remove_lock_budget():
    with pytest.raises(ValueError, match="checkpoint lock timeout is required"), _checkpoint_session(object(), None):
        pytest.fail("missing lock budget entered publication")
