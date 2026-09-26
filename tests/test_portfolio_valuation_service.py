from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from tests.test_platform_persistence import _instrument
from tests.test_portfolio_ledger import NOW, _book
from tradingagents.contracts import NormalizedTimeSeries
from tradingagents.platform.artifacts import ArtifactService, LocalArtifactStore
from tradingagents.platform.market_data import TimeSeriesSnapshotService
from tradingagents.platform.persistence import Database, PlatformRepository, upgrade_database
from tradingagents.platform.portfolio.service import PortfolioLedgerService


def setup_valuation(tmp_path, *, foreign_source=False, retrieval=NOW, database_url=None):
    url = database_url or f"sqlite:///{tmp_path / 'valuation.db'}"
    upgrade_database(url)
    database = Database(url)
    store = LocalArtifactStore(tmp_path / "artifacts")
    book = _book()
    instrument_id = next(iter(book["prices"]))
    with database.session() as session:
        repo = PlatformRepository(session)
        repo.add_instrument(_instrument().model_copy(update={"instrument_id": instrument_id}))
        for entry in book["transactions"]:
            repo.add_ledger_transaction(entry)
        series = NormalizedTimeSeries(instrument_id=instrument_id, dataset="daily_prices", interval="1d",
            timezone="UTC", quote_currency="USD", as_of=NOW, annualization_periods=252,
            bars=({"timestamp": NOW, "open": 110, "high": 110, "low": 110, "close": 110,
                   "adjusted_close": 55, "volume": 1000},))
        source = TimeSeriesSnapshotService(repo, ArtifactService(store, repo)).persist(
            owner_id=uuid4() if foreign_source else book["owner_id"], series=series,
            vendor="fixture", retrieved_at=retrieval)
    args = {key: value for key, value in book.items() if key not in {"prices", "transactions"}}
    args["price_snapshot_ids"] = {instrument_id: source.snapshot_id}
    return database, store, args


def test_persisted_valuation_replays_raw_close_and_is_idempotent(tmp_path):
    database, store, args = setup_valuation(tmp_path)
    with database.session() as session:
        repo = PlatformRepository(session)
        service = PortfolioLedgerService(ArtifactService(store, repo))
        result = service.replay(**args)
        assert service.replay(**args) == result
        assert result.positions[0].market_price == Decimal(110)
        assert result.net_asset_value == Decimal(1050)
        assert repo.get_portfolio_snapshot(result.portfolio_id, args["owner_id"]) == result
        assert repo.get_portfolio_snapshot(result.portfolio_id, uuid4()) is None
    database.dispose()


@pytest.mark.parametrize("case", ["foreign_source", "future_retrieval", "stale", "wrong_owner", "missing"])
def test_unverified_valuation_cannot_be_persisted(tmp_path, case):
    database, store, args = setup_valuation(tmp_path, foreign_source=case == "foreign_source",
        retrieval=NOW + timedelta(seconds=1) if case == "future_retrieval" else NOW)
    if case == "stale":
        args["as_of"] = NOW + timedelta(days=2)
    elif case == "wrong_owner":
        args["owner_id"] = uuid4()
    elif case == "missing":
        args["price_snapshot_ids"] = {}
    with pytest.raises(ValueError), database.session() as session:
        PortfolioLedgerService(ArtifactService(store, PlatformRepository(session))).replay(**args)
    database.dispose()
