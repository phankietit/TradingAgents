"""Owner-scoped immutable FRED storage; no default preparation/analysis activation."""

import hashlib
import json
from datetime import datetime
from uuid import UUID, uuid4

from tradingagents.contracts import ArtifactKind, SnapshotManifest
from tradingagents.dataflows.platform_fred import MacroCollection
from tradingagents.platform.analysis.snapshots import snapshot_ineligibility
from tradingagents.platform.persistence.repository import ImmutableRecordConflict

MACRO_MEDIA_TYPE = "application/vnd.tradingagents.fred-series+json"


def _payload(collection):
    return json.dumps(collection.model_dump(mode="json"), ensure_ascii=False,
        sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _manifest(collection, snapshot_id):
    dates = [point.observation_date for point in collection.observations]
    return SnapshotManifest(snapshot_id=snapshot_id, instrument_id=collection.instrument_id,
        dataset=collection.dataset, vendor=collection.vendor,
        as_of=collection.retrieved_at, retrieved_at=collection.retrieved_at,
        # Economic observation dates are periods, NOT availability/release times.
        source_start=collection.vintage_available_at if dates else None,
        source_end=collection.vintage_available_at if dates else None,
        content_hash="sha256:" + hashlib.sha256(_payload(collection)).hexdigest(),
        quality_status=collection.quality_status, quality_reasons=(collection.reason,),
        metadata={"series_id": collection.series_id, "coverage": collection.coverage,
            "retrieval_path": collection.retrieval_path,
            "requested_at": collection.requested_at.isoformat(),
            "analysis_as_of": collection.analysis_as_of.isoformat(),
            "vintage_date": collection.vintage_date.isoformat(),
            "availability": "complete_chicago_vintage_day_not_exact_release_time",
            "observation_start": collection.observation_start.isoformat(),
            "observation_end": collection.observation_end.isoformat(),
            "first_observation_date": min(dates).isoformat() if dates else None,
            "last_observation_date": max(dates).isoformat() if dates else None,
            "observations": len(dates),
            "missing_observations": sum(point.value is None for point in collection.observations),
            "units": collection.units, "frequency_short": collection.frequency_short})


class MacroSnapshotService:
    def __init__(self, repository, artifacts):
        self.repository, self.artifacts = repository, artifacts

    def _identity(self, collection):
        instrument = self.repository.get_instrument(collection.instrument_id)
        if instrument is None or any(getattr(collection, key) != expected for key, expected in {
                "canonical_symbol": instrument.canonical_symbol,
                "asset_class": instrument.asset_class.value, "venue": instrument.venue,
                "quote_currency": instrument.quote_currency, "timezone": instrument.timezone}.items()):
            raise ValueError("macro collection instrument identity mismatch")

    def persist(self, *, owner_id: UUID, collection: MacroCollection,
                snapshot_id: UUID | None = None) -> SnapshotManifest:
        collection = MacroCollection.model_validate(collection.model_dump())
        self._identity(collection)
        manifest = _manifest(collection, snapshot_id or uuid4())
        self.repository.add_snapshot(manifest)
        existing = self.repository.get_snapshot_artifact(manifest.snapshot_id, owner_id)
        if existing is not None:
            if (existing.kind is not ArtifactKind.SNAPSHOT_PAYLOAD
                    or existing.media_type != MACRO_MEDIA_TYPE
                    or existing.instrument_id != manifest.instrument_id
                    or existing.content_hash != manifest.content_hash):
                raise ImmutableRecordConflict("macro snapshot artifact already has different content")
            return manifest
        self.artifacts.create(owner_id=owner_id, kind=ArtifactKind.SNAPSHOT_PAYLOAD,
            media_type=MACRO_MEDIA_TYPE, content=_payload(collection),
            instrument_id=manifest.instrument_id, snapshot_id=manifest.snapshot_id,
            created_at=collection.retrieved_at, expected_hash=manifest.content_hash)
        return manifest

    def load(self, *, owner_id: UUID, snapshot_id: UUID, instrument_id: UUID,
             as_of: datetime, max_age_seconds: int):
        if type(max_age_seconds) is not int or not 0 <= max_age_seconds <= 315360000:
            raise ValueError("macro freshness limit is outside supported bounds")
        if type(as_of) is not datetime or as_of.utcoffset() is None:
            raise ValueError("macro analysis cutoff must be timezone-aware")
        manifest = self.repository.get_snapshot(snapshot_id)
        artifact = self.repository.get_snapshot_artifact(snapshot_id, owner_id)
        if manifest is None or artifact is None:
            raise LookupError("owner macro snapshot unavailable")
        if (manifest.dataset != "macro" or manifest.vendor != "fred"
                or snapshot_ineligibility(manifest, instrument_id, as_of, max_age_seconds)):
            raise ValueError("macro snapshot is not eligible at requested cutoff")
        if (artifact.kind is not ArtifactKind.SNAPSHOT_PAYLOAD
                or artifact.media_type != MACRO_MEDIA_TYPE or artifact.snapshot_id != snapshot_id
                or artifact.instrument_id != instrument_id or artifact.content_hash != manifest.content_hash):
            raise ValueError("macro snapshot artifact does not match manifest")
        loaded = self.artifacts.read(artifact.artifact_id, owner_id)
        if loaded is None:
            raise LookupError("owner macro snapshot unavailable")
        collection = MacroCollection.model_validate_json(loaded[1])
        self._identity(collection)
        if _manifest(collection, snapshot_id) != manifest:
            raise ValueError("macro snapshot payload does not match manifest")
        return manifest, collection
