"""Immutable owner social snapshots; publication time never backdates retrieval."""

import hashlib
import json
from uuid import uuid4

from tradingagents.contracts import ArtifactKind, SnapshotManifest
from tradingagents.dataflows.platform_social import SocialCollection
from tradingagents.platform.analysis.snapshots import snapshot_ineligibility
from tradingagents.platform.persistence.repository import ImmutableRecordConflict

SOCIAL_MEDIA_TYPE = "application/vnd.tradingagents.social-posts+json"


def _payload(collection):
    return json.dumps(collection.model_dump(mode="json"), ensure_ascii=False,
        sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _manifest(collection, snapshot_id):
    dates = [post.published_at for post in collection.posts]
    return SnapshotManifest(snapshot_id=snapshot_id, instrument_id=collection.instrument_id,
        dataset=collection.dataset, vendor=collection.vendor, as_of=collection.retrieved_at,
        retrieved_at=collection.retrieved_at, source_start=min(dates) if dates else None,
        source_end=max(dates) if dates else None,
        content_hash="sha256:" + hashlib.sha256(_payload(collection)).hexdigest(),
        quality_status=collection.quality_status, quality_reasons=(collection.reason,),
        metadata={"coverage": collection.coverage, "retrieval_path": collection.retrieval_path,
            "provider_symbol": collection.provider_symbol, "requested_at": collection.requested_at.isoformat(),
            "window_start": collection.window_start.isoformat(), "communities": list(collection.communities),
            "posts": len(collection.posts), "received_posts": collection.received_posts,
            "excluded_out_of_window": collection.excluded_out_of_window,
            "invalid_records": collection.invalid_records})


class SocialSnapshotService:
    def __init__(self, repository, artifacts):
        self.repository, self.artifacts = repository, artifacts

    def _identity(self, collection):
        from tradingagents.dataflows.platform_social import _scope
        instrument = self.repository.get_instrument(collection.instrument_id)
        if instrument is None or any(getattr(collection, name) != value
                for name, value in _scope(instrument, collection.vendor).items()):
            raise ValueError("social collection instrument identity mismatch")

    def persist(self, *, owner_id, collection, snapshot_id=None):
        collection = SocialCollection.model_validate(collection.model_dump())
        self._identity(collection)
        manifest = _manifest(collection, snapshot_id or uuid4())
        self.repository.add_snapshot(manifest)
        existing = self.repository.get_snapshot_artifact(manifest.snapshot_id, owner_id)
        if existing is not None:
            if (existing.kind is not ArtifactKind.SNAPSHOT_PAYLOAD or existing.media_type != SOCIAL_MEDIA_TYPE
                    or existing.instrument_id != manifest.instrument_id or existing.content_hash != manifest.content_hash):
                raise ImmutableRecordConflict("social snapshot artifact already has different content")
            return manifest
        self.artifacts.create(owner_id=owner_id, kind=ArtifactKind.SNAPSHOT_PAYLOAD,
            media_type=SOCIAL_MEDIA_TYPE, content=_payload(collection),
            instrument_id=collection.instrument_id, snapshot_id=manifest.snapshot_id,
            created_at=collection.retrieved_at, expected_hash=manifest.content_hash)
        return manifest

    def load(self, *, owner_id, snapshot_id, instrument_id, as_of, max_age_seconds):
        if (not 0 <= max_age_seconds <= 315360000 or as_of.tzinfo is None
                or as_of.utcoffset() is None):
            raise ValueError("invalid social observation cutoff")
        manifest = self.repository.get_snapshot(snapshot_id)
        artifact = self.repository.get_snapshot_artifact(snapshot_id, owner_id)
        if manifest is None or artifact is None:
            raise LookupError("owner social snapshot unavailable")
        if manifest.dataset != "social" or snapshot_ineligibility(manifest, instrument_id, as_of, max_age_seconds):
            raise ValueError("social snapshot is not eligible at requested cutoff")
        if (artifact.kind is not ArtifactKind.SNAPSHOT_PAYLOAD or artifact.media_type != SOCIAL_MEDIA_TYPE
                or artifact.snapshot_id != snapshot_id or artifact.instrument_id != instrument_id
                or artifact.content_hash != manifest.content_hash):
            raise ValueError("social artifact does not match manifest")
        loaded = self.artifacts.read(artifact.artifact_id, owner_id)
        if loaded is None:
            raise LookupError("owner social snapshot bytes unavailable")
        collection = SocialCollection.model_validate_json(loaded[1])
        self._identity(collection)
        if _manifest(collection, snapshot_id) != manifest:
            raise ValueError("social snapshot payload does not match manifest")
        return manifest, collection
