"""Replay immutable transactions into a long-only portfolio valuation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid5

from tradingagents._compat import UTC
from tradingagents.contracts import (
    CashBalance,
    DataQualityStatus,
    LedgerTransaction,
    LedgerTransactionType,
    PortfolioSnapshot,
    PositionSnapshot,
)
from tradingagents.contracts.ledger import ValuationQuote


@dataclass
class _Position:
    quantity: Decimal = Decimal("0")
    cost: Decimal = Decimal("0")


class PortfolioLedger:
    """Pure replay engine; it neither connects to a broker nor creates orders."""

    def replay(
        self,
        *,
        ledger_id: UUID,
        owner_id: UUID,
        base_currency: str,
        transactions: tuple[LedgerTransaction, ...],
        prices: dict[UUID, ValuationQuote],
        as_of: datetime,
        max_price_age: timedelta | None = None,
    ) -> PortfolioSnapshot:
        if as_of.tzinfo is None or as_of.utcoffset() is None:
            raise ValueError("ledger as_of requires timezone")
        as_of = as_of.astimezone(UTC)
        if max_price_age is not None and max_price_age < timedelta(0):
            raise ValueError("max_price_age must be nonnegative")
        transactions = tuple(LedgerTransaction.model_validate(item.model_dump()) for item in transactions)
        prices = {key: ValuationQuote.model_validate(value.model_dump() if isinstance(value, ValuationQuote) else value) for key, value in prices.items()}
        cash = Decimal("0")
        realized = Decimal("0")
        positions: dict[UUID, _Position] = {}
        seen: set[UUID] = set()
        ordered = sorted(transactions, key=lambda item: (item.occurred_at, item.sequence))
        ordering_keys = [(item.occurred_at, item.sequence) for item in ordered]
        if len(ordering_keys) != len(set(ordering_keys)):
            raise ValueError("ambiguous transaction order; set distinct sequence for simultaneous events")
        for entry in ordered:
            if entry.transaction_id in seen:
                raise ValueError("duplicate ledger transaction")
            seen.add(entry.transaction_id)
            if entry.ledger_id != ledger_id or entry.owner_id != owner_id:
                raise ValueError("transaction does not belong to this owner ledger")
            if entry.currency != base_currency:
                raise ValueError("multi-currency valuation requires an explicit FX contract")
            if entry.occurred_at > as_of:
                continue
            kind = entry.transaction_type
            if kind is LedgerTransactionType.CASH_DEPOSIT:
                cash += entry.cash_amount
            elif kind in {LedgerTransactionType.CASH_WITHDRAWAL, LedgerTransactionType.FEE}:
                cash -= entry.cash_amount
                if kind is LedgerTransactionType.FEE:
                    realized -= entry.cash_amount
            elif kind is LedgerTransactionType.DIVIDEND:
                cash += entry.cash_amount
                realized += entry.cash_amount
            else:
                position = positions.setdefault(entry.instrument_id, _Position())
                notional = entry.quantity * entry.unit_price
                if kind is LedgerTransactionType.BUY:
                    cash -= notional + entry.fee_amount
                    position.quantity += entry.quantity
                    position.cost += notional + entry.fee_amount
                else:
                    if entry.quantity > position.quantity:
                        raise ValueError("sell would create a short position")
                    average = position.cost / position.quantity
                    cash += notional - entry.fee_amount
                    realized += (entry.unit_price - average) * entry.quantity - entry.fee_amount
                    position.quantity -= entry.quantity
                    position.cost -= average * entry.quantity
            if cash < 0:
                raise ValueError("ledger cash cannot become negative")

        values: dict[UUID, Decimal] = {}
        unrealized = Decimal("0")
        for instrument_id, position in positions.items():
            if position.quantity == 0:
                continue
            if instrument_id not in prices:
                raise ValueError(f"missing valuation price for {instrument_id}")
            quote = ValuationQuote.model_validate(prices[instrument_id])
            if quote.instrument_id != instrument_id or quote.currency != base_currency:
                raise ValueError("valuation quote identity/currency mismatch")
            if (quote.quality_status is not DataQualityStatus.OK or quote.source_at > as_of
                    or quote.observed_at < quote.source_at or quote.observed_at > as_of):
                raise ValueError("valuation quote is not point-in-time eligible")
            if max_price_age is None or as_of - quote.source_at > max_price_age:
                raise ValueError("valuation requires an explicit freshness limit and fresh prices")
            values[instrument_id] = position.quantity * quote.price
            unrealized += values[instrument_id] - position.cost
        nav = cash + sum(values.values(), Decimal("0"))
        position_snapshots = tuple(
            PositionSnapshot(
                instrument_id=instrument_id,
                quantity=positions[instrument_id].quantity,
                average_price=positions[instrument_id].cost / positions[instrument_id].quantity,
                market_price=prices[instrument_id].price,
                market_value=value,
                weight=float(value / nav) if nav else 0.0,
            )
            for instrument_id, value in sorted(values.items(), key=lambda item: str(item[0]))
        )
        canonical = {
            "ledger_id": str(ledger_id),
            "owner_id": str(owner_id),
            "as_of": as_of.isoformat(),
            "base_currency": base_currency,
            "max_price_age_seconds": max_price_age.total_seconds() if max_price_age is not None else None,
            "transactions": [item.model_dump(mode="json") for item in ordered if item.occurred_at <= as_of],
            "prices": {str(key): prices[key].model_dump(mode="json") for key in sorted(values, key=str)},
        }
        digest = hashlib.sha256(json.dumps(canonical, sort_keys=True).encode()).hexdigest()
        return PortfolioSnapshot(
            portfolio_id=uuid5(ledger_id, digest),
            owner_id=owner_id,
            as_of=as_of,
            base_currency=base_currency,
            cash=(CashBalance(currency=base_currency, amount=cash),),
            positions=position_snapshots,
            net_asset_value=nav,
            realized_pnl=realized,
            unrealized_pnl=unrealized,
            content_hash=f"sha256:{digest}",
        )
