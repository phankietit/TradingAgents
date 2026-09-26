"""Normalized price time-series and deterministic metric contracts."""

from __future__ import annotations

from enum import Enum
from math import isfinite
from typing import Annotated
from uuid import UUID

from pydantic import AwareDatetime, Field, FiniteFloat, model_validator

from .base import NonEmptyText, StrictContract, VersionedContract

PositivePrice = Annotated[FiniteFloat, Field(gt=0)]


class PriceInterval(str, Enum):
    ONE_DAY = "1d"
    ONE_HOUR = "1h"
    FIFTEEN_MINUTES = "15m"
    FIVE_MINUTES = "5m"
    ONE_MINUTE = "1m"


class PriceBasis(str, Enum):
    CLOSE = "close"
    ADJUSTED_CLOSE = "adjusted_close"


class OHLCVBar(StrictContract):
    timestamp: AwareDatetime
    open: PositivePrice
    high: PositivePrice
    low: PositivePrice
    close: PositivePrice
    adjusted_close: PositivePrice | None = None
    volume: FiniteFloat = Field(ge=0)

    @model_validator(mode="after")
    def validate_price_envelope(self):
        if self.high < max(self.open, self.close, self.low):
            raise ValueError("high must be at least open, low, and close")
        if self.low > min(self.open, self.close, self.high):
            raise ValueError("low must be at most open, high, and close")
        if not all(
            isfinite(value)
            for value in (
                self.open,
                self.high,
                self.low,
                self.close,
                self.volume,
                self.adjusted_close if self.adjusted_close is not None else self.close,
            )
        ):
            raise ValueError("OHLCV values must be finite")
        return self


class NormalizedTimeSeries(VersionedContract):
    instrument_id: UUID
    dataset: NonEmptyText
    interval: PriceInterval
    timezone: NonEmptyText
    quote_currency: NonEmptyText
    as_of: AwareDatetime
    annualization_periods: int = Field(ge=1, le=1_000_000)
    bars: tuple[OHLCVBar, ...] = Field(min_length=1, max_length=100_000)

    @model_validator(mode="after")
    def validate_series(self):
        timestamps = [bar.timestamp for bar in self.bars]
        if timestamps != sorted(timestamps):
            raise ValueError("time-series bars must be sorted by timestamp")
        if len(timestamps) != len(set(timestamps)):
            raise ValueError("time-series bars must have unique timestamps")
        if timestamps[-1] > self.as_of:
            raise ValueError("time-series bars must not exceed as_of")
        adjusted = [bar.adjusted_close is not None for bar in self.bars]
        if any(adjusted) and not all(adjusted):
            raise ValueError("adjusted_close coverage must be complete or absent")
        return self

    @property
    def price_basis(self) -> PriceBasis:
        if self.bars[0].adjusted_close is not None:
            return PriceBasis.ADJUSTED_CLOSE
        return PriceBasis.CLOSE


class ReturnPoint(StrictContract):
    timestamp: AwareDatetime
    price: PositivePrice
    simple_return: FiniteFloat | None = None
    drawdown: FiniteFloat = Field(le=0)


class TimeSeriesStatistics(StrictContract):
    observations: int = Field(ge=1)
    price_basis: PriceBasis
    total_return: FiniteFloat
    annualized_volatility: FiniteFloat
    maximum_drawdown: FiniteFloat = Field(le=0)


class BenchmarkComparison(StrictContract):
    benchmark_instrument_id: UUID
    aligned_observations: int = Field(ge=2)
    asset_return: FiniteFloat
    benchmark_return: FiniteFloat
    excess_return: FiniteFloat
    correlation: FiniteFloat | None = Field(default=None, ge=-1, le=1)
    annualized_tracking_error: FiniteFloat


class TimeSeriesView(VersionedContract):
    series: NormalizedTimeSeries
    returns: tuple[ReturnPoint, ...]
    statistics: TimeSeriesStatistics
    benchmark: BenchmarkComparison | None = None
