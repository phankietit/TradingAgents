"""Owner/integrity/PIT/full source admission on real SQLite and disposable PG."""

from datetime import timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest

from tests import test_macro_snapshot_service as _storage_fixture
from tests.test_platform_social import AAPL, NOW, atom, collect, envelope
from tradingagents.contracts import DataQualityStatus
from tradingagents.platform.analysis.snapshots import load_snapshot_context
from tradingagents.platform.analysis.social_facts import SnapshotSocialFacts
from tradingagents.platform.artifacts import ArtifactService
from tradingagents.platform.jobs.analysis import publication_warning
from tradingagents.platform.market_data.social import SocialSnapshotService, _manifest
from tradingagents.platform.persistence import PlatformRepository
from tradingagents.platform.persistence.models import SnapshotRow

storage = _storage_fixture.storage


def service(session, store):
    repository = PlatformRepository(session)
    return SocialSnapshotService(repository, ArtifactService(store, repository))


@pytest.mark.parametrize("vendor", ["reddit", "stocktwits"])
def test_owner_storage_exact_parity_cutoff_reuse_and_full_analyst_context(storage, vendor):
    database, store, owner = storage
    collection = collect(vendor=vendor)
    with database.session() as session:
        writer = service(session, store)
        manifest = writer.persist(owner_id=owner, collection=collection)
        assert writer.persist(owner_id=owner, collection=collection, snapshot_id=manifest.snapshot_id) == manifest
    args = {"owner_id": owner, "snapshot_id": manifest.snapshot_id, "instrument_id": AAPL.instrument_id,
            "as_of": NOW, "max_age_seconds": 604800}
    assert manifest.as_of == collection.retrieved_at
    with database.session() as session:
        assert service(session, store).load(**args) == (manifest, collection)
        with pytest.raises(LookupError):
            service(session, store).load(**{**args, "owner_id": uuid4()})
        for update in ({"as_of": NOW-timedelta(microseconds=1)}, {"instrument_id": uuid4()},
                       {"as_of": NOW+timedelta(days=8)}):
            with pytest.raises(ValueError):
                service(session, store).load(**{**args, **update})
        run = SimpleNamespace(owner_id=owner, instrument_id=AAPL.instrument_id,
            snapshot_ids=(manifest.snapshot_id,), analysis_as_of=NOW, selected_analysts=("social",),
            decision_inputs=SimpleNamespace(source_max_age_seconds={"social": 604800}))
        context = load_snapshot_context(ArtifactService(store, PlatformRepository(session)), run,
            {"social": (manifest.snapshot_id,)})
        assert collection.posts[0].body in context.reports(AAPL.instrument_id, ("social",))["social"]
        assert "SOCIAL COVERAGE" in publication_warning(context)
    reader = SnapshotSocialFacts({"snapshot_id": str(manifest.snapshot_id),
        "provenance": manifest.model_dump(mode="json"), "data": collection.model_dump(mode="json")})
    reader.require_instrument(AAPL)
    assert reader.summary()["posts"] == [post.model_dump(mode="json") for post in collection.posts]
    assert reader.resolve_fact(f"social.{vendor}.sample_count.posts") == len(collection.posts)
    if vendor == "reddit":
        assert reader.resolve_fact("social.reddit.sample_count.bullish") is None
    else:
        assert reader.resolve_fact("social.stocktwits.sample_count.bullish") == 1
        assert reader.resolve_fact("social.stocktwits.sample_count.unlabeled") == 1


@pytest.mark.parametrize("field", ["posts", "coverage", "provider_symbol", "communities", "requested_at"])
def test_metadata_mutation_cannot_rebind_eligible_bytes(storage, field):
    database, store, owner = storage
    with database.session() as session:
        manifest = service(session, store).persist(owner_id=owner, collection=collect())
    with database.session() as session:
        row = session.get(SnapshotRow, manifest.snapshot_id)
        row.payload = {**row.payload, "metadata": {**row.payload["metadata"], field: "tampered"}}
    with database.session() as session, pytest.raises(ValueError, match="does not match"):
        service(session, store).load(owner_id=owner, snapshot_id=manifest.snapshot_id,
            instrument_id=AAPL.instrument_id, as_of=NOW, max_age_seconds=604800)


@pytest.mark.parametrize("raw", [envelope([]), envelope([{ "id": 1 }]), atom(updated="2030-01-01T00:00:00Z")])
def test_failed_sources_are_auditable_never_eligible(storage, raw):
    database, store, owner = storage
    collection = collect(raw, vendor="reddit" if raw.startswith(b"<") else "stocktwits")
    assert collection.quality_status is not DataQualityStatus.OK
    with database.session() as session:
        manifest = service(session, store).persist(owner_id=owner, collection=collection)
    with database.session() as session, pytest.raises(ValueError, match="not eligible"):
        service(session, store).load(owner_id=owner, snapshot_id=manifest.snapshot_id,
            instrument_id=AAPL.instrument_id, as_of=NOW, max_age_seconds=604800)


def test_full_fact_reader_identity_and_counterfeit_provenance_refuse():
    collection = collect()
    manifest = _manifest(collection, uuid4())
    source = {"snapshot_id": str(manifest.snapshot_id), "provenance": manifest.model_dump(mode="json"),
              "data": collection.model_dump(mode="json")}
    source["provenance"]["metadata"]["posts"] = 100
    with pytest.raises(ValueError):
        SnapshotSocialFacts(source)
    source["provenance"] = manifest.model_dump(mode="json")
    reader = SnapshotSocialFacts(source)
    with pytest.raises(ValueError):
        reader.require_instrument(AAPL.model_copy(update={"venue": "wrong"}))


def test_invalid_copy_and_artifact_write_failure_leave_no_metadata(storage, monkeypatch):
    database, store, owner = storage
    with pytest.raises(OSError), database.session() as session:
        writer = service(session, store)
        monkeypatch.setattr(writer.artifacts, "create", lambda **kwargs: (_ for _ in ()).throw(OSError("fixed failure")))
        writer.persist(owner_id=owner, collection=collect())
    with database.session() as session:
        assert PlatformRepository(session).list_owner_snapshots(AAPL.instrument_id, owner) == ()
