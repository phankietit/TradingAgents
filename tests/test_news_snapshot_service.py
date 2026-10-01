"""News evidence is immutable, owner-scoped and available only after retrieval."""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from tradingagents._compat import UTC
from tradingagents.contracts import DataQualityStatus
from tradingagents.dataflows.platform_news import collect_yahoo_news
from tradingagents.platform.artifacts import (
    ArtifactIntegrityError,
    ArtifactService,
    LocalArtifactStore,
)
from tradingagents.platform.instruments import INITIAL_INSTRUMENT_CATALOG
from tradingagents.platform.market_data.news import NewsSnapshotService
from tradingagents.platform.persistence import Database, PlatformRepository, upgrade_database
from tradingagents.platform.persistence.models import SnapshotRow

NOW = datetime(2026, 9, 27, 12, tzinfo=UTC)
INSTRUMENT = next(
    item.instrument for item in INITIAL_INSTRUMENT_CATALOG
    if item.instrument.canonical_symbol == "AAPL"
)


def _collection(raw):
    ticks = iter((NOW, NOW + timedelta(seconds=2)))
    return collect_yahoo_news(
        INSTRUMENT, clock=lambda: next(ticks), fetch=lambda *_: raw,
    )


def _article():
    return {"content": {
        "title": "Research update", "summary": "Untrusted source text",
        "provider": {"displayName": "Fixture publisher"},
        "canonicalUrl": {"url": "https://example.com/news"},
        "pubDate": (NOW - timedelta(hours=2)).isoformat(),
    }}


@pytest.fixture
def storage(tmp_path):
    url = f"sqlite:///{tmp_path / 'news.db'}"
    upgrade_database(url)
    database = Database(url)
    store = LocalArtifactStore(tmp_path / "artifacts")
    with database.session() as session:
        PlatformRepository(session).add_instrument(INSTRUMENT)
    yield database, store
    database.dispose()


def _service(session, store):
    repo = PlatformRepository(session)
    return NewsSnapshotService(repo, ArtifactService(store, repo))


def test_news_round_trip_retry_and_owner_isolation(storage):
    database, store = storage
    owner = uuid4()
    collection = _collection([_article()])
    with database.session() as session:
        service = _service(session, store)
        manifest = service.persist(owner_id=owner, collection=collection)
        assert service.persist(
            owner_id=owner, collection=collection, snapshot_id=manifest.snapshot_id,
        ) == manifest
        assert manifest.source_end == collection.articles[0].published_at
        assert manifest.as_of == collection.retrieved_at
        assert manifest.metadata["coverage"] == "recent_feed_not_exhaustive"
    with database.session() as session:
        service = _service(session, store)
        assert service.load(
            owner_id=owner, snapshot_id=manifest.snapshot_id,
            instrument_id=INSTRUMENT.instrument_id,
            as_of=collection.retrieved_at, max_age_seconds=86400,
        ) == (manifest, collection)
        with pytest.raises(LookupError, match="owner"):
            service.load(
                owner_id=uuid4(), snapshot_id=manifest.snapshot_id,
                instrument_id=INSTRUMENT.instrument_id,
                as_of=collection.retrieved_at, max_age_seconds=86400,
            )
        with pytest.raises(ValueError, match="cutoff"):
            service.load(
                owner_id=owner, snapshot_id=manifest.snapshot_id,
                instrument_id=INSTRUMENT.instrument_id,
                as_of=NOW, max_age_seconds=86400,
            )
        with pytest.raises(ValueError, match="cutoff"):
            service.load(
                owner_id=owner, snapshot_id=manifest.snapshot_id,
                instrument_id=INSTRUMENT.instrument_id,
                as_of=NOW + timedelta(days=2), max_age_seconds=86400,
            )


@pytest.mark.parametrize("raw,status", [
    ([], DataQualityStatus.NO_DATA),
    ([{}], DataQualityStatus.INVALID),
])
def test_failed_feed_remains_auditable_but_cannot_be_analysis_evidence(storage, raw, status):
    database, store = storage
    owner = uuid4()
    collection = _collection(raw)
    assert collection.quality_status is status
    with database.session() as session:
        manifest = _service(session, store).persist(owner_id=owner, collection=collection)
        assert manifest.source_end is None
    with database.session() as session, pytest.raises(ValueError, match="not eligible"):
        _service(session, store).load(
            owner_id=owner, snapshot_id=manifest.snapshot_id,
            instrument_id=INSTRUMENT.instrument_id,
            as_of=collection.retrieved_at, max_age_seconds=86400,
        )


def test_identity_and_manifest_tampering_fail_closed(storage, monkeypatch):
    database, store = storage
    owner = uuid4()
    collection = _collection([_article()])
    with database.session() as session:
        service = _service(session, store)
        with pytest.raises(ValueError, match="identity"):
            service.persist(
                owner_id=owner, collection=collection.model_copy(update={"venue": "NYSE"}),
            )
        manifest = service.persist(owner_id=owner, collection=collection)
    with database.session() as session:
        service = _service(session, store)
        monkeypatch.setattr(
            service.repository, "get_snapshot",
            lambda _: manifest.model_copy(update={"quality_reasons": ("forged",)}),
        )
        with pytest.raises(ValueError, match="payload does not match"):
            service.load(
                owner_id=owner, snapshot_id=manifest.snapshot_id,
                instrument_id=INSTRUMENT.instrument_id,
                as_of=collection.retrieved_at, max_age_seconds=86400,
            )


def test_corrupted_blob_is_not_loaded(storage):
    database, store = storage
    owner = uuid4()
    collection = _collection([_article()])
    with database.session() as session:
        manifest = _service(session, store).persist(owner_id=owner, collection=collection)
    with database.session() as session:
        service = _service(session, store)
        artifact = service.repository.get_snapshot_artifact(manifest.snapshot_id, owner)
        assert artifact is not None
        path = store.root / artifact.storage_key
        path.write_bytes(b"corrupted fixture blob")
        with pytest.raises(ArtifactIntegrityError):
            service.load(
                owner_id=owner, snapshot_id=manifest.snapshot_id,
                instrument_id=INSTRUMENT.instrument_id,
                as_of=collection.retrieved_at, max_age_seconds=86400,
            )


def test_failed_artifact_write_rolls_back_snapshot_manifest(storage, monkeypatch):
    database, store = storage
    owner = uuid4()
    collection = _collection([_article()])
    snapshot_id = uuid4()
    def fail(*args, **kwargs):
        raise OSError("fixture storage failure")
    monkeypatch.setattr(ArtifactService, "create", fail)
    with pytest.raises(OSError, match="fixture storage failure"), database.session() as session:
        _service(session, store).persist(
            owner_id=owner, collection=collection, snapshot_id=snapshot_id,
        )
    with database.session() as session:
        assert session.get(SnapshotRow, snapshot_id) is None
