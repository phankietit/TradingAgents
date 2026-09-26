"""Momentum, trend, volatility, relative strength, correlation, and breadth."""

from __future__ import annotations

import math
import os
import statistics
from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from tradingagents._compat import UTC
from tradingagents.contracts import (
    AssetClass,
    DataQualityStatus,
    FactorSeriesInput,
    FactorWindowConfig,
    InstrumentContract,
    PriceInterval,
    Tradability,
)
from tradingagents.platform.artifacts import ArtifactService, LocalArtifactStore
from tradingagents.platform.factors import DerivedFactorService, InsufficientFactorCoverage
from tradingagents.platform.market_data import normalize_time_series
from tradingagents.platform.persistence import (
    Database,
    PlatformRepository,
    downgrade_database,
    upgrade_database,
)

AS_OF = datetime(2026, 9, 20, tzinfo=UTC)
GENERATED_AT = AS_OF + timedelta(minutes=5)


def _source(symbol, prices, *, timestamps=None, quality=DataQualityStatus.OK):
    instrument = InstrumentContract(
        instrument_id=uuid4(),
        symbol=symbol,
        canonical_symbol=symbol,
        display_name=symbol,
        asset_class=AssetClass.ETF if symbol == "SPY" else AssetClass.EQUITY,
        tradability=Tradability.INVESTABLE,
        venue="NYSE" if symbol == "SPY" else "NASDAQ",
        quote_currency="USD",
        timezone="America/New_York",
        session_calendar="XNYS",
    )
    timestamps = timestamps or tuple(
        AS_OF - timedelta(days=len(prices) - index)
        for index in range(len(prices))
    )
    series = normalize_time_series(
        instrument=instrument,
        dataset="ohlcv.daily",
        interval=PriceInterval.ONE_DAY,
        as_of=AS_OF,
        annualization_periods=252,
        bars=tuple(
            {
                "timestamp": timestamp,
                "open": price,
                "high": price,
                "low": price,
                "close": price,
                "adjusted_close": price,
                "volume": 1_000_000,
            }
            for timestamp, price in zip(timestamps, prices, strict=True)
        ),
    )
    return FactorSeriesInput(
        canonical_symbol=symbol,
        snapshot_id=uuid4(),
        content_hash="sha256:" + "b" * 64,
        quality_status=quality,
        series=series,
    )


def _config():
    return FactorWindowConfig(
        config_id="daily-factors-test-v1",
        momentum_periods=2,
        trend_fast_periods=2,
        trend_slow_periods=3,
        volatility_periods=2,
        correlation_periods=3,
    )


@pytest.mark.unit
def test_factors_and_breadth_use_explicit_deterministic_formulas():
    rising = _source("AAPL", (100, 105, 110, 120))
    falling = _source("MSFT", (120, 115, 110, 100))
    benchmark = _source("SPY", (100, 102, 104, 106))
    snapshot = DerivedFactorService().compute(
        members=(falling, rising),
        benchmark=benchmark,
        config=_config(),
        as_of=AS_OF,
        generated_at=GENERATED_AT,
    )
    aapl = snapshot.factors[0]
    assert aapl.canonical_symbol == "AAPL"
    assert aapl.momentum == pytest.approx(120 / 105 - 1)
    assert aapl.trend_fast_vs_slow == pytest.approx(
        statistics.fmean((110, 120)) / statistics.fmean((105, 110, 120)) - 1
    )
    assert aapl.trend_price_vs_slow == pytest.approx(
        120 / statistics.fmean((105, 110, 120)) - 1
    )
    returns = (110 / 105 - 1, 120 / 110 - 1)
    assert aapl.annualized_volatility == pytest.approx(
        statistics.stdev(returns) * math.sqrt(252)
    )
    assert aapl.relative_strength == pytest.approx((120 / 105) - (106 / 102))
    assert aapl.benchmark_correlation is not None
    assert snapshot.breadth.positive_momentum_ratio == 0.5
    assert snapshot.breadth.above_slow_trend_ratio == 0.5


@pytest.mark.unit
def test_factor_result_is_input_order_independent():
    aapl = _source("AAPL", (100, 105, 110, 120))
    msft = _source("MSFT", (120, 115, 110, 100))
    benchmark = _source("SPY", (100, 102, 104, 106))
    service = DerivedFactorService()
    first = service.compute(
        members=(msft, aapl),
        benchmark=benchmark,
        config=_config(),
        as_of=AS_OF,
        generated_at=GENERATED_AT,
    )
    second = service.compute(
        members=(aapl, msft),
        benchmark=benchmark,
        config=_config(),
        as_of=AS_OF,
        generated_at=GENERATED_AT,
    )
    assert first == second


@pytest.mark.unit
def test_insufficient_history_or_alignment_fails_closed():
    short = _source("AAPL", (100, 101, 102))
    benchmark = _source("SPY", (100, 102, 104, 106))
    service = DerivedFactorService()
    with pytest.raises(InsufficientFactorCoverage, match="at least 4"):
        service.compute(
            members=(short,),
            benchmark=benchmark,
            config=_config(),
            as_of=AS_OF,
            generated_at=GENERATED_AT,
        )

    shifted = _source(
        "QQQ",
        (100, 102, 104, 106),
        timestamps=tuple(
            AS_OF - timedelta(hours=12, days=4 - index) for index in range(4)
        ),
    )
    with pytest.raises(InsufficientFactorCoverage, match="aligned"):
        service.compute(
            members=(_source("AAPL", (100, 105, 110, 120)),),
            benchmark=shifted,
            config=_config(),
            as_of=AS_OF,
            generated_at=GENERATED_AT,
        )


@pytest.mark.unit
def test_non_ok_source_quality_is_not_turned_into_a_factor():
    stale = _source(
        "AAPL", (100, 105, 110, 120), quality=DataQualityStatus.STALE
    )
    with pytest.raises(ValueError, match="OK source quality"):
        DerivedFactorService().compute(
            members=(stale,),
            benchmark=_source("SPY", (100, 102, 104, 106)),
            config=_config(),
            as_of=AS_OF,
            generated_at=GENERATED_AT,
        )


@pytest.mark.unit
def test_factor_snapshot_round_trip_is_owner_scoped(tmp_path):
    url = f"sqlite:///{tmp_path / 'factors.db'}"
    upgrade_database(url)
    database = Database(url)
    owner_id = uuid4()
    store = LocalArtifactStore(tmp_path / "artifacts")
    snapshot = DerivedFactorService().compute(
        members=(_source("AAPL", (100, 105, 110, 120)),),
        benchmark=_source("SPY", (100, 102, 104, 106)),
        config=_config(),
        as_of=AS_OF,
        generated_at=GENERATED_AT,
    )
    try:
        with database.session() as session:
            service = DerivedFactorService(ArtifactService(store, PlatformRepository(session)))
            service.persist(owner_id=owner_id, snapshot=snapshot)
        with database.session() as session:
            service = DerivedFactorService(ArtifactService(store, PlatformRepository(session)))
            assert service.load(
                owner_id=owner_id, factor_snapshot_id=snapshot.factor_snapshot_id
            ) == snapshot
            with pytest.raises(LookupError, match="unavailable"):
                service.load(
                    owner_id=uuid4(), factor_snapshot_id=snapshot.factor_snapshot_id
                )
    finally:
        database.dispose()


@pytest.mark.integration
def test_postgresql_factor_snapshot_round_trip(tmp_path):
    url = os.getenv("TEST_POSTGRES_URL")
    if not url:
        pytest.skip("TEST_POSTGRES_URL is required for the PostgreSQL integration gate")
    upgrade_database(url)
    database = Database(url)
    owner_id = uuid4()
    store = LocalArtifactStore(tmp_path / "postgres-factor-artifacts")
    snapshot = DerivedFactorService().compute(
        members=(_source("AAPL", (100, 105, 110, 120)),),
        benchmark=_source("SPY", (100, 102, 104, 106)),
        config=_config(),
        as_of=AS_OF,
        generated_at=GENERATED_AT,
    )
    try:
        with database.session() as session:
            DerivedFactorService(
                ArtifactService(store, PlatformRepository(session))
            ).persist(owner_id=owner_id, snapshot=snapshot)
        with database.session() as session:
            loaded = DerivedFactorService(
                ArtifactService(store, PlatformRepository(session))
            ).load(owner_id=owner_id, factor_snapshot_id=snapshot.factor_snapshot_id)
            assert loaded == snapshot
    finally:
        database.dispose()
        downgrade_database(url)
