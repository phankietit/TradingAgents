from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from tradingagents.contracts import LedgerTransaction, LedgerTransactionType
from tradingagents.contracts.ledger import ValuationQuote
from tradingagents.platform.portfolio import PortfolioLedger

NOW = datetime(2026, 9, 25, tzinfo=UTC)


def _quote(instrument, price="110", **changes):
    return ValuationQuote(**{
        "instrument_id": instrument, "currency": "USD", "price": price,
        "source_at": NOW, "observed_at": NOW, "snapshot_id": uuid4(),
        "content_hash": "sha256:" + "a" * 64, "quality_status": "OK", **changes,
    })


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
        transactions=entries, prices={instrument_id: _quote(instrument_id)}, max_price_age=timedelta(days=1),
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
            transactions=(buy,), prices={instrument_id: _quote(instrument_id, "10")}, as_of=NOW,
        )


def _book():
    ledger, owner, instrument = uuid4(), uuid4(), uuid4()
    entries = (
        _entry(LedgerTransactionType.CASH_DEPOSIT, ledger, owner, cash_amount="1000"),
        _entry(LedgerTransactionType.BUY, ledger, owner, instrument_id=instrument,
               quantity="5", unit_price="100", sequence=1),
    )
    return {"ledger_id": ledger, "owner_id": owner, "base_currency": "USD",
            "transactions": entries, "prices": {instrument: _quote(instrument)},
            "as_of": NOW, "max_price_age": timedelta(days=1)}


def test_replay_is_order_independent_and_hash_binds_event_values():
    args = _book()
    original = PortfolioLedger().replay(**args)
    assert PortfolioLedger().replay(**{**args, "transactions": tuple(reversed(args["transactions"]))}) == original
    deposit, buy = args["transactions"]
    changed = deposit.model_copy(update={"cash_amount": Decimal("1200")})
    updated = PortfolioLedger().replay(**{**args, "transactions": (changed, buy)})
    assert updated.content_hash != original.content_hash
    assert updated.portfolio_id != original.portfolio_id


@pytest.mark.parametrize("changes", [
    {"currency": "EUR"}, {"instrument_id": uuid4()},
    {"quality_status": "STALE"}, {"source_at": NOW + timedelta(days=1)},
    {"source_at": NOW - timedelta(days=2)},
])
def test_invalid_quote_cannot_value_a_portfolio(changes):
    args = _book()
    instrument = next(iter(args["prices"]))
    args["prices"] = {instrument: _quote(instrument, **changes)}
    with pytest.raises(ValueError):
        PortfolioLedger().replay(**args)


def test_same_time_requires_explicit_order_and_fee_affects_pnl():
    args = _book()
    deposit, buy = args["transactions"]
    with pytest.raises(ValueError, match="ambiguous"):
        PortfolioLedger().replay(**{**args, "transactions": (deposit, buy.model_copy(update={"sequence": 0}))})
    fee = _entry(LedgerTransactionType.FEE, args["ledger_id"], args["owner_id"], cash_amount="10", sequence=2)
    result = PortfolioLedger().replay(**{**args, "transactions": (deposit, buy, fee)})
    assert result.realized_pnl == -10
    assert result.net_asset_value == 1040


def test_future_transactions_do_not_change_historical_hash():
    args = _book()
    result = PortfolioLedger().replay(**args)
    future = _entry(LedgerTransactionType.CASH_DEPOSIT, args["ledger_id"], args["owner_id"],
                    cash_amount="1000", occurred_at=NOW + timedelta(days=1))
    assert PortfolioLedger().replay(**{**args, "transactions": (*args["transactions"], future)}) == result


def test_ledger_persistence_is_immutable_and_owner_scoped(tmp_path):
    from tradingagents.platform.persistence import (
        Database,
        ImmutableRecordConflict,
        PlatformRepository,
        upgrade_database,
    )

    url = f"sqlite:///{tmp_path / 'ledger.db'}"
    upgrade_database(url)
    database = Database(url)
    args = _book()
    deposit = args["transactions"][0]
    with database.session() as session:
        repository = PlatformRepository(session)
        repository.add_ledger_transaction(deposit)
        repository.add_ledger_transaction(deposit)
    with database.session() as session:
        repository = PlatformRepository(session)
        assert repository.list_ledger_transactions(args["ledger_id"], args["owner_id"]) == (deposit,)
        assert repository.list_ledger_transactions(args["ledger_id"], uuid4()) == ()
    with pytest.raises(ImmutableRecordConflict), database.session() as session:
        PlatformRepository(session).add_ledger_transaction(deposit.model_copy(update={"cash_amount": Decimal("2000")}))
    database.dispose()
