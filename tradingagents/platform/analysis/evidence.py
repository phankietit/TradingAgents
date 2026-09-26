"""Deterministic evidence-graph construction with point-in-time checks."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from uuid import UUID, uuid5

from tradingagents.contracts import (
    DataQualityStatus,
    EvidenceClaim,
    EvidenceGraph,
    EvidenceReference,
    SnapshotManifest,
)
from tradingagents.contracts.evidence import evidence_graph_hash


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
        if as_of.tzinfo is None or as_of.utcoffset() is None:
            raise ValueError("evidence as_of requires a timezone")
        as_of = as_of.astimezone(UTC)
        by_snapshot = {snapshot.snapshot_id: snapshot for snapshot in snapshots}
        if len(by_snapshot) != len(snapshots):
            raise ValueError("duplicate snapshot ids")
        evidence: list[EvidenceReference] = []
        claims: list[EvidenceClaim] = []

        for claim_text, snapshot_ids in sorted(material_claims.items()):
            if not claim_text.strip() or claim_text != claim_text.strip():
                raise ValueError("claim text must be nonempty and trimmed")
            if not snapshot_ids:
                raise ValueError("every material claim requires at least one source snapshot")
            linked_ids: list[UUID] = []
            if len(snapshot_ids) != len(set(snapshot_ids)):
                raise ValueError("duplicate snapshot links")
            for snapshot_id in sorted(snapshot_ids, key=str):
                snapshot = by_snapshot.get(snapshot_id)
                if snapshot is None:
                    raise ValueError(f"claim references unknown snapshot {snapshot_id}")
                if snapshot.quality_status is not DataQualityStatus.OK:
                    raise ValueError("material claims require OK source data")
                source_at = snapshot.source_end
                if (source_at is None or source_at > as_of or snapshot.as_of > as_of
                        or snapshot.retrieved_at > as_of):
                    raise ValueError("material claim source is not point-in-time eligible")
                reference = EvidenceReference(
                    evidence_id=uuid5(run_id, f"evidence:{claim_text}:{snapshot_id}:{snapshot.content_hash}"),
                    snapshot_id=snapshot.snapshot_id,
                    claim=claim_text,
                    source_name=snapshot.vendor,
                    observed_at=snapshot.retrieved_at.astimezone(UTC),
                    source_at=source_at.astimezone(UTC),
                    content_hash=snapshot.content_hash,
                )
                evidence.append(reference)
                linked_ids.append(reference.evidence_id)
            claims.append(
                EvidenceClaim(claim_id=uuid5(run_id, f"claim:{claim_text}"), claim=claim_text, evidence_ids=tuple(linked_ids))
            )

        digest = evidence_graph_hash(run_id, as_of, claims, evidence)
        return EvidenceGraph(
            graph_id=graph_id or uuid5(run_id, digest),
            run_id=run_id,
            as_of=as_of,
            claims=tuple(claims),
            evidence=tuple(evidence),
            content_hash=digest,
        )
