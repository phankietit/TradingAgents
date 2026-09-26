"""Deterministic derived-factor and market-breadth contracts."""

from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

from pydantic import AwareDatetime, Field, FiniteFloat, model_validator

from .base import ContentHash, NonEmptyText, StrictContract, VersionedContract
from .data import DataQualityStatus
from .timeseries import NormalizedTimeSeries


class FactorWindowConfig(VersionedContract):
    config_id: NonEmptyText
    momentum_periods: int = Field(default=63, ge=1, le=10_000)
    trend_fast_periods: int = Field(default=50, ge=1, le=10_000)
    trend_slow_periods: int = Field(default=200, ge=2, le=10_000)
    volatility_periods: int = Field(default=63, ge=2, le=10_000)
    correlation_periods: int = Field(default=63, ge=2, le=10_000)

    @model_validator(mode="after")
    def validate_windows(self):
        if self.trend_fast_periods >= self.trend_slow_periods:
            raise ValueError("trend_fast_periods must be below trend_slow_periods")
        return self


class FactorSeriesInput(StrictContract):
    canonical_symbol: NonEmptyText
    snapshot_id: UUID
    content_hash: ContentHash
    quality_status: DataQualityStatus
    series: NormalizedTimeSeries


class InstrumentFactors(StrictContract):
    instrument_id: UUID
    canonical_symbol: NonEmptyText
    source_snapshot_id: UUID
    momentum: FiniteFloat
    trend_fast_vs_slow: FiniteFloat
    trend_price_vs_slow: FiniteFloat
    annualized_volatility: FiniteFloat = Field(ge=0)
    relative_strength: FiniteFloat
    benchmark_correlation: FiniteFloat | None = Field(default=None, ge=-1, le=1)
    positive_momentum: bool
    above_slow_trend: bool


class MarketBreadth(StrictContract):
    member_count: int = Field(ge=1)
    positive_momentum_count: int = Field(ge=0)
    above_slow_trend_count: int = Field(ge=0)
    positive_momentum_ratio: FiniteFloat = Field(ge=0, le=1)
    above_slow_trend_ratio: FiniteFloat = Field(ge=0, le=1)

    @model_validator(mode="after")
    def validate_counts(self):
        if self.positive_momentum_count > self.member_count:
            raise ValueError("positive momentum count exceeds member count")
        if self.above_slow_trend_count > self.member_count:
            raise ValueError("above-trend count exceeds member count")
        return self


class DerivedFactorSnapshot(VersionedContract):
    factor_snapshot_id: UUID
    as_of: AwareDatetime
    generated_at: AwareDatetime
    config: FactorWindowConfig
    benchmark_instrument_id: UUID
    benchmark_snapshot_id: UUID
    input_hash: ContentHash
    factors: tuple[InstrumentFactors, ...] = Field(min_length=1)
    breadth: MarketBreadth

    @model_validator(mode="after")
    def validate_snapshot(self):
        if self.generated_at < self.as_of:
            raise ValueError("generated_at must not precede as_of")
        if len(self.factors) != self.breadth.member_count:
            raise ValueError("breadth must cover every factor member")
        symbols = [item.canonical_symbol.casefold() for item in self.factors]
        if symbols != sorted(symbols) or len(symbols) != len(set(symbols)):
            raise ValueError("factor members must have sorted unique symbols")
        if self.factor_snapshot_id != uuid5(NAMESPACE_URL, self.input_hash):
            raise ValueError("factor_snapshot_id must be derived from input_hash")
        return self
