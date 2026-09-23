"""Owner-private portfolio snapshot contracts."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import AwareDatetime, Field, model_validator

from .base import ContentHash, NonEmptyText, StrictContract, VersionedContract, Weight


class CashBalance(StrictContract):
    currency: NonEmptyText
    amount: Decimal = Field(ge=0)


class PositionSnapshot(StrictContract):
    instrument_id: UUID
    quantity: Decimal = Field(ge=0)
    average_price: Decimal | None = Field(default=None, ge=0)
    market_price: Decimal = Field(ge=0)
    market_value: Decimal = Field(ge=0)
    weight: Weight


class PortfolioSnapshot(VersionedContract):
    portfolio_id: UUID
    owner_id: UUID
    as_of: AwareDatetime
    base_currency: NonEmptyText
    cash: tuple[CashBalance, ...]
    positions: tuple[PositionSnapshot, ...]
    net_asset_value: Decimal = Field(ge=0)
    content_hash: ContentHash

    @model_validator(mode="after")
    def validate_unique_positions(self):
        instrument_ids = [position.instrument_id for position in self.positions]
        if len(instrument_ids) != len(set(instrument_ids)):
            raise ValueError("portfolio positions must have unique instrument_id values")
        return self
