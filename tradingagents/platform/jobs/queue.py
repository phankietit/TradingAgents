"""Transactional durable queue with leases, retries, and cancellation."""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from tradingagents._compat import UTC
from tradingagents.contracts import JobKind, JobRecord, JobStatus
from tradingagents.platform.persistence.models import JobRow


class JobConflict(ValueError):
    """An idempotency key or run was reused with different job input."""


class JobLeaseError(RuntimeError):
    """A worker attempted to mutate a job without a current lease."""


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _record(row: JobRow) -> JobRecord:
    return JobRecord(
        job_id=row.job_id,
        owner_id=row.owner_id,
        run_id=row.run_id,
        schema_version=row.schema_version,
        kind=JobKind(row.kind),
        idempotency_key=row.idempotency_key,
        status=JobStatus(row.status),
        payload=row.payload,
        attempt=row.attempt,
        max_attempts=row.max_attempts,
        available_at=_utc(row.available_at),
        lease_owner=row.lease_owner,
        lease_expires_at=_utc(row.lease_expires_at) if row.lease_expires_at else None,
        created_at=_utc(row.created_at),
        updated_at=_utc(row.updated_at),
        completed_at=_utc(row.completed_at) if row.completed_at else None,
        output_artifact_ids=tuple(UUID(value) for value in row.output_artifact_ids),
        error_code=row.error_code,
        error_message=row.error_message,
    )


class DurableJobQueue:
    def __init__(self, session: Session):
        self.session = session

    def enqueue(
        self,
        *,
        owner_id: UUID,
        run_id: UUID,
        idempotency_key: str,
        payload: dict,
        kind: JobKind = JobKind.ANALYSIS_RUN,
        max_attempts: int = 3,
        available_at: datetime | None = None,
        job_id: UUID | None = None,
        now: datetime | None = None,
    ) -> JobRecord:
        timestamp = _utc(now or datetime.now(UTC))
        available = _utc(available_at or timestamp)
        existing = self.session.scalar(
            select(JobRow)
            .where(JobRow.owner_id == owner_id, JobRow.idempotency_key == idempotency_key)
            .with_for_update()
        )
        if existing:
            if (
                existing.run_id != run_id
                or existing.kind != kind.value
                or existing.payload != payload
                or existing.max_attempts != max_attempts
            ):
                raise JobConflict("idempotency key already belongs to different job input")
            return _record(existing)

        run_job = self.session.scalar(
            select(JobRow).where(JobRow.run_id == run_id).with_for_update()
        )
        if run_job:
            raise JobConflict("run_id already belongs to another job")

        candidate = JobRecord(
            job_id=job_id or uuid4(),
            owner_id=owner_id,
            run_id=run_id,
            kind=kind,
            idempotency_key=idempotency_key,
            status=JobStatus.QUEUED,
            payload=payload,
            attempt=0,
            max_attempts=max_attempts,
            available_at=available,
            created_at=timestamp,
            updated_at=timestamp,
        )
        row = JobRow(
            job_id=candidate.job_id,
            owner_id=owner_id,
            run_id=run_id,
            schema_version=candidate.schema_version,
            kind=kind.value,
            idempotency_key=idempotency_key,
            status=candidate.status.value,
            payload=payload,
            attempt=0,
            max_attempts=max_attempts,
            available_at=available,
            lease_owner=None,
            lease_expires_at=None,
            created_at=timestamp,
            updated_at=timestamp,
            completed_at=None,
            output_artifact_ids=[],
            error_code=None,
            error_message=None,
        )
        try:
            with self.session.begin_nested():
                self.session.add(row)
                self.session.flush()
            return candidate
        except IntegrityError as error:
            concurrent = self.session.scalar(
                select(JobRow).where(
                    JobRow.owner_id == owner_id,
                    JobRow.idempotency_key == idempotency_key,
                )
            )
            if concurrent and (
                concurrent.run_id == run_id
                and concurrent.kind == kind.value
                and concurrent.payload == payload
                and concurrent.max_attempts == max_attempts
            ):
                return _record(concurrent)
            raise JobConflict("job conflicts with an existing idempotency key or run") from error

    def get(self, job_id: UUID, owner_id: UUID) -> JobRecord | None:
        row = self.session.scalar(
            select(JobRow).where(JobRow.job_id == job_id, JobRow.owner_id == owner_id)
        )
        return _record(row) if row else None

    def get_by_run(self, run_id: UUID, owner_id: UUID) -> JobRecord | None:
        row = self.session.scalar(
            select(JobRow).where(JobRow.run_id == run_id, JobRow.owner_id == owner_id)
        )
        return _record(row) if row else None

    def get_by_idempotency(self, owner_id: UUID, idempotency_key: str) -> JobRecord | None:
        row = self.session.scalar(
            select(JobRow).where(
                JobRow.owner_id == owner_id,
                JobRow.idempotency_key == idempotency_key,
            )
        )
        return _record(row) if row else None

    def claim(
        self,
        worker_id: str,
        *,
        lease_for: timedelta,
        now: datetime | None = None,
    ) -> JobRecord | None:
        if not worker_id or len(worker_id) > 128:
            raise ValueError("worker_id must contain 1 to 128 characters")
        if lease_for <= timedelta(0):
            raise ValueError("lease_for must be positive")
        timestamp = _utc(now or datetime.now(UTC))
        row = self.session.scalar(
            select(JobRow)
            .where(
                JobRow.status.in_([JobStatus.QUEUED.value, JobStatus.RETRY_WAIT.value]),
                JobRow.available_at <= timestamp,
                JobRow.attempt < JobRow.max_attempts,
            )
            .order_by(JobRow.available_at, JobRow.created_at, JobRow.job_id)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        if row is None:
            return None
        row.status = JobStatus.RUNNING.value
        row.attempt += 1
        row.lease_owner = worker_id
        row.lease_expires_at = timestamp + lease_for
        row.updated_at = timestamp
        row.error_code = None
        row.error_message = None
        self.session.flush()
        return _record(row)

    def heartbeat(
        self,
        job_id: UUID,
        worker_id: str,
        *,
        lease_for: timedelta,
        now: datetime | None = None,
    ) -> JobRecord:
        if lease_for <= timedelta(0):
            raise ValueError("lease_for must be positive")
        timestamp = _utc(now or datetime.now(UTC))
        row = self._leased_row(job_id, worker_id, timestamp)
        row.lease_expires_at = timestamp + lease_for
        row.updated_at = timestamp
        self.session.flush()
        return _record(row)

    def request_cancel(
        self, job_id: UUID, owner_id: UUID, *, now: datetime | None = None
    ) -> JobRecord | None:
        timestamp = _utc(now or datetime.now(UTC))
        row = self.session.scalar(
            select(JobRow)
            .where(JobRow.job_id == job_id, JobRow.owner_id == owner_id)
            .with_for_update()
        )
        if row is None:
            return None
        status = JobStatus(row.status)
        if status in {JobStatus.QUEUED, JobStatus.RETRY_WAIT}:
            self._finish(row, JobStatus.CANCELLED, timestamp)
        elif status is JobStatus.RUNNING:
            row.status = JobStatus.CANCEL_REQUESTED.value
            row.updated_at = timestamp
        self.session.flush()
        return _record(row)

    def cancellation_requested(self, job_id: UUID, worker_id: str) -> bool:
        row = self.session.get(JobRow, job_id)
        return bool(
            row
            and row.lease_owner == worker_id
            and JobStatus(row.status) is JobStatus.CANCEL_REQUESTED
        )

    def acknowledge_cancel(
        self, job_id: UUID, worker_id: str, *, now: datetime | None = None
    ) -> JobRecord:
        timestamp = _utc(now or datetime.now(UTC))
        row = self._leased_row(job_id, worker_id, timestamp)
        if JobStatus(row.status) is not JobStatus.CANCEL_REQUESTED:
            raise JobLeaseError("job does not have a cancellation request")
        self._finish(row, JobStatus.CANCELLED, timestamp)
        self.session.flush()
        return _record(row)

    def complete(
        self,
        job_id: UUID,
        worker_id: str,
        *,
        output_artifact_ids: tuple[UUID, ...] = (),
        now: datetime | None = None,
    ) -> JobRecord:
        timestamp = _utc(now or datetime.now(UTC))
        row = self._leased_row(job_id, worker_id, timestamp)
        if JobStatus(row.status) is JobStatus.CANCEL_REQUESTED:
            self._finish(row, JobStatus.CANCELLED, timestamp)
        else:
            row.output_artifact_ids = [str(value) for value in output_artifact_ids]
            self._finish(row, JobStatus.SUCCEEDED, timestamp)
        self.session.flush()
        return _record(row)

    def fail(
        self,
        job_id: UUID,
        worker_id: str,
        *,
        error_code: str,
        error_message: str | None = None,
        retryable: bool = True,
        retry_after: timedelta = timedelta(0),
        now: datetime | None = None,
    ) -> JobRecord:
        if not error_code:
            raise ValueError("error_code is required")
        if retry_after < timedelta(0):
            raise ValueError("retry_after cannot be negative")
        timestamp = _utc(now or datetime.now(UTC))
        row = self._leased_row(job_id, worker_id, timestamp)
        if JobStatus(row.status) is JobStatus.CANCEL_REQUESTED:
            self._finish(row, JobStatus.CANCELLED, timestamp)
        elif retryable and row.attempt < row.max_attempts:
            row.status = JobStatus.RETRY_WAIT.value
            row.available_at = timestamp + retry_after
            row.updated_at = timestamp
            row.lease_owner = None
            row.lease_expires_at = None
            row.error_code = error_code[:128]
            row.error_message = error_message[:2048] if error_message else None
        else:
            row.error_code = error_code[:128]
            row.error_message = error_message[:2048] if error_message else None
            self._finish(row, JobStatus.FAILED, timestamp, preserve_error=True)
        self.session.flush()
        return _record(row)

    def recover_expired(self, *, now: datetime | None = None) -> tuple[JobRecord, ...]:
        timestamp = _utc(now or datetime.now(UTC))
        rows = self.session.scalars(
            select(JobRow)
            .where(
                JobRow.status.in_([JobStatus.RUNNING.value, JobStatus.CANCEL_REQUESTED.value]),
                JobRow.lease_expires_at <= timestamp,
            )
            .order_by(JobRow.lease_expires_at, JobRow.job_id)
            .with_for_update(skip_locked=True)
        ).all()
        for row in rows:
            if JobStatus(row.status) is JobStatus.CANCEL_REQUESTED:
                self._finish(row, JobStatus.CANCELLED, timestamp)
            elif row.attempt < row.max_attempts:
                row.status = JobStatus.RETRY_WAIT.value
                row.available_at = timestamp
                row.updated_at = timestamp
                row.lease_owner = None
                row.lease_expires_at = None
                row.error_code = "LEASE_EXPIRED"
                row.error_message = None
            else:
                row.error_code = "LEASE_EXPIRED"
                row.error_message = None
                self._finish(row, JobStatus.FAILED, timestamp, preserve_error=True)
        self.session.flush()
        return tuple(_record(row) for row in rows)

    def _leased_row(self, job_id: UUID, worker_id: str, now: datetime) -> JobRow:
        row = self.session.scalar(select(JobRow).where(JobRow.job_id == job_id).with_for_update())
        if (
            row is None
            or row.lease_owner != worker_id
            or JobStatus(row.status) not in {JobStatus.RUNNING, JobStatus.CANCEL_REQUESTED}
            or row.lease_expires_at is None
            or _utc(row.lease_expires_at) <= now
        ):
            raise JobLeaseError("worker does not hold a current lease for this job")
        return row

    @staticmethod
    def _finish(
        row: JobRow, status: JobStatus, timestamp: datetime, *, preserve_error: bool = False
    ) -> None:
        row.status = status.value
        row.updated_at = timestamp
        row.completed_at = timestamp
        row.lease_owner = None
        row.lease_expires_at = None
        if not preserve_error:
            row.error_code = None
            row.error_message = None
