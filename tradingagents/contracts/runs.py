"""Analysis run lifecycle and reproducibility contracts."""

from __future__ import annotations

from enum import Enum
from uuid import UUID

from pydantic import AwareDatetime, model_validator

from .base import ContentHash, NonEmptyText, VersionedContract


class RunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RunManifest(VersionedContract):
    run_id: UUID
    owner_id: UUID
    instrument_id: UUID
    analysis_as_of: AwareDatetime
    status: RunStatus
    created_at: AwareDatetime
    started_at: AwareDatetime | None = None
    completed_at: AwareDatetime | None = None
    selected_analysts: tuple[NonEmptyText, ...]
    llm_provider: NonEmptyText
    quick_model: NonEmptyText
    deep_model: NonEmptyText
    config_hash: ContentHash
    prompt_version: NonEmptyText
    snapshot_ids: tuple[UUID, ...] = ()
    error_code: str | None = None
    error_message: str | None = None

    @model_validator(mode="after")
    def validate_lifecycle(self):
        if self.started_at and self.started_at < self.created_at:
            raise ValueError("started_at must not precede created_at")
        if self.completed_at:
            if not self.started_at:
                raise ValueError("completed_at requires started_at")
            if self.completed_at < self.started_at:
                raise ValueError("completed_at must not precede started_at")
        terminal = {RunStatus.SUCCEEDED, RunStatus.FAILED, RunStatus.CANCELLED}
        if self.status in terminal and not self.completed_at:
            raise ValueError("terminal run status requires completed_at")
        if self.status is RunStatus.FAILED and not self.error_code:
            raise ValueError("failed run requires error_code")
        return self
