"""Normalization, immutable snapshot storage, and deterministic price metrics."""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from tradingagents.contracts import (
    ArtifactKind,
    BenchmarkComparison,
    DataQualityStatus,
    InstrumentContract,
    NormalizedTimeSeries,
    OHLCVBar,
    PriceBasis,
    PriceInterval,
    ReturnPoint,
    SnapshotManifest,
    TimeSeriesStatistics,
    TimeSeriesView,
)
from tradingagents.platform.artifacts import ArtifactService
from tradingagents.platform.persistence import ImmutableRecordConflict, PlatformRepository


class TimeSeriesUnavailable(LookupError):
    """No eligible immutable time-series snapshot can answer the query."""


class InsufficientBenchmarkCoverage(ValueError):
    """Asset and benchmark do not have enough aligned observations."""


def _price(bar: OHLCVBar, basis: PriceBasis) -> float:
    if basis is PriceBasis.ADJUSTED_CLOSE:
        assert bar.adjusted_close is not None
        return bar.adjusted_close
    return bar.close


def normalize_time_series(
    *,
    instrument: InstrumentContract,
    dataset: str,
    interval: PriceInterval,
    as_of: datetime,
    annualization_periods: int,
    bars: Iterable[OHLCVBar | Mapping[str, Any]],
) -> NormalizedTimeSeries:
    normalized_bars = tuple(
        sorted(
            (OHLCVBar.model_validate(bar) for bar in bars),
            key=lambda bar: bar.timestamp,
        )
    )
    if instrument.timezone.upper() == "UTC" and any(
        bar.timestamp.utcoffset() is None
        or bar.timestamp.utcoffset().total_seconds() != 0
        for bar in normalized_bars
    ):
        raise ValueError("UTC instruments require UTC bar timestamps")
    return NormalizedTimeSeries(
        instrument_id=instrument.instrument_id,
        dataset=dataset,
        interval=interval,
        timezone=instrument.timezone,
        quote_currency=instrument.quote_currency,
        as_of=as_of,
        annualization_periods=annualization_periods,
        bars=normalized_bars,
    )


def _return_points(series: NormalizedTimeSeries) -> tuple[ReturnPoint, ...]:
    basis = series.price_basis
    prices = [_price(bar, basis) for bar in series.bars]
    running_peak = prices[0]
    points = []
    previous = None
    for bar, price in zip(series.bars, prices, strict=True):
        running_peak = max(running_peak, price)
        points.append(
            ReturnPoint(
                timestamp=bar.timestamp,
                price=price,
                simple_return=None if previous is None else price / previous - 1,
                drawdown=price / running_peak - 1,
            )
        )
        previous = price
    return tuple(points)


def _statistics(
    series: NormalizedTimeSeries, points: tuple[ReturnPoint, ...]
) -> TimeSeriesStatistics:
    returns = [point.simple_return for point in points if point.simple_return is not None]
    volatility = (
        statistics.stdev(returns) * math.sqrt(series.annualization_periods)
        if len(returns) >= 2
        else 0.0
    )
    return TimeSeriesStatistics(
        observations=len(points),
        price_basis=series.price_basis,
        total_return=points[-1].price / points[0].price - 1,
        annualized_volatility=volatility,
        maximum_drawdown=min(point.drawdown for point in points),
    )


def _benchmark_comparison(
    asset: NormalizedTimeSeries,
    benchmark: NormalizedTimeSeries,
) -> BenchmarkComparison:
    if asset.interval is not benchmark.interval:
        raise ValueError("asset and benchmark intervals must match")
    if asset.quote_currency != benchmark.quote_currency:
        raise ValueError("asset and benchmark quote currencies must match")
    benchmark_prices = {
        bar.timestamp: _price(bar, benchmark.price_basis) for bar in benchmark.bars
    }
    aligned = [
        (bar.timestamp, _price(bar, asset.price_basis), benchmark_prices[bar.timestamp])
        for bar in asset.bars
        if bar.timestamp in benchmark_prices
    ]
    if len(aligned) < 2:
        raise InsufficientBenchmarkCoverage(
            "asset and benchmark require at least two aligned observations"
        )
    asset_returns = [
        current[1] / previous[1] - 1
        for previous, current in zip(aligned, aligned[1:], strict=False)
    ]
    benchmark_returns = [
        current[2] / previous[2] - 1
        for previous, current in zip(aligned, aligned[1:], strict=False)
    ]
    excess_returns = [
        asset_return - benchmark_return
        for asset_return, benchmark_return in zip(
            asset_returns, benchmark_returns, strict=True
        )
    ]
    correlation = None
    if (
        len(asset_returns) >= 2
        and statistics.pstdev(asset_returns) > 0
        and statistics.pstdev(benchmark_returns) > 0
    ):
        correlation = statistics.correlation(asset_returns, benchmark_returns)
    tracking_error = (
        statistics.stdev(excess_returns) * math.sqrt(asset.annualization_periods)
        if len(excess_returns) >= 2
        else 0.0
    )
    return BenchmarkComparison(
        benchmark_instrument_id=benchmark.instrument_id,
        aligned_observations=len(aligned),
        asset_return=aligned[-1][1] / aligned[0][1] - 1,
        benchmark_return=aligned[-1][2] / aligned[0][2] - 1,
        excess_return=(aligned[-1][1] / aligned[0][1])
        - (aligned[-1][2] / aligned[0][2]),
        correlation=correlation,
        annualized_tracking_error=tracking_error,
    )


def build_time_series_view(
    series: NormalizedTimeSeries,
    *,
    benchmark: NormalizedTimeSeries | None = None,
) -> TimeSeriesView:
    points = _return_points(series)
    return TimeSeriesView(
        series=series,
        returns=points,
        statistics=_statistics(series, points),
        benchmark=(
            _benchmark_comparison(series, benchmark) if benchmark is not None else None
        ),
    )


def slice_time_series(
    series: NormalizedTimeSeries,
    *,
    start: datetime | None = None,
    end: datetime | None = None,
) -> NormalizedTimeSeries:
    if start is not None and start.tzinfo is None or end is not None and end.tzinfo is None:
        raise ValueError("time-series range boundaries must be timezone-aware")
    if start is not None and end is not None and start > end:
        raise ValueError("time-series start must not exceed end")
    if end is not None and end > series.as_of:
        raise ValueError("time-series end must not exceed snapshot as_of")
    bars = tuple(
        bar
        for bar in series.bars
        if (start is None or bar.timestamp >= start) and (end is None or bar.timestamp <= end)
    )
    if not bars:
        raise TimeSeriesUnavailable("no time-series observations in the requested window")
    return NormalizedTimeSeries.model_validate(
        {**series.model_dump(mode="python"), "bars": bars}
    )


class TimeSeriesSnapshotService:
    def __init__(
        self,
        repository: PlatformRepository,
        artifacts: ArtifactService,
    ):
        self.repository = repository
        self.artifacts = artifacts

    def persist(
        self,
        *,
        owner_id: UUID,
        series: NormalizedTimeSeries,
        vendor: str,
        retrieved_at: datetime,
        snapshot_id: UUID | None = None,
    ) -> SnapshotManifest:
        payload = json.dumps(
            series.model_dump(mode="json"),
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        if retrieved_at.tzinfo is None:
            raise ValueError("retrieved_at must be timezone-aware")
        content_hash = "sha256:" + hashlib.sha256(payload).hexdigest()
        manifest = SnapshotManifest(
            snapshot_id=snapshot_id or uuid4(),
            instrument_id=series.instrument_id,
            dataset=series.dataset,
            vendor=vendor,
            as_of=series.as_of,
            retrieved_at=retrieved_at.astimezone(UTC),
            source_start=series.bars[0].timestamp,
            source_end=series.bars[-1].timestamp,
            content_hash=content_hash,
            quality_status=DataQualityStatus.OK,
            metadata={
                "interval": series.interval.value,
                "timezone": series.timezone,
                "quote_currency": series.quote_currency,
                "observations": len(series.bars),
                "price_basis": series.price_basis.value,
            },
        )
        self.repository.add_snapshot(manifest)
        existing_artifact = self.repository.get_snapshot_artifact(
            manifest.snapshot_id, owner_id
        )
        if existing_artifact is not None:
            if existing_artifact.content_hash != manifest.content_hash:
                raise ImmutableRecordConflict(
                    "snapshot artifact already has different content"
                )
            return manifest
        self.artifacts.create(
            owner_id=owner_id,
            kind=ArtifactKind.SNAPSHOT_PAYLOAD,
            media_type="application/vnd.tradingagents.timeseries+json",
            content=payload,
            instrument_id=series.instrument_id,
            snapshot_id=manifest.snapshot_id,
            created_at=retrieved_at,
            expected_hash=manifest.content_hash,
        )
        return manifest

    def load(
        self,
        *,
        owner_id: UUID,
        instrument_id: UUID,
        dataset: str,
        as_of: datetime,
    ) -> tuple[SnapshotManifest, NormalizedTimeSeries]:
        snapshot = self.repository.latest_snapshot(
            instrument_id=instrument_id,
            dataset=dataset,
            as_of=as_of,
        )
        if snapshot is None:
            raise TimeSeriesUnavailable("no eligible time-series snapshot")
        artifact = self.repository.get_snapshot_artifact(snapshot.snapshot_id, owner_id)
        if artifact is None:
            raise TimeSeriesUnavailable("time-series snapshot payload is unavailable")
        loaded = self.artifacts.read(artifact.artifact_id, owner_id)
        if loaded is None:
            raise TimeSeriesUnavailable("time-series snapshot payload is unavailable")
        _manifest, payload = loaded
        series = NormalizedTimeSeries.model_validate_json(payload)
        if series.instrument_id != instrument_id or series.dataset != dataset:
            raise ValueError("time-series payload identity does not match its snapshot")
        return snapshot, series
