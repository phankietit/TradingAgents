from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from tradingagents.contracts import LedgerTransaction, LedgerTransactionType
from tradingagents.platform.portfolio import PortfolioLedger

NOW = datetime(2026, 9, 25, tzinfo=UTC)


def _entry(kind, ledger_id, owner_id, **kwargs):
    return LedgerTransaction(
        transaction_id=uuid4(), ledger_id=ledger_id, owner_id=owner_id,
        occurred_at=kwargs.pop("occurred_at", NOW), transaction_type=kind,
        currency="USD", **kwargs,
    )


@pytest.mark.unit
def test_ledger_replays_cash_positions_nav_and_pnl():
    ledger_id, owner_id, instrument_id = uuid4(), uuid4(), uuid4()
    entries = (
        _entry(LedgerTransactionType.CASH_DEPOSIT, ledger_id, owner_id, cash_amount="1000"),
        _entry(LedgerTransactionType.BUY, ledger_id, owner_id, instrument_id=instrument_id,
               quantity="5", unit_price="100", fee_amount="2", occurred_at=NOW + timedelta(seconds=1)),
        _entry(LedgerTransactionType.SELL, ledger_id, owner_id, instrument_id=instrument_id,
               quantity="1", unit_price="120", fee_amount="1", occurred_at=NOW + timedelta(seconds=2)),
    )
    snapshot = PortfolioLedger().replay(
        ledger_id=ledger_id, owner_id=owner_id, base_currency="USD",
        transactions=entries, prices={instrument_id: Decimal("110")},
        as_of=NOW + timedelta(seconds=3),
    )
    assert snapshot.cash[0].amount == Decimal("617")
    assert snapshot.positions[0].quantity == Decimal("4")
    assert snapshot.net_asset_value == Decimal("1057")
    assert snapshot.realized_pnl == Decimal("18.6")
    assert snapshot.unrealized_pnl == Decimal("38.4")


@pytest.mark.unit
def test_ledger_rejects_negative_cash_and_short_position():
    ledger_id, owner_id, instrument_id = uuid4(), uuid4(), uuid4()
    buy = _entry(LedgerTransactionType.BUY, ledger_id, owner_id,
                 instrument_id=instrument_id, quantity="1", unit_price="10")
    with pytest.raises(ValueError, match="cash cannot become negative"):
        PortfolioLedger().replay(
            ledger_id=ledger_id, owner_id=owner_id, base_currency="USD",
            transactions=(buy,), prices={instrument_id: Decimal("10")}, as_of=NOW,
        )
