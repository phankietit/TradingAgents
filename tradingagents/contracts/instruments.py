"""Canonical instrument identity and tradability contracts."""

from __future__ import annotations

import unicodedata
from enum import Enum
from typing import Annotated
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


InstrumentAliasText = Annotated[str, Field(min_length=1, max_length=128)]
InstrumentAliasNamespace = Annotated[
    str,
    Field(min_length=1, max_length=32, pattern=r"^[a-z0-9][a-z0-9_.-]*$"),
]


def normalize_instrument_alias(value: str) -> str:
    """Return the stable lookup key used by the instrument master."""

    normalized = unicodedata.normalize("NFKC", value).strip().casefold()
    if not normalized:
        raise ValueError("instrument alias must not be empty")
    if any(unicodedata.category(character).startswith("C") for character in normalized):
        raise ValueError("instrument alias must not contain control characters")
    if len(normalized) > 128:
        raise ValueError("instrument alias must not exceed 128 characters")
    return normalized


class InstrumentAliasContract(VersionedContract):
    instrument_id: UUID
    namespace: InstrumentAliasNamespace
    alias: InstrumentAliasText
    normalized_alias: InstrumentAliasText

    @model_validator(mode="after")
    def normalized_key_matches_alias(self):
        if self.normalized_alias != normalize_instrument_alias(self.alias):
            raise ValueError("normalized_alias must match the normalized alias")
        return self

    @classmethod
    def create(
        cls,
        *,
        instrument_id: UUID,
        namespace: str,
        alias: str,
    ) -> InstrumentAliasContract:
        return cls(
            instrument_id=instrument_id,
            namespace=namespace,
            alias=alias,
            normalized_alias=normalize_instrument_alias(alias),
        )


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
