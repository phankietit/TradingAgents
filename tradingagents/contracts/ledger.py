"""Immutable, broker-neutral portfolio ledger events."""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import AwareDatetime, Field, model_validator

from .base import NonEmptyText, VersionedContract


class LedgerTransactionType(str, Enum):
    CASH_DEPOSIT = "cash_deposit"
    CASH_WITHDRAWAL = "cash_withdrawal"
    BUY = "buy"
    SELL = "sell"
    DIVIDEND = "dividend"
    FEE = "fee"


class LedgerTransaction(VersionedContract):
    transaction_id: UUID
    ledger_id: UUID
    owner_id: UUID
    occurred_at: AwareDatetime
    transaction_type: LedgerTransactionType
    currency: NonEmptyText
    instrument_id: UUID | None = None
    quantity: Decimal | None = Field(default=None, gt=0)
    unit_price: Decimal | None = Field(default=None, ge=0)
    cash_amount: Decimal | None = Field(default=None, gt=0)
    fee_amount: Decimal = Field(default=Decimal("0"), ge=0)
    external_reference: str | None = Field(default=None, min_length=1, max_length=128)

    @model_validator(mode="after")
    def validate_transaction_shape(self):
        trade = self.transaction_type in {
            LedgerTransactionType.BUY,
            LedgerTransactionType.SELL,
        }
        if trade and (
            self.instrument_id is None or self.quantity is None or self.unit_price is None
        ):
            raise ValueError("buy/sell transactions require instrument, quantity, and unit_price")
        if (
            not trade
            and self.transaction_type is not LedgerTransactionType.DIVIDEND
            and (
                self.instrument_id is not None
                or self.quantity is not None
                or self.unit_price is not None
            )
        ):
            raise ValueError("cash-only transactions cannot include trade fields")
        if self.transaction_type is LedgerTransactionType.DIVIDEND and self.cash_amount is None:
            raise ValueError("dividend requires cash_amount")
        cash_only = {
            LedgerTransactionType.CASH_DEPOSIT,
            LedgerTransactionType.CASH_WITHDRAWAL,
            LedgerTransactionType.FEE,
        }
        if self.transaction_type in cash_only and self.cash_amount is None:
            raise ValueError("cash transaction requires cash_amount")
        if trade and self.cash_amount is not None:
            raise ValueError("trade cash value is derived from quantity and unit_price")
        return self
