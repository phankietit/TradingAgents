"""Canonical instrument identity and tradability contracts."""

from __future__ import annotations

from enum import Enum
from uuid import UUID

from pydantic import Field, model_validator

from .base import NonEmptyText, VersionedContract


class AssetClass(str, Enum):
    EQUITY = "equity"
    ETF = "etf"
    CASH_INDEX = "cash_index"
    REFERENCE_FUTURE = "reference_future"
    CRYPTO = "crypto"


class Tradability(str, Enum):
    INVESTABLE = "investable"
    REFERENCE_ONLY = "reference_only"


class InstrumentContract(VersionedContract):
    instrument_id: UUID
    symbol: NonEmptyText
    canonical_symbol: NonEmptyText
    display_name: NonEmptyText
    asset_class: AssetClass
    tradability: Tradability
    venue: NonEmptyText
    quote_currency: NonEmptyText
    timezone: NonEmptyText
    session_calendar: NonEmptyText
    benchmark_symbol: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def enforce_asset_boundaries(self):
        if (
            self.asset_class in {AssetClass.CASH_INDEX, AssetClass.REFERENCE_FUTURE}
            and self.tradability is not Tradability.REFERENCE_ONLY
        ):
            raise ValueError("cash indices and reference futures must be reference_only")
        if self.asset_class is AssetClass.CRYPTO and self.timezone.upper() != "UTC":
            raise ValueError("crypto instruments must use UTC")
        return self
