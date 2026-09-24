"""Deterministic point-in-time large-cap stock screening."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from tradingagents.contracts import (
    AssetClass,
    DataQualityStatus,
    InstrumentContract,
    ScreeningExclusionCode,
    StockScreenerPolicy,
    StockScreeningInput,
    Tradability,
)
from tradingagents.platform.artifacts import ArtifactService, LocalArtifactStore
from tradingagents.platform.persistence import (
    Database,
    PlatformRepository,
    downgrade_database,
    upgrade_database,
)
from tradingagents.platform.screening import DeterministicStockScreener

AS_OF = datetime(2026, 9, 20, 20, tzinfo=UTC)
GENERATED_AT = AS_OF + timedelta(minutes=10)


def _instrument(
    symbol: str,
    *,
    asset_class=AssetClass.EQUITY,
    tradability=Tradability.INVESTABLE,
    venue="NASDAQ",
    currency="USD",
):
    return InstrumentContract(
        instrument_id=uuid4(),
        symbol=symbol,
        canonical_symbol=symbol,
        display_name=symbol,
        asset_class=asset_class,
        tradability=tradability,
        venue=venue,
        quote_currency=currency,
        timezone="America/New_York",
        session_calendar="XNYS",
    )


def _input(
    symbol: str,
    *,
    market_cap=100_000_000_000,
    liquidity=100_000_000,
    price=100,
    history=500,
    volatility=0.3,
    quality=DataQualityStatus.OK,
    instrument=None,
):
    return StockScreeningInput(
        instrument=instrument or _instrument(symbol),
        observed_at=AS_OF - timedelta(minutes=1),
        source_snapshot_id=uuid4(),
        source_content_hash="sha256:" + "a" * 64,
        market_cap_usd=market_cap,
        average_dollar_volume_20d_usd=liquidity,
        last_price_usd=price,
        history_days=history,
        annualized_volatility=volatility,
        quality_status=quality,
    )


def _policy(**updates):
    values = {
        "policy_id": "us-large-cap-v1",
        "allowed_venues": ("NASDAQ", "NYSE"),
        "max_candidates": 2,
    }
    values.update(updates)
    return StockScreenerPolicy(**values)


@pytest.mark.unit
def test_screening_is_reproducible_and_input_order_independent():
    aapl = _input("AAPL", market_cap=3_000_000_000_000, liquidity=500_000_000)
    msft = _input("MSFT", market_cap=2_800_000_000_000, liquidity=600_000_000)
    nvda = _input("NVDA", market_cap=2_500_000_000_000, liquidity=700_000_000)
    screener = DeterministicStockScreener()
    first = screener.screen(
        inputs=(nvda, aapl, msft),
        policy=_policy(),
        as_of=AS_OF,
        generated_at=GENERATED_AT,
    )
    second = screener.screen(
        inputs=(msft, nvda, aapl),
        policy=_policy(),
        as_of=AS_OF,
        generated_at=GENERATED_AT,
    )
    assert first == second
    assert [item.canonical_symbol for item in first.candidates] == ["AAPL", "MSFT"]
    assert first.candidates[0].ranking_score == 4
    assert first.exclusions[0].codes == (ScreeningExclusionCode.OUTSIDE_LIMIT,)
    assert first.input_hash.startswith("sha256:")
    assert first.universe_hash.startswith("sha256:")


@pytest.mark.unit
def test_all_filter_failures_are_recorded_without_neutral_defaults():
    instrument = _instrument(
        "BAD",
        asset_class=AssetClass.ETF,
        tradability=Tradability.REFERENCE_ONLY,
        venue="OTC",
        currency="CAD",
    )
    bad = _input(
        "BAD",
        market_cap=1,
        liquidity=1,
        price=1,
        history=1,
        volatility=2,
        quality=DataQualityStatus.UNAVAILABLE,
        instrument=instrument,
    )
    snapshot = DeterministicStockScreener().screen(
        inputs=(bad,),
        policy=_policy(),
        as_of=AS_OF,
        generated_at=GENERATED_AT,
    )
    assert snapshot.candidates == ()
    assert snapshot.exclusions[0].codes == (
        ScreeningExclusionCode.NON_EQUITY,
        ScreeningExclusionCode.NOT_INVESTABLE,
        ScreeningExclusionCode.VENUE_NOT_ALLOWED,
        ScreeningExclusionCode.CURRENCY_NOT_ALLOWED,
        ScreeningExclusionCode.DATA_QUALITY,
        ScreeningExclusionCode.MARKET_CAP,
        ScreeningExclusionCode.LIQUIDITY,
        ScreeningExclusionCode.PRICE,
        ScreeningExclusionCode.HISTORY,
        ScreeningExclusionCode.VOLATILITY,
    )


@pytest.mark.unit
def test_future_and_duplicate_inputs_fail_closed():
    item = _input("AAPL")
    future = item.model_copy(update={"observed_at": AS_OF + timedelta(seconds=1)})
    screener = DeterministicStockScreener()
    with pytest.raises(ValueError, match="observable"):
        screener.screen(
            inputs=(future,),
            policy=_policy(),
            as_of=AS_OF,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="unique instrument"):
        screener.screen(
            inputs=(item, item),
            policy=_policy(),
            as_of=AS_OF,
            generated_at=GENERATED_AT,
        )


@pytest.mark.unit
def test_screening_snapshot_round_trip_is_owner_scoped(tmp_path):
    url = f"sqlite:///{tmp_path / 'screening.db'}"
    upgrade_database(url)
    database = Database(url)
    owner_id = uuid4()
    store = LocalArtifactStore(tmp_path / "artifacts")
    try:
        with database.session() as session:
            service = DeterministicStockScreener(
                ArtifactService(store, PlatformRepository(session))
            )
            snapshot = service.screen(
                inputs=(_input("AAPL"),),
                policy=_policy(),
                as_of=AS_OF,
                generated_at=GENERATED_AT,
            )
            manifest = service.persist(owner_id=owner_id, snapshot=snapshot)
            assert manifest.artifact_id == snapshot.screening_snapshot_id
        with database.session() as session:
            service = DeterministicStockScreener(
                ArtifactService(store, PlatformRepository(session))
            )
            assert service.load(
                owner_id=owner_id,
                screening_snapshot_id=snapshot.screening_snapshot_id,
            ) == snapshot
            with pytest.raises(LookupError, match="unavailable"):
                service.load(
                    owner_id=uuid4(),
                    screening_snapshot_id=snapshot.screening_snapshot_id,
                )
    finally:
        database.dispose()


@pytest.mark.integration
def test_postgresql_screening_snapshot_round_trip(tmp_path):
    url = os.getenv("TEST_POSTGRES_URL")
    if not url:
        pytest.skip("TEST_POSTGRES_URL is required for the PostgreSQL integration gate")
    upgrade_database(url)
    database = Database(url)
    owner_id = uuid4()
    store = LocalArtifactStore(tmp_path / "postgres-screening-artifacts")
    try:
        with database.session() as session:
            service = DeterministicStockScreener(
                ArtifactService(store, PlatformRepository(session))
            )
            snapshot = service.screen(
                inputs=(_input("AAPL"),),
                policy=_policy(),
                as_of=AS_OF,
                generated_at=GENERATED_AT,
            )
            service.persist(owner_id=owner_id, snapshot=snapshot)
        with database.session() as session:
            loaded = DeterministicStockScreener(
                ArtifactService(store, PlatformRepository(session))
            ).load(
                owner_id=owner_id,
                screening_snapshot_id=UUID(str(snapshot.screening_snapshot_id)),
            )
            assert loaded == snapshot
    finally:
        database.dispose()
        downgrade_database(url)
