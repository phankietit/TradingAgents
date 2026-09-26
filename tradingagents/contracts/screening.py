"""Deterministic, point-in-time stock-universe screening contracts."""

from __future__ import annotations

import hashlib
import json
from enum import Enum
from uuid import NAMESPACE_URL, UUID, uuid5

from pydantic import AwareDatetime, Field, FiniteFloat, model_validator

from .base import ContentHash, NonEmptyText, StrictContract, VersionedContract
from .data import DataQualityStatus
from .instruments import InstrumentContract


class ScreeningExclusionCode(str, Enum):
    NON_EQUITY = "non_equity"
    NOT_INVESTABLE = "not_investable"
    VENUE_NOT_ALLOWED = "venue_not_allowed"
    CURRENCY_NOT_ALLOWED = "currency_not_allowed"
    DATA_QUALITY = "data_quality"
    MARKET_CAP = "market_cap"
    LIQUIDITY = "liquidity"
    PRICE = "price"
    HISTORY = "history"
    VOLATILITY = "volatility"
    OUTSIDE_LIMIT = "outside_limit"


class StockScreenerPolicy(VersionedContract):
    policy_id: NonEmptyText
    allowed_venues: tuple[NonEmptyText, ...] = ("NASDAQ", "NYSE")
    quote_currency: NonEmptyText = "USD"
    min_market_cap_usd: FiniteFloat = Field(default=10_000_000_000, ge=0)
    min_average_dollar_volume_20d_usd: FiniteFloat = Field(default=25_000_000, ge=0)
    min_last_price_usd: FiniteFloat = Field(default=5, gt=0)
    min_history_days: int = Field(default=252, ge=1)
    max_annualized_volatility: FiniteFloat = Field(default=1.5, gt=0)
    max_candidates: int = Field(default=50, ge=1, le=500)
    market_cap_rank_weight: int = Field(default=1, ge=0, le=100)
    liquidity_rank_weight: int = Field(default=1, ge=0, le=100)

    @model_validator(mode="after")
    def validate_policy(self):
        normalized = tuple(venue.upper() for venue in self.allowed_venues)
        if not normalized or len(normalized) != len(set(normalized)):
            raise ValueError("allowed_venues must be non-empty and unique")
        if self.allowed_venues != normalized or normalized != tuple(sorted(normalized)):
            raise ValueError("allowed_venues must be uppercase and sorted")
        if self.quote_currency != self.quote_currency.upper():
            raise ValueError("quote_currency must be uppercase")
        if self.market_cap_rank_weight + self.liquidity_rank_weight == 0:
            raise ValueError("at least one ranking weight must be positive")
        return self


class StockScreeningInput(StrictContract):
    instrument: InstrumentContract
    observed_at: AwareDatetime
    source_snapshot_id: UUID
    source_content_hash: ContentHash
    market_cap_usd: FiniteFloat = Field(ge=0)
    average_dollar_volume_20d_usd: FiniteFloat = Field(ge=0)
    last_price_usd: FiniteFloat = Field(gt=0)
    history_days: int = Field(ge=0)
    annualized_volatility: FiniteFloat = Field(ge=0)
    quality_status: DataQualityStatus


class ScreenedStock(StrictContract):
    rank: int = Field(ge=1)
    instrument_id: UUID
    canonical_symbol: NonEmptyText
    source_snapshot_id: UUID
    market_cap_usd: FiniteFloat = Field(ge=0)
    average_dollar_volume_20d_usd: FiniteFloat = Field(ge=0)
    annualized_volatility: FiniteFloat = Field(ge=0)
    market_cap_rank: int = Field(ge=1)
    liquidity_rank: int = Field(ge=1)
    ranking_score: int = Field(ge=0)


class StockScreeningExclusion(StrictContract):
    instrument_id: UUID
    canonical_symbol: NonEmptyText
    codes: tuple[ScreeningExclusionCode, ...] = Field(min_length=1)
    reasons: tuple[NonEmptyText, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_reasons(self):
        if len(self.codes) != len(self.reasons):
            raise ValueError("each exclusion code requires one reason")
        if len(self.codes) != len(set(self.codes)):
            raise ValueError("exclusion codes must be unique")
        return self


class StockUniverseSnapshot(VersionedContract):
    screening_snapshot_id: UUID
    as_of: AwareDatetime
    generated_at: AwareDatetime
    policy: StockScreenerPolicy
    input_count: int = Field(ge=0)
    input_hash: ContentHash
    universe_hash: ContentHash
    candidates: tuple[ScreenedStock, ...]
    exclusions: tuple[StockScreeningExclusion, ...]

    @model_validator(mode="after")
    def validate_snapshot(self):
        if self.generated_at < self.as_of:
            raise ValueError("generated_at must not precede as_of")
        if self.input_count != len(self.candidates) + len(self.exclusions):
            raise ValueError("every screening input must be selected or excluded")
        if tuple(item.rank for item in self.candidates) != tuple(
            range(1, len(self.candidates) + 1)
        ):
            raise ValueError("candidate ranks must be contiguous and ordered")
        identities = [
            item.instrument_id for item in (*self.candidates, *self.exclusions)
        ]
        if len(identities) != len(set(identities)):
            raise ValueError("screening results must have unique instruments")
        material = {
            "input_hash": self.input_hash,
            "generated_at": self.generated_at.isoformat(),
            "candidates": [item.model_dump(mode="json") for item in self.candidates],
            "exclusions": [item.model_dump(mode="json") for item in self.exclusions],
        }
        encoded = json.dumps(
            material,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        expected_hash = "sha256:" + hashlib.sha256(encoded).hexdigest()
        if self.universe_hash != expected_hash:
            raise ValueError("universe_hash does not match the screening results")
        if self.screening_snapshot_id != uuid5(NAMESPACE_URL, self.universe_hash):
            raise ValueError("screening_snapshot_id must be derived from universe_hash")
        return self
