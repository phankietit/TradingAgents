"""Traceable claim-to-source graph for decision evidence."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC
from uuid import UUID

from pydantic import AwareDatetime, Field, model_validator

from .base import ContentHash, NonEmptyText, StrictContract, VersionedContract
from .data import EvidenceReference


def evidence_graph_hash(run_id, as_of, claims, evidence) -> str:
    payload = {
        "run_id": str(run_id),
        "as_of": as_of.astimezone(UTC).isoformat(),
        "claims": [item.model_dump(mode="json") for item in claims],
        "evidence": [item.model_dump(mode="json") for item in evidence],
    }
    return "sha256:" + hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


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
        claim_ids = [claim.claim_id for claim in self.claims]
        if len(claim_ids) != len(set(claim_ids)):
            raise ValueError("duplicate claim ids")
        by_id = {item.evidence_id: item for item in self.evidence}
        linked = set()
        for claim in self.claims:
            if len(claim.evidence_ids) != len(set(claim.evidence_ids)):
                raise ValueError("duplicate claim evidence links")
            missing = set(claim.evidence_ids) - known
            if missing:
                raise ValueError(f"claim references unknown evidence ids: {sorted(map(str, missing))}")
            for evidence_id in claim.evidence_ids:
                if by_id[evidence_id].claim != claim.claim:
                    raise ValueError("evidence claim text does not match linked claim")
            linked.update(claim.evidence_ids)
        if linked != known:
            raise ValueError("unlinked evidence in graph")
        for item in self.evidence:
            if item.source_at is None or item.source_at > self.as_of:
                raise ValueError("evidence source timestamp is missing or future")
            if item.observed_at < item.source_at:
                raise ValueError("evidence observation predates its source")
            if item.observed_at > self.as_of:
                raise ValueError("evidence observation is future at graph as_of")
        if self.content_hash != evidence_graph_hash(self.run_id, self.as_of, self.claims, self.evidence):
            raise ValueError("evidence graph content hash mismatch")
        return self
