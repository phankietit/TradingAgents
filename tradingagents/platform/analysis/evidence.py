"""Deterministic evidence-graph construction with point-in-time checks."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from datetime import datetime
from uuid import UUID, uuid4

from tradingagents.contracts import (
    DataQualityStatus,
    EvidenceClaim,
    EvidenceGraph,
    EvidenceReference,
    SnapshotManifest,
)


class EvidenceGraphBuilder:
    def build(
        self,
        *,
        run_id: UUID,
        as_of: datetime,
        snapshots: Sequence[SnapshotManifest],
        material_claims: Mapping[str, Sequence[UUID]],
        graph_id: UUID | None = None,
    ) -> EvidenceGraph:
        by_snapshot = {snapshot.snapshot_id: snapshot for snapshot in snapshots}
        evidence: list[EvidenceReference] = []
        claims: list[EvidenceClaim] = []

        for claim_text, snapshot_ids in material_claims.items():
            if not snapshot_ids:
                raise ValueError("every material claim requires at least one source snapshot")
            linked_ids: list[UUID] = []
            for snapshot_id in snapshot_ids:
                snapshot = by_snapshot.get(snapshot_id)
                if snapshot is None:
                    raise ValueError(f"claim references unknown snapshot {snapshot_id}")
                if snapshot.quality_status is not DataQualityStatus.OK:
                    raise ValueError("material claims require OK source data")
                source_at = snapshot.source_end or snapshot.as_of
                if source_at > as_of:
                    raise ValueError("material claim source is not point-in-time eligible")
                reference = EvidenceReference(
                    evidence_id=uuid4(),
                    snapshot_id=snapshot.snapshot_id,
                    claim=claim_text,
                    source_name=snapshot.vendor,
                    observed_at=snapshot.retrieved_at,
                    source_at=source_at,
                    content_hash=snapshot.content_hash,
                )
                evidence.append(reference)
                linked_ids.append(reference.evidence_id)
            claims.append(
                EvidenceClaim(claim_id=uuid4(), claim=claim_text, evidence_ids=tuple(linked_ids))
            )

        canonical = {
            "run_id": str(run_id),
            "as_of": as_of.isoformat(),
            "claims": [claim.model_dump(mode="json") for claim in claims],
            "evidence": [item.model_dump(mode="json") for item in evidence],
        }
        digest = hashlib.sha256(
            json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        return EvidenceGraph(
            graph_id=graph_id or uuid4(),
            run_id=run_id,
            as_of=as_of,
            claims=tuple(claims),
            evidence=tuple(evidence),
            content_hash=f"sha256:{digest}",
        )
