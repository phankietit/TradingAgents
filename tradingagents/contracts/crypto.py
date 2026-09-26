"""Large-cap crypto snapshot, venue coverage, and quality contracts."""

from __future__ import annotations

from uuid import UUID

from pydantic import AwareDatetime, Field, FiniteFloat, model_validator

from .base import NonEmptyText, StrictContract, VersionedContract
from .data import DataQualityStatus
from .timeseries import BenchmarkComparison, TimeSeriesStatistics


class CryptoVenueObservation(StrictContract):
    venue: NonEmptyText
    base_asset: NonEmptyText
    quote_asset: NonEmptyText
    observed_at: AwareDatetime
    last_price: FiniteFloat = Field(gt=0)
    bid: FiniteFloat = Field(gt=0)
    ask: FiniteFloat = Field(gt=0)
    quote_volume_24h: FiniteFloat = Field(ge=0)
    vendor: NonEmptyText

    @model_validator(mode="after")
    def validate_market(self):
        if self.ask < self.bid:
            raise ValueError("crypto ask must not be below bid")
        return self


class CryptoQualityThresholds(VersionedContract):
    min_venues: int = Field(default=2, ge=1, le=100)
    min_aggregate_quote_volume_24h: FiniteFloat = Field(default=1_000_000, ge=0)
    max_median_spread_bps: FiniteFloat = Field(default=100, gt=0)
    max_observation_age_seconds: int = Field(default=900, ge=1, le=86_400)


class CryptoLiquidityMetrics(StrictContract):
    observed_venues: int = Field(ge=0)
    excluded_future_observations: int = Field(ge=0)
    aggregate_quote_volume_24h: FiniteFloat = Field(ge=0)
    median_spread_bps: FiniteFloat | None = Field(default=None, ge=0)
    oldest_observation_age_seconds: FiniteFloat | None = Field(default=None, ge=0)


class CryptoSnapshot(VersionedContract):
    crypto_snapshot_id: UUID
    instrument_id: UUID
    canonical_symbol: NonEmptyText
    as_of: AwareDatetime
    retrieved_at: AwareDatetime
    price_snapshot_id: UUID
    benchmark_price_snapshot_id: UUID | None = None
    venues: tuple[CryptoVenueObservation, ...]
    thresholds: CryptoQualityThresholds
    liquidity: CryptoLiquidityMetrics
    price_statistics: TimeSeriesStatistics
    benchmark: BenchmarkComparison | None = None
    quality_status: DataQualityStatus
    quality_reasons: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_crypto_boundary(self):
        if self.canonical_symbol not in {"BTC-USD", "ETH-USD"}:
            raise ValueError("initial crypto snapshots are limited to BTC and ETH")
        if self.retrieved_at < self.as_of:
            raise ValueError("retrieved_at must not precede as_of")
        if any(item.observed_at > self.as_of for item in self.venues):
            raise ValueError("crypto venue observations must not exceed as_of")
        venue_names = [item.venue.casefold() for item in self.venues]
        if len(venue_names) != len(set(venue_names)):
            raise ValueError("crypto venue observations must use unique venues")
        if self.canonical_symbol == "ETH-USD" and (
            self.benchmark_price_snapshot_id is None or self.benchmark is None
        ):
            raise ValueError("ETH snapshots require a BTC benchmark")
        if self.canonical_symbol == "BTC-USD" and (
            self.benchmark_price_snapshot_id is not None or self.benchmark is not None
        ):
            raise ValueError("BTC is the crypto benchmark and must not benchmark itself")
        return self
