"""Owner-bound immutable storage for current-vintage news collections."""

import hashlib
import json
from uuid import uuid4

from tradingagents.contracts import ArtifactKind, SnapshotManifest
from tradingagents.dataflows.platform_news import NewsCollection
from tradingagents.platform.analysis.snapshots import snapshot_ineligibility


class NewsSnapshotService:
    def __init__(self, repository, artifacts):
        self.repository = repository
        self.artifacts = artifacts

    def _identity(self, collection):
        instrument = self.repository.get_instrument(collection.instrument_id)
        if instrument is None or any(getattr(collection, field) != value for field, value in {
            "canonical_symbol":instrument.canonical_symbol if instrument else None,
            "asset_class":instrument.asset_class.value if instrument else None,
            "venue":instrument.venue if instrument else None,
            "quote_currency":instrument.quote_currency if instrument else None,
            "timezone":instrument.timezone if instrument else None,
        }.items()):
            raise ValueError("news collection instrument identity mismatch")

    def persist(self, *, owner_id, collection):
        # Revalidate even frozen instances: model_copy can bypass validators.
        collection = NewsCollection.model_validate(collection.model_dump())
        self._identity(collection)
        payload = json.dumps(collection.model_dump(mode="json"), ensure_ascii=False,
                             sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        published = [article.published_at for article in collection.articles]
        manifest = SnapshotManifest(snapshot_id=uuid4(), instrument_id=collection.instrument_id,
            dataset=collection.dataset, vendor=collection.vendor,
            # Today's revised article text was observed at retrieval, not at its
            # original publication date or at the beginning of the request.
            as_of=collection.retrieved_at, retrieved_at=collection.retrieved_at,
            source_start=min(published) if published else None,
            source_end=max(published) if published else None,
            content_hash="sha256:" + hashlib.sha256(payload).hexdigest(),
            quality_status=collection.quality_status, quality_reasons=(collection.reason,),
            metadata={"coverage":collection.coverage, "retrieval_path":collection.retrieval_path,
                "requested_at":collection.requested_at.isoformat(),
                "window_start":collection.window_start.isoformat(),
                "articles":len(collection.articles), "invalid_records":collection.invalid_records,
                "excluded_out_of_window":collection.excluded_out_of_window})
        self.repository.add_snapshot(manifest)
        self.artifacts.create(owner_id=owner_id, kind=ArtifactKind.SNAPSHOT_PAYLOAD,
            media_type="application/vnd.tradingagents.news+json", content=payload,
            instrument_id=collection.instrument_id, snapshot_id=manifest.snapshot_id,
            created_at=collection.retrieved_at, expected_hash=manifest.content_hash)
        return manifest

    def load(self, *, owner_id, snapshot_id, instrument_id, as_of, max_age_seconds):
        if max_age_seconds < 0:
            raise ValueError("news freshness limit must not be negative")
        manifest = self.repository.get_snapshot(snapshot_id)
        artifact = self.repository.get_snapshot_artifact(snapshot_id, owner_id)
        if manifest is None or artifact is None:
            raise LookupError("owner news snapshot unavailable")
        if manifest.dataset != "news" or snapshot_ineligibility(manifest, instrument_id, as_of, max_age_seconds):
            raise ValueError("news snapshot is not eligible at requested cutoff")
        loaded = self.artifacts.read(artifact.artifact_id, owner_id)
        if loaded is None:
            raise LookupError("owner news snapshot unavailable")
        collection = NewsCollection.model_validate_json(loaded[1])
        if (artifact.content_hash != manifest.content_hash or artifact.instrument_id != instrument_id
                or collection.instrument_id != instrument_id or collection.vendor != manifest.vendor
                or collection.retrieved_at != manifest.retrieved_at
                or manifest.as_of != collection.retrieved_at
                or collection.quality_status != manifest.quality_status):
            raise ValueError("news snapshot payload does not match manifest")
        self._identity(collection)
        return manifest, collection
