"""Compute reproducible momentum, trend, risk, relative, and breadth factors."""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from datetime import datetime
from uuid import NAMESPACE_URL, UUID, uuid5

from tradingagents.contracts import (
    ArtifactKind,
    DataQualityStatus,
    DerivedFactorSnapshot,
    FactorSeriesInput,
    FactorWindowConfig,
    InstrumentFactors,
    MarketBreadth,
    NormalizedTimeSeries,
    PriceBasis,
)
from tradingagents.platform.artifacts import ArtifactService


class InsufficientFactorCoverage(ValueError):
    """A factor cannot be calculated without the configured observation window."""


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _price_series(series: NormalizedTimeSeries) -> list[tuple[datetime, float]]:
    adjusted = series.price_basis is PriceBasis.ADJUSTED_CLOSE
    return [
        (
            bar.timestamp,
            bar.adjusted_close if adjusted else bar.close,
        )
        for bar in series.bars
    ]


def _simple_returns(prices: list[float]) -> list[float]:
    return [
        current / previous - 1
        for previous, current in zip(prices, prices[1:], strict=False)
    ]


class DerivedFactorService:
    def __init__(self, artifacts: ArtifactService | None = None):
        self.artifacts = artifacts

    def compute(
        self,
        *,
        members: tuple[FactorSeriesInput, ...],
        benchmark: FactorSeriesInput,
        config: FactorWindowConfig,
        as_of: datetime,
        generated_at: datetime,
    ) -> DerivedFactorSnapshot:
        ordered = tuple(sorted(members, key=lambda item: item.canonical_symbol.casefold()))
        self._validate_sources(ordered, benchmark, as_of)
        factors = tuple(
            self._instrument_factors(member, benchmark, config) for member in ordered
        )
        positive = sum(item.positive_momentum for item in factors)
        above = sum(item.above_slow_trend for item in factors)
        breadth = MarketBreadth(
            member_count=len(factors),
            positive_momentum_count=positive,
            above_slow_trend_count=above,
            positive_momentum_ratio=positive / len(factors),
            above_slow_trend_ratio=above / len(factors),
        )
        input_hash = "sha256:" + hashlib.sha256(
            _canonical_bytes(
                {
                    "as_of": as_of.isoformat(),
                    "generated_at": generated_at.isoformat(),
                    "config": config.model_dump(mode="json"),
                    "benchmark": benchmark.model_dump(mode="json"),
                    "members": [item.model_dump(mode="json") for item in ordered],
                }
            )
        ).hexdigest()
        return DerivedFactorSnapshot(
            factor_snapshot_id=uuid5(NAMESPACE_URL, input_hash),
            as_of=as_of,
            generated_at=generated_at,
            config=config,
            benchmark_instrument_id=benchmark.series.instrument_id,
            benchmark_snapshot_id=benchmark.snapshot_id,
            input_hash=input_hash,
            factors=factors,
            breadth=breadth,
        )

    def persist(self, *, owner_id: UUID, snapshot: DerivedFactorSnapshot):
        artifacts = self._require_artifacts()
        return artifacts.create(
            owner_id=owner_id,
            kind=ArtifactKind.DERIVED_FACTOR_SNAPSHOT,
            media_type="application/vnd.tradingagents.derived-factors+json",
            content=_canonical_bytes(snapshot.model_dump(mode="json")),
            artifact_id=snapshot.factor_snapshot_id,
            created_at=snapshot.generated_at,
        )

    def load(self, *, owner_id: UUID, factor_snapshot_id: UUID) -> DerivedFactorSnapshot:
        loaded = self._require_artifacts().read(factor_snapshot_id, owner_id)
        if loaded is None:
            raise LookupError("derived factor snapshot is unavailable")
        manifest, payload = loaded
        if manifest.kind is not ArtifactKind.DERIVED_FACTOR_SNAPSHOT:
            raise ValueError("artifact is not a derived factor snapshot")
        snapshot = DerivedFactorSnapshot.model_validate_json(payload)
        if snapshot.factor_snapshot_id != factor_snapshot_id:
            raise ValueError("factor payload identity does not match its artifact")
        return snapshot

    def _require_artifacts(self) -> ArtifactService:
        if self.artifacts is None:
            raise RuntimeError("artifact service is required for persistence")
        return self.artifacts

    @staticmethod
    def _validate_sources(
        members: tuple[FactorSeriesInput, ...],
        benchmark: FactorSeriesInput,
        as_of: datetime,
    ) -> None:
        if not members:
            raise ValueError("at least one factor member is required")
        ids = [item.series.instrument_id for item in members]
        symbols = [item.canonical_symbol.casefold() for item in members]
        if len(ids) != len(set(ids)) or len(symbols) != len(set(symbols)):
            raise ValueError("factor members must have unique instruments and symbols")
        sources = (*members, benchmark)
        if any(item.quality_status is not DataQualityStatus.OK for item in sources):
            raise ValueError("derived factors require OK source quality")
        if any(item.series.as_of > as_of for item in sources):
            raise ValueError("factor sources must be observable by as_of")
        if any(item.series.interval is not benchmark.series.interval for item in members):
            raise ValueError("factor members and benchmark must use the same interval")
        if any(
            item.series.quote_currency != benchmark.series.quote_currency
            for item in members
        ):
            raise ValueError("factor members and benchmark must use the same quote currency")

    @staticmethod
    def _instrument_factors(
        member: FactorSeriesInput,
        benchmark: FactorSeriesInput,
        config: FactorWindowConfig,
    ) -> InstrumentFactors:
        member_points = _price_series(member.series)
        minimum = max(
            config.momentum_periods + 1,
            config.trend_slow_periods,
            config.volatility_periods + 1,
        )
        if len(member_points) < minimum:
            raise InsufficientFactorCoverage(
                f"{member.canonical_symbol} requires at least {minimum} observations"
            )
        prices = [price for _timestamp, price in member_points]
        momentum = prices[-1] / prices[-config.momentum_periods - 1] - 1
        fast_average = statistics.fmean(prices[-config.trend_fast_periods :])
        slow_average = statistics.fmean(prices[-config.trend_slow_periods :])
        volatility_returns = _simple_returns(
            prices[-config.volatility_periods - 1 :]
        )
        annualized_volatility = statistics.stdev(volatility_returns) * math.sqrt(
            member.series.annualization_periods
        )

        benchmark_by_time = dict(_price_series(benchmark.series))
        aligned = [
            (timestamp, price, benchmark_by_time[timestamp])
            for timestamp, price in member_points
            if timestamp in benchmark_by_time
        ]
        required_aligned = max(
            config.momentum_periods + 1, config.correlation_periods + 1
        )
        if len(aligned) < required_aligned:
            raise InsufficientFactorCoverage(
                f"{member.canonical_symbol} and benchmark require at least "
                f"{required_aligned} aligned observations"
            )
        momentum_aligned = aligned[-config.momentum_periods - 1 :]
        relative_strength = momentum_aligned[-1][1] / momentum_aligned[0][1] - (
            momentum_aligned[-1][2] / momentum_aligned[0][2]
        )
        correlation_aligned = aligned[-config.correlation_periods - 1 :]
        asset_returns = _simple_returns([item[1] for item in correlation_aligned])
        benchmark_returns = _simple_returns([item[2] for item in correlation_aligned])
        correlation = None
        if statistics.pstdev(asset_returns) > 0 and statistics.pstdev(
            benchmark_returns
        ) > 0:
            correlation = statistics.correlation(asset_returns, benchmark_returns)
        return InstrumentFactors(
            instrument_id=member.series.instrument_id,
            canonical_symbol=member.canonical_symbol,
            source_snapshot_id=member.snapshot_id,
            momentum=momentum,
            trend_fast_vs_slow=fast_average / slow_average - 1,
            trend_price_vs_slow=prices[-1] / slow_average - 1,
            annualized_volatility=annualized_volatility,
            relative_strength=relative_strength,
            benchmark_correlation=correlation,
            positive_momentum=momentum > 0,
            above_slow_trend=prices[-1] > slow_average,
        )
