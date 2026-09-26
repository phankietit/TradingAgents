"""Traceable claim-to-source graph for decision evidence."""

from __future__ import annotations

from uuid import UUID

from pydantic import AwareDatetime, Field, model_validator

from .base import ContentHash, NonEmptyText, StrictContract, VersionedContract
from .data import EvidenceReference


class EvidenceClaim(StrictContract):
    claim_id: UUID
    claim: NonEmptyText
    material: bool = True
    evidence_ids: tuple[UUID, ...] = Field(min_length=1)


class EvidenceGraph(VersionedContract):
    graph_id: UUID
    run_id: UUID
    as_of: AwareDatetime
    claims: tuple[EvidenceClaim, ...]
    evidence: tuple[EvidenceReference, ...]
    content_hash: ContentHash

    @model_validator(mode="after")
    def validate_graph_links(self):
        ids = [item.evidence_id for item in self.evidence]
        if len(ids) != len(set(ids)):
            raise ValueError("evidence graph contains duplicate evidence_id values")
        known = set(ids)
        for claim in self.claims:
            missing = set(claim.evidence_ids) - known
            if missing:
                raise ValueError(f"claim references unknown evidence ids: {sorted(map(str, missing))}")
        return self
