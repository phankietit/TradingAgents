"""Versioned HTTP request and response schemas."""

from __future__ import annotations

from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from tradingagents.contracts import JobRecord, RunManifest


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


class RunCreateRequest(ApiModel):
    instrument_id: UUID
    analysis_as_of: AwareDatetime
    selected_analysts: tuple[str, ...] = Field(min_length=1, max_length=4)


class RunAcceptedResponse(ApiModel):
    run: RunManifest
    job: JobRecord


class StatusResponse(ApiModel):
    status: str
