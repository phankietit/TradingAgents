"""Process one durable job at a time without holding execution-time DB locks."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import UUID

from tradingagents.contracts import JobKind, JobRecord
from tradingagents.platform.persistence import Database

from .queue import DurableJobQueue


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

    def heartbeat(self) -> JobRecord:
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
        if self.cancellation_requested():
            raise JobCancellationRequested("job cancellation requested")


JobHandler = Callable[[JobRecord, JobExecutionContext], tuple[UUID, ...] | None]


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
    ):
        if retry_base < timedelta(0):
            raise ValueError("retry_base cannot be negative")
        self.database = database
        self.worker_id = worker_id
        self.handlers = handlers
        self.lease_for = lease_for
        self.retry_base = retry_base
        self.clock = clock or (lambda: datetime.now(UTC))

    def run_once(self) -> JobRecord | None:
        now = self.clock()
        with self.database.session() as session:
            queue = DurableJobQueue(session)
            queue.recover_expired(now=now)
            job = queue.claim(self.worker_id, lease_for=self.lease_for, now=now)
        if job is None:
            return None

        handler = self.handlers.get(job.kind)
        if handler is None:
            with self.database.session() as session:
                return DurableJobQueue(session).fail(
                    job.job_id,
                    self.worker_id,
                    error_code="HANDLER_NOT_REGISTERED",
                    retryable=False,
                    now=self.clock(),
                )

        context = JobExecutionContext(
            self.database,
            job.job_id,
            self.worker_id,
            self.lease_for,
            self.clock,
        )
        try:
            output_artifact_ids = handler(job, context) or ()
            with self.database.session() as session:
                return DurableJobQueue(session).complete(
                    job.job_id,
                    self.worker_id,
                    output_artifact_ids=output_artifact_ids,
                    now=self.clock(),
                )
        except JobCancellationRequested:
            with self.database.session() as session:
                return DurableJobQueue(session).acknowledge_cancel(
                    job.job_id, self.worker_id, now=self.clock()
                )
        except Exception as exc:
            retry_after = self.retry_base * (2 ** max(job.attempt - 1, 0))
            with self.database.session() as session:
                return DurableJobQueue(session).fail(
                    job.job_id,
                    self.worker_id,
                    error_code="HANDLER_ERROR",
                    error_message=type(exc).__name__,
                    retryable=True,
                    retry_after=retry_after,
                    now=self.clock(),
                )
