"""BTC/ETH UTC snapshot pipeline with multi-venue quality and BTC benchmark."""

from __future__ import annotations

import hashlib
import json
import statistics
from datetime import datetime
from uuid import UUID, uuid4

from tradingagents.contracts import (
    ArtifactKind,
    AssetClass,
    CryptoLiquidityMetrics,
    CryptoQualityThresholds,
    CryptoSnapshot,
    CryptoVenueObservation,
    DataQualityStatus,
    InstrumentContract,
    SnapshotManifest,
)
from tradingagents.platform.artifacts import ArtifactService
from tradingagents.platform.persistence import ImmutableRecordConflict, PlatformRepository

from .equity_etf import QUALITY_PRIORITY
from .timeseries import TimeSeriesSnapshotService, build_time_series_view


class CryptoSnapshotPipeline:
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
        price_dataset: str,
        venue_observations: tuple[CryptoVenueObservation, ...],
        thresholds: CryptoQualityThresholds,
        pipeline_id: str,
        benchmark_instrument: InstrumentContract | None = None,
        crypto_snapshot_id: UUID | None = None,
    ) -> tuple[SnapshotManifest, CryptoSnapshot]:
        if instrument.asset_class is not AssetClass.CRYPTO:
            raise ValueError("crypto pipeline requires a crypto instrument")
        if instrument.canonical_symbol not in {"BTC-USD", "ETH-USD"}:
            raise ValueError("initial crypto pipeline is limited to BTC and ETH")
        if instrument.timezone != "UTC" or instrument.session_calendar != "24/7":
            raise ValueError("crypto pipeline requires UTC and a 24/7 calendar")
        if not pipeline_id.strip():
            raise ValueError("pipeline_id is required")

        base_asset = instrument.canonical_symbol.removesuffix("-USD")
        for observation in venue_observations:
            if observation.base_asset.upper() != base_asset or observation.quote_asset.upper() != "USD":
                raise ValueError("crypto venue identity does not match the instrument")
            if observation.observed_at.utcoffset() is None or observation.observed_at.utcoffset().total_seconds() != 0:
                raise ValueError("crypto venue observations must use UTC")

        eligible = tuple(
            sorted(
                (item for item in venue_observations if item.observed_at <= as_of),
                key=lambda item: item.venue.casefold(),
            )
        )
        venue_names = [item.venue.casefold() for item in eligible]
        if len(venue_names) != len(set(venue_names)):
            raise ValueError("crypto venue observations must use unique venues")
        excluded_future = len(venue_observations) - len(eligible)
        spreads = [
            (item.ask - item.bid) / ((item.ask + item.bid) / 2) * 10_000
            for item in eligible
        ]
        ages = [(as_of - item.observed_at).total_seconds() for item in eligible]
        liquidity = CryptoLiquidityMetrics(
            observed_venues=len(eligible),
            excluded_future_observations=excluded_future,
            aggregate_quote_volume_24h=sum(item.quote_volume_24h for item in eligible),
            median_spread_bps=statistics.median(spreads) if spreads else None,
            oldest_observation_age_seconds=max(ages) if ages else None,
        )

        price_snapshot, series = self.time_series.load(
            owner_id=owner_id,
            instrument_id=instrument.instrument_id,
            dataset=price_dataset,
            as_of=as_of,
        )
        benchmark_snapshot = None
        benchmark_series = None
        if instrument.canonical_symbol == "ETH-USD":
            if benchmark_instrument is None or benchmark_instrument.canonical_symbol != "BTC-USD":
                raise ValueError("ETH crypto snapshots require the BTC-USD benchmark instrument")
            if benchmark_instrument.asset_class is not AssetClass.CRYPTO:
                raise ValueError("crypto benchmark must be a crypto instrument")
            benchmark_snapshot, benchmark_series = self.time_series.load(
                owner_id=owner_id,
                instrument_id=benchmark_instrument.instrument_id,
                dataset=price_dataset,
                as_of=as_of,
            )
        elif benchmark_instrument is not None:
            raise ValueError("BTC is the benchmark and must not receive another benchmark")

        view = build_time_series_view(series, benchmark=benchmark_series)
        statuses = [price_snapshot.quality_status]
        reasons = list(price_snapshot.quality_reasons)
        if len(eligible) < thresholds.min_venues:
            statuses.append(DataQualityStatus.COVERAGE_GAP)
            reasons.append(
                f"venue coverage {len(eligible)} is below required {thresholds.min_venues}"
            )
        if liquidity.aggregate_quote_volume_24h < thresholds.min_aggregate_quote_volume_24h:
            statuses.append(DataQualityStatus.COVERAGE_GAP)
            reasons.append("aggregate quote volume is below the configured threshold")
        if (
            liquidity.median_spread_bps is not None
            and liquidity.median_spread_bps > thresholds.max_median_spread_bps
        ):
            statuses.append(DataQualityStatus.COVERAGE_GAP)
            reasons.append("median spread is above the configured threshold")
        if (
            liquidity.oldest_observation_age_seconds is None
            or liquidity.oldest_observation_age_seconds > thresholds.max_observation_age_seconds
        ):
            statuses.append(DataQualityStatus.STALE)
            reasons.append("one or more venue observations are stale or absent")
        quality = max(statuses, key=QUALITY_PRIORITY.__getitem__)

        snapshot = CryptoSnapshot(
            crypto_snapshot_id=crypto_snapshot_id or uuid4(),
            instrument_id=instrument.instrument_id,
            canonical_symbol=instrument.canonical_symbol,
            as_of=as_of,
            retrieved_at=retrieved_at,
            price_snapshot_id=price_snapshot.snapshot_id,
            benchmark_price_snapshot_id=(
                benchmark_snapshot.snapshot_id if benchmark_snapshot is not None else None
            ),
            venues=eligible,
            thresholds=thresholds,
            liquidity=liquidity,
            price_statistics=view.statistics,
            benchmark=view.benchmark,
            quality_status=quality,
            quality_reasons=tuple(reasons),
        )
        return self._persist(owner_id=owner_id, snapshot=snapshot, pipeline_id=pipeline_id)

    def load(
        self,
        *,
        owner_id: UUID,
        instrument_id: UUID,
        as_of: datetime,
    ) -> tuple[SnapshotManifest, CryptoSnapshot]:
        manifest = self.repository.latest_snapshot(
            instrument_id=instrument_id,
            dataset="crypto.bundle",
            as_of=as_of,
        )
        if manifest is None:
            raise LookupError("no eligible crypto snapshot")
        artifact = self.repository.get_snapshot_artifact(manifest.snapshot_id, owner_id)
        if artifact is None:
            raise LookupError("crypto snapshot payload is unavailable")
        loaded = self.artifacts.read(artifact.artifact_id, owner_id)
        if loaded is None:
            raise LookupError("crypto snapshot payload is unavailable")
        _artifact, payload = loaded
        snapshot = CryptoSnapshot.model_validate_json(payload)
        if snapshot.instrument_id != instrument_id or snapshot.crypto_snapshot_id != manifest.snapshot_id:
            raise ValueError("crypto payload identity does not match its snapshot")
        return manifest, snapshot

    def _persist(
        self,
        *,
        owner_id: UUID,
        snapshot: CryptoSnapshot,
        pipeline_id: str,
    ) -> tuple[SnapshotManifest, CryptoSnapshot]:
        content = json.dumps(
            snapshot.model_dump(mode="json"),
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        content_hash = "sha256:" + hashlib.sha256(content).hexdigest()
        price_snapshot = self.repository.get_snapshot(snapshot.price_snapshot_id)
        if price_snapshot is None:
            raise ValueError("crypto price snapshot no longer exists")
        source_times = [
            value
            for value in (price_snapshot.source_start, price_snapshot.source_end)
            if value is not None
        ]
        source_times.extend(item.observed_at for item in snapshot.venues)
        manifest = SnapshotManifest(
            snapshot_id=snapshot.crypto_snapshot_id,
            instrument_id=snapshot.instrument_id,
            dataset="crypto.bundle",
            vendor=pipeline_id,
            as_of=snapshot.as_of,
            retrieved_at=snapshot.retrieved_at,
            source_start=min(source_times) if source_times else None,
            source_end=max(source_times) if source_times else None,
            content_hash=content_hash,
            quality_status=snapshot.quality_status,
            quality_reasons=snapshot.quality_reasons,
            metadata={
                "canonical_symbol": snapshot.canonical_symbol,
                "price_snapshot_id": str(snapshot.price_snapshot_id),
                "benchmark_price_snapshot_id": (
                    str(snapshot.benchmark_price_snapshot_id)
                    if snapshot.benchmark_price_snapshot_id is not None
                    else None
                ),
                "venue_count": snapshot.liquidity.observed_venues,
                "excluded_future_observations": (
                    snapshot.liquidity.excluded_future_observations
                ),
                "thresholds": snapshot.thresholds.model_dump(mode="json"),
            },
        )
        self.repository.add_snapshot(manifest)
        existing = self.repository.get_snapshot_artifact(manifest.snapshot_id, owner_id)
        if existing is not None:
            if existing.content_hash != manifest.content_hash:
                raise ImmutableRecordConflict("snapshot artifact already has different content")
            return manifest, snapshot
        self.artifacts.create(
            owner_id=owner_id,
            kind=ArtifactKind.SNAPSHOT_PAYLOAD,
            media_type="application/vnd.tradingagents.crypto-snapshot+json",
            content=content,
            instrument_id=snapshot.instrument_id,
            snapshot_id=manifest.snapshot_id,
            created_at=snapshot.retrieved_at,
            expected_hash=content_hash,
        )
        return manifest, snapshot
