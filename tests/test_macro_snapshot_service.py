"""Macro snapshots preserve provenance/owner/cutoff, never backdate retrieval."""

import os
from copy import deepcopy
from datetime import timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest

from tests.test_platform_fred import NOW, collect, documents
from tests.test_price_preparation import AAPL
from tradingagents.contracts import DataQualityStatus
from tradingagents.platform.analysis.snapshots import (
    load_snapshot_context,
    supported_snapshot_analysts,
)
from tradingagents.platform.artifacts import (
    ArtifactIntegrityError,
    ArtifactService,
    LocalArtifactStore,
)
from tradingagents.platform.auth import OwnerAuth
from tradingagents.platform.market_data.macro import MacroSnapshotService
from tradingagents.platform.persistence import (
    Database,
    PlatformRepository,
    downgrade_database,
    upgrade_database,
)
from tradingagents.platform.persistence.models import SnapshotRow


@pytest.fixture(params=["sqlite", "postgres"])
def storage(tmp_path, request):
    url = f"sqlite:///{tmp_path / 'macro.db'}"
    if request.param == "postgres":
        url = os.environ.get("TEST_POSTGRES_URL")
        if not url or os.environ.get("TA_ALLOW_TEST_DB_RESET") != "1":
            pytest.skip("Explicitly acknowledged disposable PostgreSQL gate required")
    upgrade_database(url)
    database = Database(url)
    store = LocalArtifactStore(tmp_path / "artifacts")
    with database.session() as session:
        owner = OwnerAuth(session).bootstrap_owner("macro-fixture@example.com", "synthetic-qa-password").owner_id
        PlatformRepository(session).add_instrument(AAPL)
    try:
        yield database, store, owner
    finally:
        database.dispose()
        if request.param == "postgres":
            downgrade_database(url)


def service(session, store):
    repository = PlatformRepository(session)
    return MacroSnapshotService(repository, ArtifactService(store, repository))


def test_immutable_roundtrip_owner_and_temporal_identity(storage):
    database, store, owner = storage
    collection = collect()
    with database.session() as session:
        writer = service(session, store)
        manifest = writer.persist(owner_id=owner, collection=collection)
        assert writer.persist(owner_id=owner, collection=collection, snapshot_id=manifest.snapshot_id) == manifest
    assert manifest.as_of == collection.retrieved_at
    assert supported_snapshot_analysts(manifest.dataset) == ("news",)  # Explicit semantic map; full payload admission is separate.
    assert manifest.source_end == collection.vintage_available_at
    assert manifest.metadata["last_observation_date"] == "2026-10-02"
    assert manifest.metadata["availability"] == "complete_chicago_vintage_day_not_exact_release_time"
    with database.session() as session:
        reader = service(session, store)
        args = {"owner_id": owner, "snapshot_id": manifest.snapshot_id, "instrument_id": AAPL.instrument_id,
            "as_of": NOW, "max_age_seconds": 86400}
        assert reader.load(**args) == (manifest, collection)
        with pytest.raises(LookupError, match="owner"):
            reader.load(**{**args, "owner_id": uuid4()})
        with pytest.raises(ValueError, match="not eligible"):
            reader.load(**{**args, "instrument_id": uuid4()})
        with pytest.raises(ValueError, match="not eligible"):
            reader.load(**{**args, "as_of": NOW - timedelta(seconds=1)})
        with pytest.raises(ValueError, match="not eligible"):
            reader.load(**{**args, "as_of": NOW + timedelta(days=2)})


@pytest.mark.parametrize("case", ["empty", "missing", "stale", "invalid"])
def test_failure_snapshot_auditable_but_never_eligible(storage, case):
    database, store, owner = storage
    raw = documents()
    envelope = raw["series/observations"]
    if case == "empty":
        envelope.update(observations=[], count=0)
    elif case == "missing":
        envelope["observations"][0]["value"] = "."
    elif case == "stale":
        envelope["observations"][0]["date"] = "2026-01-01"
    else:
        envelope["observations"][0]["value"] = "NaN"
    collection = collect(raw)
    assert collection.quality_status is not DataQualityStatus.OK
    with database.session() as session:
        manifest = service(session, store).persist(owner_id=owner, collection=collection)
        assert manifest.quality_reasons == (collection.reason,)
    with database.session() as session, pytest.raises(ValueError, match="not eligible"):
        service(session, store).load(owner_id=owner, snapshot_id=manifest.snapshot_id,
            instrument_id=AAPL.instrument_id, as_of=NOW, max_age_seconds=86400)


@pytest.mark.parametrize("field", ["vintage_date", "observations", "units", "coverage", "availability"])
def test_complete_manifest_metadata_parity_is_required(storage, field):
    database, store, owner = storage
    with database.session() as session:
        manifest = service(session, store).persist(owner_id=owner, collection=collect())
    with database.session() as session:
        row = session.get(SnapshotRow, manifest.snapshot_id)
        payload = deepcopy(row.payload)
        payload["metadata"][field] = "synthetic tamper"
        row.payload = payload
    with database.session() as session, pytest.raises(ValueError, match="does not match"):
        service(session, store).load(owner_id=owner, snapshot_id=manifest.snapshot_id,
            instrument_id=AAPL.instrument_id, as_of=NOW, max_age_seconds=86400)


@pytest.mark.parametrize("field,value", [
    ("canonical_symbol", "OTHER"), ("asset_class", "crypto"), ("venue", "OTHER"),
    ("quote_currency", "EUR"), ("timezone", "UTC"),
    ("quality_status", DataQualityStatus.NO_DATA),
])
def test_collection_copy_cannot_bypass_identity_or_status(storage, field, value):
    database, store, owner = storage
    with database.session() as session, pytest.raises(ValueError):
        service(session, store).persist(owner_id=owner, collection=collect().model_copy(update={field: value}))


def test_corrupted_blob_is_never_loaded(storage):
    database, store, owner = storage
    with database.session() as session:
        writer = service(session, store)
        manifest = writer.persist(owner_id=owner, collection=collect())
        artifact = writer.repository.get_snapshot_artifact(manifest.snapshot_id, owner)
        (store.root / artifact.storage_key).write_bytes(b"synthetic corrupted macro fixture")
    with database.session() as session, pytest.raises(ArtifactIntegrityError):
        service(session, store).load(owner_id=owner, snapshot_id=manifest.snapshot_id,
            instrument_id=AAPL.instrument_id, as_of=NOW, max_age_seconds=86400)


def test_artifact_failure_rolls_back_snapshot(storage, monkeypatch):
    database, store, owner = storage
    snapshot_id = uuid4()

    def fail(*_, **kwargs):
        raise OSError("synthetic macro storage failure")

    monkeypatch.setattr(ArtifactService, "create", fail)
    with pytest.raises(OSError, match="synthetic macro storage failure"), database.session() as session:
        service(session, store).persist(owner_id=owner, collection=collect(), snapshot_id=snapshot_id)
    with database.session() as session:
        assert PlatformRepository(session).get_snapshot(snapshot_id) is None


def test_owner_context_loader_rechecks_macro_service_before_graph_admission(storage):
    database, store, owner = storage
    with database.session() as session:
        writer = service(session, store)
        manifest = writer.persist(owner_id=owner, collection=collect())
    run = SimpleNamespace(owner_id=owner, instrument_id=AAPL.instrument_id,
        snapshot_ids=(manifest.snapshot_id,), analysis_as_of=NOW, selected_analysts=("news",),
        decision_inputs=SimpleNamespace(source_max_age_seconds={"news": 86400}))
    with database.session() as session:
        reader = service(session, store)
        context = load_snapshot_context(reader.artifacts, run, {"news": (manifest.snapshot_id,)})
        assert context.by_analyst["news"][0].manifest == manifest
        run.owner_id = uuid4()
        with pytest.raises(ValueError, match="owner"):
            load_snapshot_context(reader.artifacts, run, {"news": (manifest.snapshot_id,)})
