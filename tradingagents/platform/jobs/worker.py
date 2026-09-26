"""Process one durable job at a time without holding execution-time DB locks."""

from __future__ import annotations

import logging
from collections.abc import Callable
from contextlib import contextmanager
from datetime import datetime, timedelta
from threading import Event, Thread
from uuid import UUID

from sqlalchemy.orm import Session

from tradingagents._compat import UTC
from tradingagents.contracts import JobKind, JobRecord, JobStatus, RunEventType, RunStatus
from tradingagents.platform.events import RunEventStore
from tradingagents.platform.observability import MetricsRegistry
from tradingagents.platform.persistence import Database, PlatformRepository

from .queue import DurableJobQueue, JobLeaseError


class JobCancellationRequested(RuntimeError):
    """A cooperative handler stopped after an owner cancellation request."""


class JobExecutionContext:
    def __init__(
        self,
        database: Database,
        job_id: UUID,
        worker_id: str,
        lease_for: timedelta,
        clock: Callable[[], datetime],
    ):
        self.database = database
        self.job_id = job_id
        self.worker_id = worker_id
        self.lease_for = lease_for
        self.clock = clock
        self._lease_error = None

    def _check_lease(self):
        if self._lease_error is not None:
            raise JobLeaseError("background lease renewal failed") from self._lease_error

    @contextmanager
    def keepalive(self):
        """Renew on a separate session while a synchronous model call runs."""
        stopped = Event()

        def renew():
            while not stopped.wait(self.lease_for.total_seconds() / 3):
                try:
                    self.heartbeat()
                except Exception as error:
                    self._lease_error = error
                    return

        thread = Thread(target=renew, name=f"job-lease-{self.job_id}", daemon=True)
        thread.start()
        try:
            yield
        finally:
            stopped.set()
            thread.join()
        self._check_lease()

    @contextmanager
    def publication_session(self):
        """Fence publication against cancellation/recovery in the same transaction."""
        self._check_lease()
        with self.database.session() as session:
            job = DurableJobQueue(session).heartbeat(
                self.job_id, self.worker_id, lease_for=self.lease_for, now=self.clock())
            if job.status is JobStatus.CANCEL_REQUESTED:
                raise JobCancellationRequested("job cancellation requested")
            yield session

    def heartbeat(self) -> JobRecord:
        self._check_lease()
        with self.database.session() as session:
            return DurableJobQueue(session).heartbeat(
                self.job_id,
                self.worker_id,
                lease_for=self.lease_for,
                now=self.clock(),
            )

    def cancellation_requested(self) -> bool:
        with self.database.session() as session:
            return DurableJobQueue(session).cancellation_requested(self.job_id, self.worker_id)

    def raise_if_cancelled(self) -> None:
        self._check_lease()
        if self.cancellation_requested():
            raise JobCancellationRequested("job cancellation requested")


JobHandler = Callable[[JobRecord, JobExecutionContext], tuple[UUID, ...] | None]
logger = logging.getLogger("tradingagents.platform.jobs")


class JobWorker:
    def __init__(
        self,
        database: Database,
        *,
        worker_id: str,
        handlers: dict[JobKind, JobHandler],
        lease_for: timedelta = timedelta(minutes=5),
        retry_base: timedelta = timedelta(seconds=30),
        clock: Callable[[], datetime] | None = None,
        metrics: MetricsRegistry | None = None,
    ):
        if retry_base < timedelta(0):
            raise ValueError("retry_base cannot be negative")
        self.database = database
        self.worker_id = worker_id
        self.handlers = handlers
        self.lease_for = lease_for
        self.retry_base = retry_base
        self.clock = clock or (lambda: datetime.now(UTC))
        self.metrics = metrics

    def run_once(self) -> JobRecord | None:
        now = self.clock()
        with self.database.session() as session:
            queue = DurableJobQueue(session)
            for recovered in queue.recover_expired(now=now):
                self._record_job_state(session, recovered, now)
            job = queue.claim(self.worker_id, lease_for=self.lease_for, now=now)
            if job is not None:
                self._record_job_state(session, job, now)
        if job is None:
            return None

        handler = self.handlers.get(job.kind)
        if handler is None:
            with self.database.session() as session:
                timestamp = self.clock()
                failed = DurableJobQueue(session).fail(
                    job.job_id,
                    self.worker_id,
                    error_code="HANDLER_NOT_REGISTERED",
                    retryable=False,
                    now=timestamp,
                )
                self._record_job_state(session, failed, timestamp)
                return failed

        context = JobExecutionContext(
            self.database,
            job.job_id,
            self.worker_id,
            self.lease_for,
            self.clock,
        )
        try:
            with context.keepalive():
                output_artifact_ids = handler(job, context) or ()
            with self.database.session() as session:
                timestamp = self.clock()
                completed = DurableJobQueue(session).complete(
                    job.job_id,
                    self.worker_id,
                    output_artifact_ids=output_artifact_ids,
                    now=timestamp,
                )
                self._record_job_state(session, completed, timestamp)
                return completed
        except JobLeaseError:
            # A stale worker has no authority to mark a recovered job failed.
            with self.database.session() as session:
                return DurableJobQueue(session).get(job.job_id, job.owner_id)
        except JobCancellationRequested:
            try:
                with self.database.session() as session:
                    timestamp = self.clock()
                    cancelled = DurableJobQueue(session).acknowledge_cancel(
                        job.job_id, self.worker_id, now=timestamp
                    )
                    self._record_job_state(session, cancelled, timestamp)
                    return cancelled
            except JobLeaseError:
                with self.database.session() as session:
                    return DurableJobQueue(session).get(job.job_id, job.owner_id)
        except Exception as exc:
            retry_after = self.retry_base * (2 ** max(job.attempt - 1, 0))
            try:
                with self.database.session() as session:
                    timestamp = self.clock()
                    failed = DurableJobQueue(session).fail(
                        job.job_id,
                        self.worker_id,
                        error_code="HANDLER_ERROR",
                        error_message=type(exc).__name__,
                        retryable=True,
                        retry_after=retry_after,
                        now=timestamp,
                    )
                    self._record_job_state(session, failed, timestamp)
                    return failed
            except JobLeaseError:
                with self.database.session() as session:
                    return DurableJobQueue(session).get(job.job_id, job.owner_id)

    def _record_job_state(self, session: Session, job: JobRecord, timestamp: datetime) -> None:
        repository = PlatformRepository(session)
        run = repository.get_run(job.run_id, job.owner_id)
        if run is None:
            return
        event_type: RunEventType | None = None
        payload: dict[str, object] = {"job_id": str(job.job_id), "attempt": job.attempt}

        if job.status is JobStatus.RUNNING:
            if run.status is RunStatus.QUEUED:
                repository.save_run(
                    run.model_copy(update={"status": RunStatus.RUNNING, "started_at": timestamp})
                )
            event_type = RunEventType.RUN_STARTED
        elif job.status is JobStatus.RETRY_WAIT:
            event_type = RunEventType.RUN_RETRYING
            payload["error_code"] = job.error_code
        elif job.status in {JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED}:
            status_map = {
                JobStatus.SUCCEEDED: (RunStatus.SUCCEEDED, RunEventType.RUN_SUCCEEDED),
                JobStatus.FAILED: (RunStatus.FAILED, RunEventType.RUN_FAILED),
                JobStatus.CANCELLED: (RunStatus.CANCELLED, RunEventType.RUN_CANCELLED),
            }
            run_status, event_type = status_map[job.status]
            update = {
                "status": run_status,
                "started_at": run.started_at or timestamp,
                "completed_at": timestamp,
                "error_code": job.error_code if run_status is RunStatus.FAILED else None,
                "error_message": None,
            }
            repository.save_run(run.model_copy(update=update))
            if job.error_code:
                payload["error_code"] = job.error_code
            if job.output_artifact_ids:
                payload["output_artifact_ids"] = [
                    str(artifact_id) for artifact_id in job.output_artifact_ids
                ]

        if event_type is not None:
            RunEventStore(session).append(
                owner_id=job.owner_id,
                run_id=job.run_id,
                event_type=event_type,
                occurred_at=timestamp,
                payload=payload,
            )
            if self.metrics is not None:
                self.metrics.observe_job(job.status.value)
            logger.info(
                "job_transition",
                extra={
                    "job_id": str(job.job_id),
                    "run_id": str(job.run_id),
                    "job_status": job.status.value,
                    "attempt": job.attempt,
                },
            )
