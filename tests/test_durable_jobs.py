"""Durable job idempotency, lease, retry, cancellation, and worker evidence."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from tradingagents.contracts import (
    AssetClass,
    InstrumentContract,
    JobKind,
    JobStatus,
    RunEventType,
    RunManifest,
    RunStatus,
    Tradability,
)
from tradingagents.platform.events import RunEventStore
from tradingagents.platform.jobs import (
    DurableJobQueue,
    JobConflict,
    JobLeaseError,
    JobWorker,
)
from tradingagents.platform.observability import MetricsRegistry
from tradingagents.platform.persistence import (
    Database,
    PlatformRepository,
    downgrade_database,
    upgrade_database,
)

NOW = datetime(2026, 9, 23, 10, 0, tzinfo=UTC)


def _instrument() -> InstrumentContract:
    return InstrumentContract(
        instrument_id=uuid4(),
        symbol="AAPL",
        canonical_symbol=f"AAPL-{uuid4()}",
        display_name="Apple Inc.",
        asset_class=AssetClass.EQUITY,
        tradability=Tradability.INVESTABLE,
        venue="NASDAQ",
        quote_currency="USD",
        timezone="America/New_York",
        session_calendar="XNYS",
        benchmark_symbol="SPY",
    )


def _run(instrument_id: UUID, owner_id: UUID) -> RunManifest:
    return RunManifest(
        run_id=uuid4(),
        owner_id=owner_id,
        instrument_id=instrument_id,
        analysis_as_of=NOW,
        status=RunStatus.QUEUED,
        created_at=NOW,
        selected_analysts=("market",),
        llm_provider="openai",
        quick_model="quick",
        deep_model="deep",
        config_hash="sha256:" + "a" * 64,
        prompt_version="1",
    )


def _database(tmp_path) -> tuple[Database, UUID, RunManifest]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    url = f"sqlite:///{tmp_path / 'jobs.db'}"
    upgrade_database(url)
    database = Database(url)
    owner_id = uuid4()
    instrument = _instrument()
    run = _run(instrument.instrument_id, owner_id)
    with database.session() as session:
        repository = PlatformRepository(session)
        repository.add_instrument(instrument)
        repository.save_run(run)
    return database, owner_id, run


def _enqueue(database: Database, owner_id: UUID, run: RunManifest, **overrides):
    values = {
        "owner_id": owner_id,
        "run_id": run.run_id,
        "idempotency_key": f"analysis:{run.run_id}",
        "payload": {"symbol": "AAPL", "as_of": "2026-09-23"},
        "now": NOW,
    }
    values.update(overrides)
    with database.session() as session:
        return DurableJobQueue(session).enqueue(**values)


@pytest.mark.unit
def test_enqueue_is_idempotent_owner_scoped_and_rejects_changed_input(tmp_path):
    database, owner_id, run = _database(tmp_path)
    first = _enqueue(database, owner_id, run)
    second = _enqueue(database, owner_id, run)
    assert first == second

    with pytest.raises(JobConflict), database.session() as session:
        DurableJobQueue(session).enqueue(
            owner_id=owner_id,
            run_id=run.run_id,
            idempotency_key=f"analysis:{run.run_id}",
            payload={"symbol": "MSFT"},
            now=NOW,
        )

    with database.session() as session:
        queue = DurableJobQueue(session)
        assert queue.get(first.job_id, owner_id) == first
        assert queue.get(first.job_id, uuid4()) is None
    database.dispose()


@pytest.mark.unit
def test_claim_requires_current_worker_lease_and_completion_is_terminal(tmp_path):
    database, owner_id, run = _database(tmp_path)
    queued = _enqueue(database, owner_id, run)
    artifact_id = uuid4()
    with database.session() as session:
        claimed = DurableJobQueue(session).claim(
            "worker-a", lease_for=timedelta(minutes=1), now=NOW
        )
    assert claimed.job_id == queued.job_id
    assert claimed.status is JobStatus.RUNNING
    assert claimed.attempt == 1

    with pytest.raises(JobLeaseError), database.session() as session:
        DurableJobQueue(session).complete(queued.job_id, "worker-b", now=NOW)

    with database.session() as session:
        completed = DurableJobQueue(session).complete(
            queued.job_id,
            "worker-a",
            output_artifact_ids=(artifact_id,),
            now=NOW + timedelta(seconds=1),
        )
    assert completed.status is JobStatus.SUCCEEDED
    assert completed.output_artifact_ids == (artifact_id,)
    assert completed.lease_owner is None
    database.dispose()


@pytest.mark.unit
def test_retry_backoff_and_attempt_limit(tmp_path):
    database, owner_id, run = _database(tmp_path)
    job = _enqueue(database, owner_id, run, max_attempts=2)
    with database.session() as session:
        queue = DurableJobQueue(session)
        queue.claim("worker-a", lease_for=timedelta(minutes=1), now=NOW)
        retry = queue.fail(
            job.job_id,
            "worker-a",
            error_code="PROVIDER_UNAVAILABLE",
            retry_after=timedelta(seconds=30),
            now=NOW + timedelta(seconds=1),
        )
    assert retry.status is JobStatus.RETRY_WAIT

    with database.session() as session:
        queue = DurableJobQueue(session)
        assert (
            queue.claim("worker-b", lease_for=timedelta(minutes=1), now=NOW + timedelta(seconds=30))
            is None
        )
        second_attempt = queue.claim(
            "worker-b", lease_for=timedelta(minutes=1), now=NOW + timedelta(seconds=31)
        )
    assert second_attempt.attempt == 2

    with database.session() as session:
        failed = DurableJobQueue(session).fail(
            job.job_id,
            "worker-b",
            error_code="PROVIDER_UNAVAILABLE",
            retryable=True,
            now=NOW + timedelta(seconds=32),
        )
    assert failed.status is JobStatus.FAILED
    assert failed.completed_at == NOW + timedelta(seconds=32)
    database.dispose()


@pytest.mark.unit
def test_cancellation_is_immediate_before_claim_and_cooperative_while_running(tmp_path):
    database, owner_id, run = _database(tmp_path)
    queued = _enqueue(database, owner_id, run)
    with database.session() as session:
        cancelled = DurableJobQueue(session).request_cancel(queued.job_id, owner_id, now=NOW)
    assert cancelled.status is JobStatus.CANCELLED
    with database.session() as session:
        assert (
            DurableJobQueue(session).claim("worker-a", lease_for=timedelta(minutes=1), now=NOW)
            is None
        )
    database.dispose()

    database, owner_id, run = _database(tmp_path / "running")
    running_job = _enqueue(database, owner_id, run)
    with database.session() as session:
        DurableJobQueue(session).claim("worker-a", lease_for=timedelta(minutes=1), now=NOW)
    with database.session() as session:
        requested = DurableJobQueue(session).request_cancel(
            running_job.job_id, owner_id, now=NOW + timedelta(seconds=1)
        )
    assert requested.status is JobStatus.CANCEL_REQUESTED
    with database.session() as session:
        acknowledged = DurableJobQueue(session).acknowledge_cancel(
            running_job.job_id, "worker-a", now=NOW + timedelta(seconds=2)
        )
    assert acknowledged.status is JobStatus.CANCELLED
    database.dispose()


@pytest.mark.unit
def test_expired_lease_resumes_then_fails_after_attempt_budget(tmp_path):
    database, owner_id, run = _database(tmp_path)
    job = _enqueue(database, owner_id, run, max_attempts=2)
    with database.session() as session:
        DurableJobQueue(session).claim("worker-a", lease_for=timedelta(seconds=10), now=NOW)
    with database.session() as session:
        recovered = DurableJobQueue(session).recover_expired(now=NOW + timedelta(seconds=11))
    assert recovered[0].status is JobStatus.RETRY_WAIT
    assert recovered[0].error_code == "LEASE_EXPIRED"

    with database.session() as session:
        DurableJobQueue(session).claim(
            "worker-b", lease_for=timedelta(seconds=10), now=NOW + timedelta(seconds=11)
        )
    with database.session() as session:
        exhausted = DurableJobQueue(session).recover_expired(now=NOW + timedelta(seconds=22))
    assert exhausted[0].job_id == job.job_id
    assert exhausted[0].status is JobStatus.FAILED
    database.dispose()


@pytest.mark.unit
def test_heartbeat_extends_the_current_lease(tmp_path):
    database, owner_id, run = _database(tmp_path)
    job = _enqueue(database, owner_id, run)
    with database.session() as session:
        queue = DurableJobQueue(session)
        queue.claim("worker-a", lease_for=timedelta(seconds=30), now=NOW)
        heartbeat = queue.heartbeat(
            job.job_id,
            "worker-a",
            lease_for=timedelta(seconds=60),
            now=NOW + timedelta(seconds=20),
        )
    assert heartbeat.lease_expires_at == NOW + timedelta(seconds=80)

    with database.session() as session:
        assert not DurableJobQueue(session).recover_expired(now=NOW + timedelta(seconds=31))
    with database.session() as session:
        recovered = DurableJobQueue(session).recover_expired(now=NOW + timedelta(seconds=81))
    assert recovered[0].status is JobStatus.RETRY_WAIT
    database.dispose()


@pytest.mark.unit
def test_worker_commits_claim_before_handler_and_records_outputs(tmp_path):
    database, owner_id, run = _database(tmp_path)
    job = _enqueue(database, owner_id, run)
    artifact_id = uuid4()

    def handler(claimed, _context):
        with database.session() as session:
            persisted = DurableJobQueue(session).get(claimed.job_id, owner_id)
        assert persisted.status is JobStatus.RUNNING
        return (artifact_id,)

    metrics = MetricsRegistry()
    worker = JobWorker(
        database,
        worker_id="worker-a",
        handlers={JobKind.ANALYSIS_RUN: handler},
        clock=lambda: NOW + timedelta(seconds=1),
        metrics=metrics,
    )
    completed = worker.run_once()
    assert completed.job_id == job.job_id
    assert completed.status is JobStatus.SUCCEEDED
    assert completed.output_artifact_ids == (artifact_id,)
    with database.session() as session:
        persisted_run = PlatformRepository(session).get_run(run.run_id, owner_id)
        events = RunEventStore(session).list_after(owner_id, run.run_id)
    assert persisted_run.status is RunStatus.SUCCEEDED
    assert [event.event_type for event in events] == [
        RunEventType.RUN_STARTED,
        RunEventType.RUN_SUCCEEDED,
    ]
    rendered_metrics = metrics.render()
    assert 'status="running"' in rendered_metrics
    assert 'status="succeeded"' in rendered_metrics
    database.dispose()


@pytest.mark.unit
def test_worker_retries_without_persisting_exception_message(tmp_path):
    database, owner_id, run = _database(tmp_path)
    _enqueue(database, owner_id, run)

    def handler(_job, _context):
        raise RuntimeError("secret-looking detail must not be persisted")

    worker = JobWorker(
        database,
        worker_id="worker-a",
        handlers={JobKind.ANALYSIS_RUN: handler},
        clock=lambda: NOW + timedelta(seconds=1),
    )
    retry = worker.run_once()
    assert retry.status is JobStatus.RETRY_WAIT
    assert retry.error_code == "HANDLER_ERROR"
    assert retry.error_message == "RuntimeError"
    with database.session() as session:
        persisted_run = PlatformRepository(session).get_run(run.run_id, owner_id)
        events = RunEventStore(session).list_after(owner_id, run.run_id)
    assert persisted_run.status is RunStatus.RUNNING
    assert [event.event_type for event in events] == [
        RunEventType.RUN_STARTED,
        RunEventType.RUN_RETRYING,
    ]
    database.dispose()


@pytest.mark.integration
def test_postgresql_skip_locked_assigns_distinct_jobs():
    url = os.environ.get("TEST_POSTGRES_URL")
    if not url:
        pytest.skip("TEST_POSTGRES_URL is required for the PostgreSQL integration gate")

    database = Database(url)
    try:
        upgrade_database(url)
        owner_id = uuid4()
        instrument = _instrument()
        first_run = _run(instrument.instrument_id, owner_id)
        second_run = _run(instrument.instrument_id, owner_id)
        with database.session() as session:
            repository = PlatformRepository(session)
            repository.add_instrument(instrument)
            repository.save_run(first_run)
            repository.save_run(second_run)
            queue = DurableJobQueue(session)
            for run in (first_run, second_run):
                queue.enqueue(
                    owner_id=owner_id,
                    run_id=run.run_id,
                    idempotency_key=f"analysis:{run.run_id}",
                    payload={"symbol": "AAPL"},
                    now=NOW,
                )

        with database.session() as first_session:
            first = DurableJobQueue(first_session).claim(
                "worker-a", lease_for=timedelta(minutes=1), now=NOW
            )
            with database.session() as second_session:
                second = DurableJobQueue(second_session).claim(
                    "worker-b", lease_for=timedelta(minutes=1), now=NOW
                )
            assert first.job_id != second.job_id
    finally:
        downgrade_database(url)
        database.dispose()
