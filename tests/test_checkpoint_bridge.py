"""Opt-in spawned checkpoint RPC to parent-only SQLite commit; no providers."""

import os
from datetime import timedelta
from multiprocessing import get_context
from pathlib import Path
from time import monotonic, sleep
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import select

from tests.test_durable_jobs import NOW, _database, _enqueue
from tests.test_research_supervision import _process_running, assert_child_stopped, request_with
from tests.test_snapshot_checkpoint_codec import checkpoint
from tradingagents.platform.analysis.checkpoint_codec import SnapshotCheckpointCodec
from tradingagents.platform.analysis.checkpoint_saver import CommittedSnapshotSaver
from tradingagents.platform.analysis.checkpoint_store import (
    CheckpointCommit,
    PrivateCheckpointStore,
)
from tradingagents.platform.analysis.engine import AnalysisResult
from tradingagents.platform.analysis.observer import (
    ResearchBudgetExceeded,
    ResearchExecutionFailed,
    ResearchObserver,
)
from tradingagents.platform.analysis.supervision import SupervisedAnalysisEngine
from tradingagents.platform.jobs import DurableJobQueue, JobLeaseError
from tradingagents.platform.jobs.worker import JobCancellationRequested, JobExecutionContext
from tradingagents.platform.persistence import Database
from tradingagents.platform.persistence.models import ResearchCheckpointRow


class CheckpointFixtureEngine:
    supports_checkpoint_bridge = True

    def __init__(self, *, base_config=None):
        self.config = base_config

    def analyze(self, request):
        bridge = request.execution_observer
        Path(self.config["marker"]).write_text(str(os.getpid()))
        value = checkpoint()
        thread = bridge.checkpoint_options["thread_id"]
        value.config["configurable"]["thread_id"] = thread
        value.metadata["thread_id"] = thread
        codec = SnapshotCheckpointCodec(fingerprint=bridge.checkpoint_options["fingerprint"],
                                       nodes={"Market Analyst"})
        if self.config.get("invalid"):
            bridge.commit_checkpoint(b'{"private_secret":"NEVER_ECHO"}')
        saver = CommittedSnapshotSaver(codec=codec, commit=bridge.commit_checkpoint)
        saver.put({"configurable": {"thread_id": thread, "checkpoint_ns": ""}},
                  value.checkpoint, value.metadata, value.checkpoint["channel_versions"])
        model_id = uuid4()
        bridge.on_chat_model_start({}, [], run_id=model_id)
        bridge.on_llm_end(SimpleNamespace(generations=[]), run_id=model_id)
        return AnalysisResult(instrument=request.instrument, analysis_date=request.analysis_date,
            selected_analysts=("market",), profile_name="equity", reference_only=False,
            final_state={"market_report": "Synthetic committed output"}, narrative_signal="REVIEW")


@pytest.mark.parametrize("mode", ["success", "invalid", "exception", "bad_ack", "cancel_after",
                                  "expired_before", "lease_after", "deadline_after"])
def test_spawned_child_waits_for_parent_commit_and_fenced_ack(tmp_path, mode):
    database, owner, run = _database(tmp_path)
    _enqueue(database, owner, run)
    with database.session() as session:
        job = DurableJobQueue(session).claim("fixture", lease_for=timedelta(minutes=5), now=NOW)
    clock = [NOW]
    context = JobExecutionContext(database, job.job_id, "fixture", timedelta(minutes=5), lambda: clock[0])
    codec = SnapshotCheckpointCodec(fingerprint="a" * 64, nodes={"Market Analyst"})
    store = PrivateCheckpointStore(codec=codec)
    captures = []
    cancelled = [False]
    parent_pid = os.getpid()
    elapsed = [0.0]

    def check():
        if cancelled[0]:
            raise JobCancellationRequested("fixture cancellation")
        context.heartbeat()

    observer = ResearchObserver(check_cancelled=check, emit=lambda *_: None,
                                max_seconds=60, clock=lambda: elapsed[0])

    def commit(raw):
        assert os.getpid() == parent_pid
        captures.append(raw)
        if mode == "exception":
            raise RuntimeError("PRIVATE_DB_ERROR_NEVER_ECHO")
        if mode == "expired_before":
            clock[0] = NOW + timedelta(minutes=6)
        result = store.commit(context=context, owner_id=owner, run_id=run.run_id, raw=raw)
        if mode == "bad_ack":
            return CheckpointCommit(result.record_id, result.sequence, "0" * 64)
        if mode == "cancel_after":
            cancelled[0] = True
        if mode == "lease_after":
            clock[0] = NOW + timedelta(minutes=6)
        if mode == "deadline_after":
            elapsed[0] = 61
        return result

    marker = tmp_path / "bridge-child"
    engine = SupervisedAnalysisEngine(base_config={"marker": str(marker), "invalid": mode == "invalid"},
        engine_factory=CheckpointFixtureEngine, checkpoint_codec=codec,
        checkpoint_thread_id=str(run.run_id), checkpoint_commit=commit)
    try:
        if mode == "success":
            assert engine.analyze(request_with(observer)).narrative_signal == "REVIEW"
        else:
            expected = {"cancel_after": JobCancellationRequested, "lease_after": JobLeaseError,
                        "expired_before": JobLeaseError, "deadline_after": ResearchBudgetExceeded}.get(
                            mode, ResearchExecutionFailed)
            with pytest.raises(expected) as raised:
                engine.analyze(request_with(observer))
            assert "NEVER_ECHO" not in str(raised.value)
        assert_child_stopped(marker)
        with database.session() as session:
            row = session.scalar(select(ResearchCheckpointRow))
            assert (row is not None) == (mode in {"success", "bad_ack", "cancel_after", "lease_after", "deadline_after"})
            if row:
                assert b"PRIVATE_RAW_MESSAGE" not in row.payload and b"PRIVATE_REASONING" not in row.payload
        assert observer.started_calls == (1 if mode == "success" else 0)
        assert bool(captures) == (mode != "invalid")
    finally:
        database.dispose()


def test_partial_or_unreviewed_bridge_setup_fails_before_child():
    codec = SnapshotCheckpointCodec(fingerprint="a" * 64, nodes={"Market Analyst"})
    with pytest.raises(ValueError, match="invalid checkpoint bridge configuration"):
        SupervisedAnalysisEngine(checkpoint_codec=codec)
    with pytest.raises(ValueError, match="invalid checkpoint bridge configuration"):
        SupervisedAnalysisEngine(checkpoint_codec=codec, checkpoint_thread_id=str(uuid4()),
                                 checkpoint_commit=lambda raw: None)


def _crash_parent(root, phase):
    root = Path(root)
    database, owner, run = _database(root)
    _enqueue(database, owner, run)
    with database.session() as session:
        job = DurableJobQueue(session).claim("fixture", lease_for=timedelta(minutes=5), now=NOW)
    context = JobExecutionContext(database, job.job_id, "fixture", timedelta(minutes=5), lambda: NOW)
    codec = SnapshotCheckpointCodec(fingerprint="a" * 64, nodes={"Market Analyst"})
    store = PrivateCheckpointStore(codec=codec)

    def paused_commit(raw):
        if phase == "after_commit":
            store.commit(context=context, owner_id=owner, run_id=run.run_id, raw=raw)
        (root / "awaiting-ack").write_text("fixture-only")
        while True:
            sleep(.05)

    observer = ResearchObserver(check_cancelled=lambda: None, emit=lambda *_: None, max_seconds=60)
    SupervisedAnalysisEngine(base_config={"marker": str(root / "child-pid")},
        engine_factory=CheckpointFixtureEngine, checkpoint_codec=codec,
        checkpoint_thread_id=str(run.run_id), checkpoint_commit=paused_commit).analyze(request_with(observer))


@pytest.mark.skipif(os.name != "posix", reason="POSIX parent-crash checkpoint fixture")
@pytest.mark.parametrize("phase", ["before_commit", "after_commit"])
def test_parent_crash_while_child_waits_for_ack_leaves_no_executing_orphan(tmp_path, phase):
    parent = get_context("spawn").Process(target=_crash_parent, args=(str(tmp_path), phase))
    try:
        parent.start()
        until = monotonic() + 25
        while not (tmp_path / "awaiting-ack").exists() and monotonic() < until and parent.is_alive():
            sleep(.05)
        assert (tmp_path / "awaiting-ack").exists()
        child_pid = int((tmp_path / "child-pid").read_text())
        assert _process_running(child_pid)
        parent.kill()
        parent.join(5)
        assert not parent.is_alive()
        until = monotonic() + 10
        while _process_running(child_pid) and monotonic() < until:
            sleep(.05)
        assert not _process_running(child_pid)
        # A terminal zombie is not called "reaped". Read actual DB after crash;
        # commit uncertainty never produces an automatic retry or final output.
        database = Database(f"sqlite:///{tmp_path / 'jobs.db'}")
        try:
            with database.session() as session:
                rows = session.scalars(select(ResearchCheckpointRow)).all()
                assert len(rows) == (1 if phase == "after_commit" else 0)
        finally:
            database.dispose()
    finally:
        if parent.is_alive():
            parent.kill()
        parent.join(5)
        parent.close()
