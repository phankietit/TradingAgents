"""Append-only run event contracts for resumable user interfaces."""

from __future__ import annotations

from enum import Enum
from uuid import UUID

from pydantic import AwareDatetime, Field, JsonValue

from .base import VersionedContract


class RunEventType(str, Enum):
    RUN_QUEUED = "run.queued"
    RUN_STARTED = "run.started"
    STAGE_STARTED = "stage.started"
    STAGE_COMPLETED = "stage.completed"
    ARTIFACT_CREATED = "artifact.created"
    DECISION_READY = "decision.ready"
    RUN_RETRYING = "run.retrying"
    RUN_CANCEL_REQUESTED = "run.cancel_requested"
    RUN_CANCELLED = "run.cancelled"
    RUN_FAILED = "run.failed"
    RUN_SUCCEEDED = "run.succeeded"


TERMINAL_RUN_EVENTS = {
    RunEventType.RUN_CANCELLED,
    RunEventType.RUN_FAILED,
    RunEventType.RUN_SUCCEEDED,
}


class RunEvent(VersionedContract):
    event_id: UUID
    owner_id: UUID
    run_id: UUID
    sequence: int = Field(ge=1)
    event_type: RunEventType
    occurred_at: AwareDatetime
    payload: dict[str, JsonValue] = Field(default_factory=dict)
