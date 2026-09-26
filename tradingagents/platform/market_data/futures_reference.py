"""NQ/ES reference-only continuous-series snapshot pipeline."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from uuid import UUID, uuid4

from tradingagents.contracts import (
    ArtifactKind,
    AssetClass,
    DataQualityStatus,
    FuturesContractReference,
    FuturesDataGap,
    FuturesReferenceSnapshot,
    FuturesSessionWindow,
    GapDisposition,
    InstrumentContract,
    RolloverMetadata,
    SnapshotManifest,
    Tradability,
    worst_data_quality_status,
)
from tradingagents.platform.artifacts import ArtifactService
from tradingagents.platform.persistence import ImmutableRecordConflict, PlatformRepository

from .timeseries import TimeSeriesSnapshotService


class FuturesReferencePipeline:
    def __init__(
        self,
        repository: PlatformRepository,
        artifacts: ArtifactService,
    ):
        self.repository = repository
        self.artifacts = artifacts
        self.time_series = TimeSeriesSnapshotService(repository, artifacts)

    def build(
        self,
        *,
        owner_id: UUID,
        instrument: InstrumentContract,
        as_of: datetime,
        retrieved_at: datetime,
        continuous_dataset: str,
        active_contract: FuturesContractReference,
        next_contract: FuturesContractReference | None,
        rollovers: tuple[RolloverMetadata, ...],
        sessions: tuple[FuturesSessionWindow, ...],
        gaps: tuple[FuturesDataGap, ...] = (),
        pipeline_id: str,
        reference_id: UUID | None = None,
    ) -> tuple[SnapshotManifest, FuturesReferenceSnapshot]:
        if instrument.asset_class is not AssetClass.REFERENCE_FUTURE:
            raise ValueError("futures reference pipeline requires a reference future")
        if instrument.tradability is not Tradability.REFERENCE_ONLY:
            raise ValueError("futures reference pipeline cannot use an investable instrument")
        if instrument.canonical_symbol not in {"NQ=F", "ES=F"}:
            raise ValueError("initial futures reference pipeline is limited to NQ=F and ES=F")
        if instrument.timezone != "America/Chicago" or instrument.session_calendar != "CME_Equity":
            raise ValueError("NQ/ES references require CME_Equity in America/Chicago")
        if not pipeline_id.strip():
            raise ValueError("pipeline_id is required")

        root_symbol = instrument.canonical_symbol.removesuffix("=F")
        price_snapshot, series = self.time_series.load(
            owner_id=owner_id,
            instrument_id=instrument.instrument_id,
            dataset=continuous_dataset,
            as_of=as_of,
        )
        if series.timezone != instrument.timezone:
            raise ValueError("continuous series timezone does not match the instrument")

        sorted_rollovers = tuple(sorted(rollovers, key=lambda item: item.effective_at))
        sorted_sessions = tuple(sorted(sessions, key=lambda item: item.overnight_open))
        sorted_gaps = tuple(sorted(gaps, key=lambda item: item.start))
        degraded_gaps = [
            gap
            for gap in sorted_gaps
            if gap.disposition is GapDisposition.UNAVAILABLE
        ]
        statuses = [price_snapshot.quality_status]
        reasons = list(price_snapshot.quality_reasons)
        if degraded_gaps:
            statuses.append(DataQualityStatus.COVERAGE_GAP)
            reasons.append(f"{len(degraded_gaps)} unresolved futures data gap(s)")
        quality = worst_data_quality_status(statuses)

        reference = FuturesReferenceSnapshot(
            reference_id=reference_id or uuid4(),
            instrument_id=instrument.instrument_id,
            root_symbol=root_symbol,
            as_of=as_of,
            retrieved_at=retrieved_at,
            continuous_series_snapshot_id=price_snapshot.snapshot_id,
            active_contract=active_contract,
            next_contract=next_contract,
            rollovers=sorted_rollovers,
            sessions=sorted_sessions,
            gaps=sorted_gaps,
            quality_status=quality,
            quality_reasons=tuple(reasons),
        )
        return self._persist(owner_id=owner_id, reference=reference, pipeline_id=pipeline_id)

    def load(
        self,
        *,
        owner_id: UUID,
        instrument_id: UUID,
        as_of: datetime,
    ) -> tuple[SnapshotManifest, FuturesReferenceSnapshot]:
        snapshot = self.repository.latest_snapshot(
            instrument_id=instrument_id,
            dataset="futures.reference",
            as_of=as_of,
        )
        if snapshot is None:
            raise LookupError("no eligible futures reference snapshot")
        artifact = self.repository.get_snapshot_artifact(snapshot.snapshot_id, owner_id)
        if artifact is None:
            raise LookupError("futures reference payload is unavailable")
        loaded = self.artifacts.read(artifact.artifact_id, owner_id)
        if loaded is None:
            raise LookupError("futures reference payload is unavailable")
        _artifact, payload = loaded
        reference = FuturesReferenceSnapshot.model_validate_json(payload)
        if reference.instrument_id != instrument_id or reference.reference_id != snapshot.snapshot_id:
            raise ValueError("futures reference payload identity does not match its snapshot")
        return snapshot, reference

    def _persist(
        self,
        *,
        owner_id: UUID,
        reference: FuturesReferenceSnapshot,
        pipeline_id: str,
    ) -> tuple[SnapshotManifest, FuturesReferenceSnapshot]:
        content = json.dumps(
            reference.model_dump(mode="json"),
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        content_hash = "sha256:" + hashlib.sha256(content).hexdigest()
        continuous_snapshot = self.repository.get_snapshot(
            reference.continuous_series_snapshot_id
        )
        if continuous_snapshot is None:
            raise ValueError("continuous-series snapshot no longer exists")
        source_times = [
            value
            for value in (
                continuous_snapshot.source_start,
                continuous_snapshot.source_end,
            )
            if value is not None
        ]
        source_times.extend(
            roll.effective_at
            for roll in reference.rollovers
            if roll.effective_at <= reference.as_of
        )
        source_times.extend(gap.start for gap in reference.gaps)
        source_times.extend(gap.end for gap in reference.gaps)
        manifest = SnapshotManifest(
            snapshot_id=reference.reference_id,
            instrument_id=reference.instrument_id,
            dataset="futures.reference",
            vendor=pipeline_id,
            as_of=reference.as_of,
            retrieved_at=reference.retrieved_at,
            source_start=min(source_times) if source_times else None,
            source_end=max(source_times) if source_times else None,
            content_hash=content_hash,
            quality_status=reference.quality_status,
            quality_reasons=reference.quality_reasons,
            metadata={
                "root_symbol": reference.root_symbol,
                "active_contract": reference.active_contract.contract_symbol,
                "next_contract": (
                    reference.next_contract.contract_symbol
                    if reference.next_contract is not None
                    else None
                ),
                "continuous_series_snapshot_id": str(
                    reference.continuous_series_snapshot_id
                ),
                "session_count": len(reference.sessions),
                "rollover_count": len(reference.rollovers),
                "gap_count": len(reference.gaps),
            },
        )
        self.repository.add_snapshot(manifest)
        existing = self.repository.get_snapshot_artifact(manifest.snapshot_id, owner_id)
        if existing is not None:
            if existing.content_hash != manifest.content_hash:
                raise ImmutableRecordConflict("snapshot artifact already has different content")
            return manifest, reference
        self.artifacts.create(
            owner_id=owner_id,
            kind=ArtifactKind.SNAPSHOT_PAYLOAD,
            media_type="application/vnd.tradingagents.futures-reference+json",
            content=content,
            instrument_id=reference.instrument_id,
            snapshot_id=manifest.snapshot_id,
            created_at=reference.retrieved_at,
            expected_hash=content_hash,
        )
        return manifest, reference
