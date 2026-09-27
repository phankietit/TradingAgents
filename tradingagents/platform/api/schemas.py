"""Versioned HTTP request and response schemas."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from tradingagents.contracts import (
    ArtifactKind,
    DecisionCandidate,
    DecisionLifecycleEvent,
    DecisionStatus,
    InstrumentAliasContract,
    InstrumentContract,
    JobRecord,
    JobStatus,
    RunManifest,
    SnapshotManifest,
    TimeSeriesView,
)
from tradingagents.contracts.runs import DecisionRunInputs


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LoginRequest(ApiModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=1024)


class OwnerResponse(ApiModel):
    owner_id: UUID
    email: str


class LoginResponse(OwnerResponse):
    expires_at: AwareDatetime


class CsrfResponse(ApiModel):
    csrf_token: str = Field(repr=False)


class AnalysisConfigurationResponse(ApiModel):
    provider: str
    quick_model: str
    deep_model: str
    worker_status: Literal["UNVERIFIED"] = "UNVERIFIED"
    provider_connection: Literal["UNVERIFIED"] = "UNVERIFIED"
    max_job_attempts: int


class RunJobStateResponse(ApiModel):
    job_id: UUID
    run_id: UUID
    status: JobStatus
    attempt: int
    max_attempts: int
    available_at: AwareDatetime
    updated_at: AwareDatetime
    completed_at: AwareDatetime | None


class ArtifactMetadataResponse(ApiModel):
    artifact_id: UUID
    kind: ArtifactKind
    media_type: str
    content_hash: str
    byte_size: int
    created_at: AwareDatetime
    run_id: UUID | None
    instrument_id: UUID | None
    snapshot_id: UUID | None


class InstrumentDetailResponse(ApiModel):
    instrument: InstrumentContract
    aliases: tuple[InstrumentAliasContract, ...]


class AnalysisProfileResponse(ApiModel):
    name: str
    allowed_analysts: tuple[str, ...]
    investable: bool


class TimeSeriesResponse(ApiModel):
    snapshot: SnapshotManifest
    view: TimeSeriesView
    benchmark_snapshot: SnapshotManifest | None = None


class SnapshotDiscoveryResponse(ApiModel):
    snapshot: SnapshotManifest
    metadata_eligible: bool
    ineligibility_reasons: tuple[str, ...]
    supported_analysts: tuple[str, ...]
    content_validation: Literal["required_on_run_creation"] = "required_on_run_creation"


class RunCreateRequest(ApiModel):
    instrument_id: UUID
    analysis_as_of: AwareDatetime
    selected_analysts: tuple[str, ...] = Field(min_length=1, max_length=4)
    decision_inputs: DecisionRunInputs | None = None
    report_language: Literal["en", "vi", "en-vi"] | None = None

    @model_validator(mode="after")
    def validate_snapshot_roles(self):
        if self.decision_inputs and set(self.decision_inputs.snapshots_by_analyst) != set(self.selected_analysts):
            raise ValueError("snapshot roles must match selected analysts")
        return self


class RunAcceptedResponse(ApiModel):
    run: RunManifest
    job: JobRecord


class StatusResponse(ApiModel):
    status: str


class DecisionTransitionRequest(ApiModel):
    event_id: UUID
    expected_status: DecisionStatus
    action: Literal["approve", "reject", "review", "expire"]
    reason: str = Field(min_length=1, max_length=2000)
    policy_id: UUID | None = None
    policy_version: str | None = Field(default=None, min_length=1, max_length=64)


class DecisionStateResponse(ApiModel):
    candidate: DecisionCandidate
    current_status: DecisionStatus
    events: tuple[DecisionLifecycleEvent, ...]
