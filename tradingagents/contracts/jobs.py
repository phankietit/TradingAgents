"""Durable analysis-job lifecycle contracts."""

from __future__ import annotations

from enum import Enum
from uuid import UUID

from pydantic import AwareDatetime, Field, JsonValue, model_validator

from .base import NonEmptyText, VersionedContract


class JobKind(str, Enum):
    ANALYSIS_RUN = "analysis.run"


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    RETRY_WAIT = "retry_wait"
    CANCEL_REQUESTED = "cancel_requested"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


TERMINAL_JOB_STATUSES = {JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED}
LEASED_JOB_STATUSES = {JobStatus.RUNNING, JobStatus.CANCEL_REQUESTED}


class JobRecord(VersionedContract):
    job_id: UUID
    owner_id: UUID
    run_id: UUID
    kind: JobKind
    idempotency_key: str = Field(min_length=1, max_length=128)
    status: JobStatus
    payload: dict[str, JsonValue] = Field(default_factory=dict)
    attempt: int = Field(ge=0)
    max_attempts: int = Field(ge=1, le=20)
    available_at: AwareDatetime
    lease_owner: str | None = Field(default=None, min_length=1, max_length=128)
    lease_expires_at: AwareDatetime | None = None
    created_at: AwareDatetime
    updated_at: AwareDatetime
    completed_at: AwareDatetime | None = None
    output_artifact_ids: tuple[UUID, ...] = ()
    error_code: NonEmptyText | None = None
    error_message: str | None = None

    @model_validator(mode="after")
    def validate_lifecycle(self):
        has_complete_lease = self.lease_owner is not None and self.lease_expires_at is not None
        if (self.lease_owner is None) != (self.lease_expires_at is None):
            raise ValueError("lease_owner and lease_expires_at must be set together")
        if self.status in LEASED_JOB_STATUSES and not has_complete_lease:
            raise ValueError("running jobs require a complete lease")
        if self.status not in LEASED_JOB_STATUSES and has_complete_lease:
            raise ValueError("only running jobs may retain a lease")
        if self.status in TERMINAL_JOB_STATUSES and self.completed_at is None:
            raise ValueError("terminal jobs require completed_at")
        if self.status not in TERMINAL_JOB_STATUSES and self.completed_at is not None:
            raise ValueError("non-terminal jobs cannot have completed_at")
        if self.status is JobStatus.FAILED and not self.error_code:
            raise ValueError("failed jobs require error_code")
        if self.updated_at < self.created_at:
            raise ValueError("updated_at must not precede created_at")
        return self
