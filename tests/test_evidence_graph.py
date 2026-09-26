from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from tradingagents.contracts import DataQualityStatus, EvidenceGraph, SnapshotManifest
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


def test_graph_hash_and_ids_are_reproducible_under_input_permutation():
    first, second = _snapshot(), _snapshot()
    run_id = uuid4()
    builder = EvidenceGraphBuilder()
    graph = builder.build(run_id=run_id, as_of=NOW, snapshots=(first, second),
                          material_claims={"B": (first.snapshot_id, second.snapshot_id), "A": (second.snapshot_id,)})
    repeat = builder.build(run_id=run_id, as_of=NOW, snapshots=(second, first),
                           material_claims={"A": (second.snapshot_id,), "B": (second.snapshot_id, first.snapshot_id)})
    assert repeat == graph
    payload = graph.model_dump(mode="json")
    payload["content_hash"] = "sha256:" + "0" * 64
    with pytest.raises(ValueError, match="content hash mismatch"):
        EvidenceGraph.model_validate(payload)


@pytest.mark.parametrize("changes", [
    {"source_end": None},
    {"as_of": NOW + timedelta(days=1), "source_end": NOW + timedelta(days=1)},
    {"retrieved_at": NOW - timedelta(days=1)},
])
def test_unproven_time_eligibility_fails_closed(changes):
    snapshot = _snapshot(**changes)
    with pytest.raises(ValueError):
        EvidenceGraphBuilder().build(run_id=uuid4(), as_of=NOW, snapshots=(snapshot,),
                                     material_claims={"Claim": (snapshot.snapshot_id,)})


def test_duplicate_sources_are_not_silently_overwritten():
    snapshot = _snapshot()
    with pytest.raises(ValueError, match="duplicate snapshot ids"):
        EvidenceGraphBuilder().build(run_id=uuid4(), as_of=NOW, snapshots=(snapshot, snapshot),
                                     material_claims={"Claim": (snapshot.snapshot_id,)})


def test_run_bound_evidence_persistence_and_owner_isolation(tmp_path):
    from tests.test_platform_persistence import _instrument, _run
    from tradingagents.platform.analysis.evidence_service import EvidenceGraphService
    from tradingagents.platform.artifacts import ArtifactService, LocalArtifactStore
    from tradingagents.platform.persistence import Database, PlatformRepository, upgrade_database

    url = f"sqlite:///{tmp_path / 'evidence.db'}"
    upgrade_database(url)
    database = Database(url)
    owner, instrument = uuid4(), _instrument()
    run = _run(instrument.instrument_id, owner)
    snapshot = _snapshot(instrument_id=instrument.instrument_id,
                         as_of=run.analysis_as_of, source_end=run.analysis_as_of)
    run = run.model_copy(update={"snapshot_ids": (snapshot.snapshot_id,)})
    store = LocalArtifactStore(tmp_path / "artifacts")
    with database.session() as session:
        repository = PlatformRepository(session)
        repository.add_instrument(instrument)
        repository.add_snapshot(snapshot)
        repository.save_run(run)
        service = EvidenceGraphService(ArtifactService(store, repository))
        manifest = service.create(owner_id=owner, run_id=run.run_id, material_claims={"Claim": (snapshot.snapshot_id,)})
        assert service.create(owner_id=owner, run_id=run.run_id, material_claims={"Claim": (snapshot.snapshot_id,)}) == manifest
    with database.session() as session:
        service = EvidenceGraphService(ArtifactService(store, PlatformRepository(session)))
        assert service.read(manifest.artifact_id, owner).run_id == run.run_id
        assert service.read(manifest.artifact_id, uuid4()) is None
        with pytest.raises(ValueError, match="run not found"):
            service.create(owner_id=uuid4(), run_id=run.run_id, material_claims={})
        with pytest.raises(ValueError, match="not bound"):
            service.create(owner_id=owner, run_id=run.run_id, material_claims={"Claim": (uuid4(),)})
    database.dispose()
