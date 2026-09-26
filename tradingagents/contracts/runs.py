"""Analysis run lifecycle and reproducibility contracts."""

from __future__ import annotations

from enum import Enum
from typing import Annotated
from uuid import UUID

from pydantic import AwareDatetime, Field, model_validator

from .base import ContentHash, NonEmptyText, StrictContract, VersionedContract, Weight


class DecisionRunInputs(StrictContract):
    snapshots_by_analyst: dict[str, tuple[UUID, ...]]
    source_max_age_seconds: dict[str, Annotated[int, Field(ge=0, le=315360000)]]
    portfolio_snapshot_id: UUID | None = None
    policy_id: UUID | None = None
    policy_version: NonEmptyText | None = None
    requested_target_weight: Weight | None = None
    risk_snapshot_ids: tuple[UUID, ...] = Field(default=(), max_length=100)

    @model_validator(mode="after")
    def validate_inputs(self):
        if not self.snapshots_by_analyst or len(self.snapshots_by_analyst) > 4:
            raise ValueError("snapshot analysis requires one to four roles")
        if set(self.source_max_age_seconds) != set(self.snapshots_by_analyst):
            raise ValueError("every snapshot role requires an explicit freshness limit")
        if any(not 1 <= len(ids) <= 16 or len(ids) != len(set(ids))
               for ids in self.snapshots_by_analyst.values()):
            raise ValueError("snapshot roles require bounded unique sources")
        risk = (self.portfolio_snapshot_id, self.policy_id, self.policy_version, self.requested_target_weight)
        if any(item is not None for item in risk) and not all(item is not None for item in risk):
            raise ValueError("risk proposal requires portfolio, policy version and owner target together")
        if len(self.risk_snapshot_ids) != len(set(self.risk_snapshot_ids)):
            raise ValueError("duplicate risk snapshots")
        return self

    def snapshot_ids(self):
        return tuple(sorted(set(self.risk_snapshot_ids).union(
            key for ids in self.snapshots_by_analyst.values() for key in ids), key=str))


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
    decision_inputs: DecisionRunInputs | None = None
    error_code: str | None = None
    error_message: str | None = None

    @model_validator(mode="after")
    def validate_lifecycle(self):
        if self.decision_inputs is not None:
            if set(self.decision_inputs.snapshots_by_analyst) != set(self.selected_analysts):
                raise ValueError("run snapshot roles must match selected analysts")
            if set(self.decision_inputs.snapshot_ids()) != set(self.snapshot_ids):
                raise ValueError("run snapshots must cover exact analysis and risk inputs")
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
