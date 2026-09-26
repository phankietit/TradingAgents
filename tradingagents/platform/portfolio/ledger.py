"""Replay immutable transactions into a long-only portfolio valuation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID, uuid4

from tradingagents.contracts import (
    CashBalance,
    LedgerTransaction,
    LedgerTransactionType,
    PortfolioSnapshot,
    PositionSnapshot,
)


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
        prices: dict[UUID, Decimal],
        as_of,
    ) -> PortfolioSnapshot:
        cash = Decimal("0")
        realized = Decimal("0")
        positions: dict[UUID, _Position] = {}
        seen: set[UUID] = set()
        ordered = sorted(transactions, key=lambda item: (item.occurred_at, str(item.transaction_id)))
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
            values[instrument_id] = position.quantity * prices[instrument_id]
            unrealized += values[instrument_id] - position.cost
        nav = cash + sum(values.values(), Decimal("0"))
        position_snapshots = tuple(
            PositionSnapshot(
                instrument_id=instrument_id,
                quantity=positions[instrument_id].quantity,
                average_price=positions[instrument_id].cost / positions[instrument_id].quantity,
                market_price=prices[instrument_id],
                market_value=value,
                weight=float(value / nav) if nav else 0.0,
            )
            for instrument_id, value in sorted(values.items(), key=lambda item: str(item[0]))
        )
        canonical = {
            "ledger_id": str(ledger_id),
            "owner_id": str(owner_id),
            "as_of": as_of.isoformat(),
            "transactions": [str(item.transaction_id) for item in ordered if item.occurred_at <= as_of],
            "prices": {str(key): str(value) for key, value in sorted(prices.items(), key=lambda item: str(item[0]))},
        }
        digest = hashlib.sha256(json.dumps(canonical, sort_keys=True).encode()).hexdigest()
        return PortfolioSnapshot(
            portfolio_id=uuid4(),
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
