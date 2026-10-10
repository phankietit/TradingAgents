"""Owner-bound immutable SEC companyfacts snapshots for platform research."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, time
from uuid import UUID, uuid4

from tradingagents._compat import UTC
from tradingagents.contracts import ArtifactKind, SnapshotManifest
from tradingagents.dataflows.platform_sec import SecCollection
from tradingagents.platform.analysis.snapshots import snapshot_ineligibility
from tradingagents.platform.persistence.repository import ImmutableRecordConflict

SEC_MEDIA_TYPE = "application/vnd.tradingagents.sec-facts+json"


class SecSnapshotService:
    def __init__(self, repository, artifacts):
        self.repository = repository
        self.artifacts = artifacts

    def _validate_identity(self, collection: SecCollection):
        instrument = self.repository.get_instrument(collection.instrument_id)
        if instrument is None or (
            collection.canonical_symbol != instrument.canonical_symbol
            or collection.asset_class != instrument.asset_class.value
            or collection.venue != instrument.venue
            or collection.quote_currency != instrument.quote_currency
            or collection.timezone != instrument.timezone
        ):
            raise ValueError("SEC collection instrument identity mismatch")

    def persist(self, *, owner_id: UUID, collection: SecCollection,
                snapshot_id: UUID | None = None) -> SnapshotManifest:
        collection = SecCollection.model_validate(collection.model_dump())
        self._validate_identity(collection)
        payload = json.dumps(collection.model_dump(mode="json"), ensure_ascii=False,
            sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
        filed = [datetime.combine(fact.filed_at, time.min, tzinfo=UTC)
                 for fact in collection.facts]
        manifest = SnapshotManifest(
            snapshot_id=snapshot_id or uuid4(), instrument_id=collection.instrument_id,
            dataset=collection.dataset, vendor=collection.vendor,
            # A current retrieval is never backdated to an earlier filing.
            as_of=collection.retrieved_at, retrieved_at=collection.retrieved_at,
            source_start=min(filed) if filed else None,
            source_end=max(filed) if filed else None,
            content_hash="sha256:" + hashlib.sha256(payload).hexdigest(),
            quality_status=collection.quality_status,
            quality_reasons=(collection.reason,),
            metadata={"cik": collection.cik,
                      "retrieval_path": collection.retrieval_path,
                      "requested_at": collection.requested_at.isoformat(),
                      "facts": len(collection.facts),
                      "invalid_records": collection.invalid_records,
                      "vintage": "current_retrieval_filed_date_filter"},
        )
        self.repository.add_snapshot(manifest)
        existing = self.repository.get_snapshot_artifact(manifest.snapshot_id, owner_id)
        if existing is not None:
            if (existing.content_hash != manifest.content_hash
                    or existing.instrument_id != manifest.instrument_id
                    or existing.kind is not ArtifactKind.SNAPSHOT_PAYLOAD
                    or existing.media_type != SEC_MEDIA_TYPE):
                raise ImmutableRecordConflict("SEC snapshot artifact already has different content")
            return manifest
        self.artifacts.create(
            owner_id=owner_id, kind=ArtifactKind.SNAPSHOT_PAYLOAD,
            media_type=SEC_MEDIA_TYPE, content=payload,
            instrument_id=collection.instrument_id, snapshot_id=manifest.snapshot_id,
            created_at=collection.retrieved_at, expected_hash=manifest.content_hash,
        )
        return manifest

    def load(self, *, owner_id: UUID, snapshot_id: UUID, instrument_id: UUID,
             as_of: datetime, max_age_seconds: int) -> tuple[SnapshotManifest, SecCollection]:
        if not 0 <= max_age_seconds <= 315360000:
            raise ValueError("SEC freshness limit is outside supported bounds")
        if as_of.tzinfo is None or as_of.utcoffset() is None:
            raise ValueError("SEC analysis cutoff must be timezone-aware")
        manifest = self.repository.get_snapshot(snapshot_id)
        artifact = self.repository.get_snapshot_artifact(snapshot_id, owner_id)
        if manifest is None or artifact is None:
            raise LookupError("owner SEC snapshot unavailable")
        if manifest.dataset != "fundamentals" or snapshot_ineligibility(
            manifest, instrument_id, as_of, max_age_seconds,
        ):
            raise ValueError("SEC snapshot is not eligible at requested cutoff")
        if (artifact.kind is not ArtifactKind.SNAPSHOT_PAYLOAD
                or artifact.media_type != SEC_MEDIA_TYPE
                or artifact.snapshot_id != snapshot_id
                or artifact.instrument_id != instrument_id
                or artifact.content_hash != manifest.content_hash):
            raise ValueError("SEC snapshot artifact does not match manifest")
        loaded = self.artifacts.read(artifact.artifact_id, owner_id)
        if loaded is None:
            raise LookupError("owner SEC snapshot unavailable")
        collection = SecCollection.model_validate_json(loaded[1])
        filed = [datetime.combine(fact.filed_at, time.min, tzinfo=UTC)
                 for fact in collection.facts]
        if (collection.instrument_id != instrument_id
                or collection.dataset != manifest.dataset
                or collection.vendor != manifest.vendor
                or collection.retrieved_at != manifest.retrieved_at
                or manifest.as_of != collection.retrieved_at
                or collection.quality_status != manifest.quality_status
                or manifest.quality_reasons != (collection.reason,)
                or manifest.source_start != (min(filed) if filed else None)
                or manifest.source_end != (max(filed) if filed else None)
                or manifest.metadata.get("cik") != collection.cik
                or manifest.metadata.get("retrieval_path") != collection.retrieval_path
                or manifest.metadata.get("requested_at") != collection.requested_at.isoformat()
                or manifest.metadata.get("facts") != len(collection.facts)
                or manifest.metadata.get("invalid_records") != collection.invalid_records
                or manifest.metadata.get("vintage") != "current_retrieval_filed_date_filter"):
            raise ValueError("SEC snapshot payload does not match manifest")
        self._validate_identity(collection)
        return manifest, collection
