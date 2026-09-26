from datetime import timedelta
from threading import Event, enumerate as enumerate_threads
from time import monotonic

import pytest

from tests.test_durable_jobs import NOW, _database, _enqueue
from tradingagents.contracts import JobKind, JobStatus
from tradingagents.platform.jobs import DurableJobQueue, JobWorker


def test_long_handler_renews_lease_and_stops_renewal_thread(tmp_path, monkeypatch):
    database, owner, run = _database(tmp_path)
    job = _enqueue(database, owner, run)
    ready = Event()
    heartbeats = []
    heartbeat = DurableJobQueue.heartbeat
    start = monotonic()

    def clock():
        return NOW + timedelta(seconds=monotonic() - start)

    def observe(self, *args, **kwargs):
        result = heartbeat(self, *args, **kwargs)
        heartbeats.append(result)
        if len(heartbeats) >= 4:
            ready.set()
        return result

    monkeypatch.setattr(DurableJobQueue, "heartbeat", observe)

    def handler(job, context):
        assert ready.wait(3), "lease was not renewed during handler execution"
        with database.session() as session:
            assert DurableJobQueue(session).recover_expired(now=clock()) == ()
        with context.publication_session():
            pass

    worker = JobWorker(database, worker_id="renewing", handlers={JobKind.ANALYSIS_RUN: handler},
                       lease_for=timedelta(seconds=.3), clock=clock)
    assert worker.run_once().status is JobStatus.SUCCEEDED
    assert len(heartbeats) >= 4
    assert not any(t.name == f"job-lease-{job.job_id}" for t in enumerate_threads())
    database.dispose()


@pytest.mark.parametrize("failure", ["publish", "handler_error"])
def test_stale_worker_cannot_publish_or_fail_reclaimed_job(tmp_path, failure):
    database, owner, run = _database(tmp_path)
    _enqueue(database, owner, run)
    timestamp = [NOW]

    def handler(job, context):
        timestamp[0] += timedelta(minutes=2)
        with database.session() as session:
            queue = DurableJobQueue(session)
            assert len(queue.recover_expired(now=timestamp[0])) == 1
            reclaimed = queue.claim("replacement", lease_for=timedelta(minutes=1), now=timestamp[0])
            assert reclaimed.job_id == job.job_id
        if failure == "handler_error":
            raise ValueError("late handler failure")
        with context.publication_session():
            pytest.fail("stale worker entered publication transaction")

    worker = JobWorker(database, worker_id="stale", handlers={JobKind.ANALYSIS_RUN: handler},
                       lease_for=timedelta(minutes=1), clock=lambda: timestamp[0])
    result = worker.run_once()
    assert result.status is JobStatus.RUNNING
    assert result.lease_owner == "replacement"
    assert result.attempt == 2
    database.dispose()
