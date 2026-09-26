from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from tradingagents.contracts import DataQualityStatus, SnapshotManifest
from tradingagents.platform.analysis import EvidenceGraphBuilder

NOW = datetime(2026, 9, 25, tzinfo=UTC)


def _snapshot(**overrides):
    values = {
        "snapshot_id": uuid4(),
        "instrument_id": uuid4(),
        "dataset": "ohlcv.daily",
        "vendor": "approved-vendor",
        "as_of": NOW,
        "retrieved_at": NOW + timedelta(minutes=1),
        "source_end": NOW,
        "content_hash": "sha256:" + "a" * 64,
        "quality_status": DataQualityStatus.OK,
    }
    values.update(overrides)
    return SnapshotManifest(**values)


@pytest.mark.unit
def test_material_claim_links_to_source_time_and_hash():
    snapshot = _snapshot()
    graph = EvidenceGraphBuilder().build(
        run_id=uuid4(),
        as_of=NOW,
        snapshots=(snapshot,),
        material_claims={"Relative strength is positive": (snapshot.snapshot_id,)},
    )
    reference = graph.evidence[0]
    assert reference.snapshot_id == snapshot.snapshot_id
    assert reference.source_at == NOW
    assert reference.content_hash == snapshot.content_hash
    assert graph.claims[0].evidence_ids == (reference.evidence_id,)
    assert graph.content_hash.startswith("sha256:")


@pytest.mark.unit
def test_material_claim_without_source_fails_closed():
    with pytest.raises(ValueError, match="at least one source"):
        EvidenceGraphBuilder().build(
            run_id=uuid4(), as_of=NOW, snapshots=(), material_claims={"Claim": ()}
        )


@pytest.mark.unit
def test_non_ok_snapshot_cannot_support_material_claim():
    snapshot = _snapshot(quality_status=DataQualityStatus.STALE)
    with pytest.raises(ValueError, match="require OK"):
        EvidenceGraphBuilder().build(
            run_id=uuid4(),
            as_of=NOW,
            snapshots=(snapshot,),
            material_claims={"Claim": (snapshot.snapshot_id,)},
        )
