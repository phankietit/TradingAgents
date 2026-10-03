"""Spawned allowance proof uses original parent observer, no model/provider."""

import os
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from tests.test_checkpoint_bridge import CheckpointFixtureEngine
from tests.test_durable_jobs import NOW, _database, _enqueue
from tests.test_research_supervision import assert_child_stopped, request_with
from tradingagents.platform.analysis.checkpoint_codec import SnapshotCheckpointCodec
from tradingagents.platform.analysis.checkpoint_store import PrivateCheckpointStore
from tradingagents.platform.analysis.observer import (
    ResearchBudgetExceeded,
    ResearchExecutionFailed,
    ResearchObserver,
)
from tradingagents.platform.analysis.supervision import SupervisedAnalysisEngine, _Bridge
from tradingagents.platform.jobs import DurableJobQueue
from tradingagents.platform.jobs.worker import JobExecutionContext


class AllowanceFixtureEngine(CheckpointFixtureEngine):
    def analyze(self, request):
        Path(self.config["marker"]).write_text(str(os.getpid()))
        bridge = request.execution_observer
        values = {"wall_seconds": 60, "model_calls": 128,
            "fingerprint": bridge.checkpoint_options["fingerprint"],
            "thread_id": bridge.checkpoint_options["thread_id"]}
        mode = self.config["mode"]
        if mode == "wall":
            values["wall_seconds"] += 1
        elif mode == "calls":
            values["model_calls"] += 1
        elif mode == "bool":
            values["wall_seconds"] = True
        elif mode == "fingerprint":
            values["fingerprint"] = "0" * 64
        elif mode == "thread":
            values["thread_id"] = str(uuid4())
        elif mode == "extra":
            values["PRIVATE_NEVER_ECHO"] = "PRIVATE_NEVER_ECHO"
        if mode == "extra":
            bridge.rpc("recording_allowance", values)
        else:
            bridge.validate_recording_allowance(**values)
        return super().analyze(request)


@pytest.mark.parametrize("mode", ["success", "wall", "calls", "bool", "fingerprint", "thread", "extra", "expired"])
def test_spawned_allowance_ack_is_bound_to_original_parent_budget(tmp_path, mode):
    database, owner, run = _database(tmp_path)
    try:
        _enqueue(database, owner, run)
        with database.session() as session:
            job = DurableJobQueue(session).claim("fixture", lease_for=timedelta(minutes=5), now=NOW)
        context = JobExecutionContext(database, job.job_id, "fixture", timedelta(minutes=5), lambda: NOW)
        codec = SnapshotCheckpointCodec(fingerprint="a" * 64, nodes={"Market Analyst"})
        store = PrivateCheckpointStore(codec=codec)
        elapsed = [0.0]
        observer = ResearchObserver(check_cancelled=context.raise_if_cancelled, emit=lambda *_: None,
            max_seconds=60, clock=lambda: elapsed[0])
        original_start = observer.started
        elapsed[0] = 61 if mode == "expired" else 10
        commits = []

        def commit(raw):
            commits.append(raw)
            return store.commit(context=context, owner_id=owner, run_id=run.run_id, raw=raw)

        marker = tmp_path / "child.pid"
        engine = SupervisedAnalysisEngine(base_config={"mode": mode, "marker": str(marker)},
            engine_factory=AllowanceFixtureEngine, checkpoint_codec=codec,
            checkpoint_thread_id=str(run.run_id), checkpoint_commit=commit)
        request = request_with(observer)
        if mode == "success":
            engine.analyze(request)
            assert len(commits) == 1 and observer.started_calls == 1
            assert observer.usage["model_calls"] == 1
        else:
            expected = ResearchBudgetExceeded if mode == "expired" else ResearchExecutionFailed
            with pytest.raises(expected) as error:
                engine.analyze(request)
            assert "PRIVATE_NEVER_ECHO" not in str(error.value)
            assert not commits and observer.started_calls == 0
        assert observer.started == original_start and observer.max_seconds == 60 and observer.max_calls == 128
        if marker.exists():
            assert_child_stopped(marker)
        else:
            assert mode == "expired"
    finally:
        database.dispose()


def test_unenabled_bridge_cannot_claim_recording_allowance():
    class ForbiddenPipe:
        def send(self, *args):
            raise AssertionError("disabled bridge attempted RPC")

    bridge = _Bridge(ForbiddenPipe())
    with pytest.raises(ResearchExecutionFailed, match="recording allowance requires review"):
        bridge.validate_recording_allowance(wall_seconds=60, model_calls=128,
            fingerprint="a" * 64, thread_id=str(uuid4()))
