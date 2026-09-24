"""Immutable snapshot provenance and evidence contracts."""

from __future__ import annotations

from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import AwareDatetime, Field, HttpUrl, model_validator

from .base import ContentHash, NonEmptyText, StrictContract, VersionedContract


class DataQualityStatus(str, Enum):
    OK = "OK"
    NO_DATA = "NO_DATA"
    STALE = "STALE"
    UNAVAILABLE = "UNAVAILABLE"
    COVERAGE_GAP = "COVERAGE_GAP"
    INVALID = "INVALID"


class SnapshotManifest(VersionedContract):
    snapshot_id: UUID
    instrument_id: UUID
    dataset: NonEmptyText
    vendor: NonEmptyText
    as_of: AwareDatetime
    retrieved_at: AwareDatetime
    source_start: AwareDatetime | None = None
    source_end: AwareDatetime | None = None
    content_hash: ContentHash
    quality_status: DataQualityStatus
    quality_reasons: tuple[str, ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_time_window(self):
        if self.source_start and self.source_end and self.source_start > self.source_end:
            raise ValueError("source_start must not be after source_end")
        if self.source_end and self.source_end > self.as_of:
            raise ValueError("snapshot source_end must not exceed as_of")
        return self


class EvidenceReference(StrictContract):
    evidence_id: UUID
    snapshot_id: UUID
    claim: NonEmptyText
    source_name: NonEmptyText
    source_url: HttpUrl | None = None
    observed_at: AwareDatetime
    source_at: AwareDatetime | None = None
    content_hash: ContentHash
