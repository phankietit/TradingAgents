"""Deterministic data-health probes, checks, and aggregate reports."""

from __future__ import annotations

from uuid import UUID

from pydantic import AwareDatetime, Field, FiniteFloat, model_validator

from .base import ContentHash, NonEmptyText, StrictContract, VersionedContract
from .data import DataQualityStatus


class DataHealthProbe(StrictContract):
    dataset: NonEmptyText
    vendor: NonEmptyText
    instrument_id: UUID | None = None
    as_of: AwareDatetime
    checked_at: AwareDatetime
    source_available: bool
    coverage_supported: bool
    schema_valid: bool
    identity_valid: bool
    eligible_records: int = Field(ge=0)
    excluded_future_records: int = Field(default=0, ge=0)
    latest_eligible_source_at: AwareDatetime | None = None
    freshness_limit_seconds: int = Field(ge=1, le=31_536_000)
    diagnostics: tuple[NonEmptyText, ...] = ()

    @model_validator(mode="after")
    def validate_check_time(self):
        if self.checked_at < self.as_of:
            raise ValueError("checked_at must not precede as_of")
        return self


class DataHealthCheck(StrictContract):
    dataset: NonEmptyText
    vendor: NonEmptyText
    instrument_id: UUID | None = None
    status: DataQualityStatus
    reason: NonEmptyText
    eligible_records: int = Field(ge=0)
    excluded_future_records: int = Field(ge=0)
    latest_eligible_source_at: AwareDatetime | None = None
    age_seconds: FiniteFloat | None = Field(default=None, ge=0)
    diagnostics: tuple[NonEmptyText, ...] = ()


class DataHealthSummary(StrictContract):
    ok: int = Field(ge=0)
    stale: int = Field(ge=0)
    no_data: int = Field(ge=0)
    unavailable: int = Field(ge=0)
    coverage_gap: int = Field(ge=0)
    invalid: int = Field(ge=0)

    @property
    def total(self) -> int:
        return (
            self.ok
            + self.stale
            + self.no_data
            + self.unavailable
            + self.coverage_gap
            + self.invalid
        )


class DataHealthReport(VersionedContract):
    report_id: UUID
    as_of: AwareDatetime
    evaluated_at: AwareDatetime
    report_hash: ContentHash
    overall_status: DataQualityStatus
    summary: DataHealthSummary
    checks: tuple[DataHealthCheck, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_report(self):
        if self.evaluated_at < self.as_of:
            raise ValueError("evaluated_at must not precede as_of")
        if self.summary.total != len(self.checks):
            raise ValueError("data health summary must cover every check")
        keys = [
            (
                str(item.instrument_id) if item.instrument_id is not None else "",
                item.dataset.casefold(),
                item.vendor.casefold(),
            )
            for item in self.checks
        ]
        if keys != sorted(keys) or len(keys) != len(set(keys)):
            raise ValueError("data health checks must have sorted unique identities")
        return self
