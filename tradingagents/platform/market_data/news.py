"""Owner-bound immutable storage for current-vintage news collections."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from uuid import UUID, uuid4

from tradingagents.contracts import ArtifactKind, SnapshotManifest
from tradingagents.dataflows.platform_news import NewsCollection
from tradingagents.platform.analysis.snapshots import snapshot_ineligibility
from tradingagents.platform.persistence.repository import ImmutableRecordConflict

NEWS_MEDIA_TYPE = "application/vnd.tradingagents.news+json"


class NewsSnapshotService:
    def __init__(self, repository, artifacts):
        self.repository = repository
        self.artifacts = artifacts

    def _validate_identity(self, collection: NewsCollection) -> None:
        instrument = self.repository.get_instrument(collection.instrument_id)
        if instrument is None or (
            collection.canonical_symbol != instrument.canonical_symbol
            or collection.asset_class != instrument.asset_class.value
            or collection.venue != instrument.venue
            or collection.quote_currency != instrument.quote_currency
            or collection.timezone != instrument.timezone
        ):
            raise ValueError("news collection instrument identity mismatch")

    def persist(
        self, *, owner_id: UUID, collection: NewsCollection, snapshot_id: UUID | None = None,
    ) -> SnapshotManifest:
        """Persist within the caller's commit-or-rollback database transaction."""
        # A frozen Pydantic model can still be changed through model_copy(update=...).
        collection = NewsCollection.model_validate(collection.model_dump())
        self._validate_identity(collection)
        payload = json.dumps(
            collection.model_dump(mode="json"), ensure_ascii=False, sort_keys=True,
            separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")
        published = [article.published_at for article in collection.articles]
        manifest = SnapshotManifest(
            snapshot_id=snapshot_id or uuid4(),
            instrument_id=collection.instrument_id,
            dataset=collection.dataset,
            vendor=collection.vendor,
            # Revised article text is observed at retrieval, never at publication.
            as_of=collection.retrieved_at,
            retrieved_at=collection.retrieved_at,
            source_start=min(published) if published else None,
            source_end=max(published) if published else None,
            content_hash="sha256:" + hashlib.sha256(payload).hexdigest(),
            quality_status=collection.quality_status,
            quality_reasons=(collection.reason,),
            metadata={
                "coverage": collection.coverage,
                "retrieval_path": collection.retrieval_path,
                "requested_at": collection.requested_at.isoformat(),
                "window_start": collection.window_start.isoformat(),
                "articles": len(collection.articles),
                "invalid_records": collection.invalid_records,
                "excluded_out_of_window": collection.excluded_out_of_window,
            },
        )
        self.repository.add_snapshot(manifest)
        existing = self.repository.get_snapshot_artifact(manifest.snapshot_id, owner_id)
        if existing is not None:
            if (
                existing.content_hash != manifest.content_hash
                or existing.instrument_id != manifest.instrument_id
                or existing.kind is not ArtifactKind.SNAPSHOT_PAYLOAD
                or existing.media_type != NEWS_MEDIA_TYPE
            ):
                raise ImmutableRecordConflict("news snapshot artifact already has different content")
            return manifest
        self.artifacts.create(
            owner_id=owner_id,
            kind=ArtifactKind.SNAPSHOT_PAYLOAD,
            media_type=NEWS_MEDIA_TYPE,
            content=payload,
            instrument_id=collection.instrument_id,
            snapshot_id=manifest.snapshot_id,
            created_at=collection.retrieved_at,
            expected_hash=manifest.content_hash,
        )
        return manifest

    def load(
        self, *, owner_id: UUID, snapshot_id: UUID, instrument_id: UUID,
        as_of: datetime, max_age_seconds: int,
    ) -> tuple[SnapshotManifest, NewsCollection]:
        if not 0 <= max_age_seconds <= 315360000:
            raise ValueError("news freshness limit is outside supported bounds")
        if as_of.tzinfo is None or as_of.utcoffset() is None:
            raise ValueError("news analysis cutoff must be timezone-aware")
        manifest = self.repository.get_snapshot(snapshot_id)
        artifact = self.repository.get_snapshot_artifact(snapshot_id, owner_id)
        if manifest is None or artifact is None:
            raise LookupError("owner news snapshot unavailable")
        if manifest.dataset != "news" or snapshot_ineligibility(
            manifest, instrument_id, as_of, max_age_seconds,
        ):
            raise ValueError("news snapshot is not eligible at requested cutoff")
        if (
            artifact.kind is not ArtifactKind.SNAPSHOT_PAYLOAD
            or artifact.media_type != NEWS_MEDIA_TYPE
            or artifact.snapshot_id != snapshot_id
            or artifact.instrument_id != instrument_id
            or artifact.content_hash != manifest.content_hash
        ):
            raise ValueError("news snapshot artifact does not match manifest")
        loaded = self.artifacts.read(artifact.artifact_id, owner_id)
        if loaded is None:
            raise LookupError("owner news snapshot unavailable")
        collection = NewsCollection.model_validate_json(loaded[1])
        published = [article.published_at for article in collection.articles]
        if (
            collection.instrument_id != instrument_id
            or collection.dataset != manifest.dataset
            or collection.vendor != manifest.vendor
            or collection.retrieved_at != manifest.retrieved_at
            or manifest.as_of != collection.retrieved_at
            or collection.quality_status != manifest.quality_status
            or manifest.quality_reasons != (collection.reason,)
            or manifest.source_start != (min(published) if published else None)
            or manifest.source_end != (max(published) if published else None)
            or manifest.metadata.get("coverage") != collection.coverage
            or manifest.metadata.get("retrieval_path") != collection.retrieval_path
            or manifest.metadata.get("requested_at") != collection.requested_at.isoformat()
            or manifest.metadata.get("window_start") != collection.window_start.isoformat()
            or manifest.metadata.get("articles") != len(collection.articles)
            or manifest.metadata.get("invalid_records") != collection.invalid_records
            or manifest.metadata.get("excluded_out_of_window") != collection.excluded_out_of_window
        ):
            raise ValueError("news snapshot payload does not match manifest")
        self._validate_identity(collection)
        return manifest, collection
