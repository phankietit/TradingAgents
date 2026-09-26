"""Immutable artifact manifests for durable platform evidence."""

from __future__ import annotations

from enum import Enum
from uuid import UUID

from pydantic import AwareDatetime, Field, model_validator

from .base import ContentHash, NonEmptyText, VersionedContract


class ArtifactKind(str, Enum):
    SNAPSHOT_PAYLOAD = "snapshot_payload"
    SCREENING_SNAPSHOT = "screening_snapshot"
    DERIVED_FACTOR_SNAPSHOT = "derived_factor_snapshot"
    DATA_HEALTH_REPORT = "data_health_report"
    ANALYSIS_REPORT = "analysis_report"
    RUN_EVENT_LOG = "run_event_log"
    DECISION_EVIDENCE = "decision_evidence"


class ArtifactManifest(VersionedContract):
    artifact_id: UUID
    owner_id: UUID
    kind: ArtifactKind
    media_type: NonEmptyText
    content_hash: ContentHash
    byte_size: int = Field(ge=0)
    storage_key: NonEmptyText
    created_at: AwareDatetime
    run_id: UUID | None = None
    instrument_id: UUID | None = None
    snapshot_id: UUID | None = None

    @model_validator(mode="after")
    def require_context_for_snapshot_payload(self):
        if self.kind is ArtifactKind.SNAPSHOT_PAYLOAD and not self.snapshot_id:
            raise ValueError("snapshot payload artifacts require snapshot_id")
        digest = self.content_hash.removeprefix("sha256:")
        expected_key = f"sha256/{digest[:2]}/{digest[2:4]}/{digest}"
        if self.storage_key != expected_key:
            raise ValueError("storage_key must be derived from content_hash")
        return self
