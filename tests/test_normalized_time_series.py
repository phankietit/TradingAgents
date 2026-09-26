"""Normalized OHLCV, deterministic metrics, and immutable snapshot evidence."""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy import func, select

from tradingagents._compat import UTC
from tradingagents.contracts import (
    AssetClass,
    InstrumentContract,
    OHLCVBar,
    PriceBasis,
    PriceInterval,
    Tradability,
)
from tradingagents.platform.artifacts import ArtifactService, LocalArtifactStore
from tradingagents.platform.market_data import (
    InsufficientBenchmarkCoverage,
    TimeSeriesSnapshotService,
    TimeSeriesUnavailable,
    build_time_series_view,
    normalize_time_series,
    slice_time_series,
)
from tradingagents.platform.persistence import (
    Database,
    PlatformRepository,
    downgrade_database,
    upgrade_database,
)
from tradingagents.platform.persistence.models import ArtifactRow

AS_OF = datetime(2026, 9, 20, tzinfo=UTC)


def _instrument(*, crypto=False):
    return InstrumentContract(
        instrument_id=uuid4(),
        symbol="BTC-USD" if crypto else "AAPL",
        canonical_symbol="BTC-USD" if crypto else "AAPL",
        display_name="Bitcoin" if crypto else "Apple Inc.",
        asset_class=AssetClass.CRYPTO if crypto else AssetClass.EQUITY,
        tradability=Tradability.INVESTABLE,
        venue="AGGREGATE" if crypto else "NASDAQ",
        quote_currency="USD",
        timezone="UTC" if crypto else "America/New_York",
        session_calendar="24/7" if crypto else "XNAS",
        benchmark_symbol=None if crypto else "SPY",
    )


def _bars(prices=(50.0, 55.0, 52.0, 60.0)):
    result = []
    for index, adjusted_close in enumerate(prices):
        close = 100.0 + index
        result.append(
            {
                "timestamp": AS_OF - timedelta(days=len(prices) - index),
                "open": close - 1,
                "high": close + 2,
                "low": close - 2,
                "close": close,
                "adjusted_close": adjusted_close,
                "volume": 1_000_000 + index,
            }
        )
    return result


def _series(instrument=None, prices=(50.0, 55.0, 52.0, 60.0)):
    instrument = instrument or _instrument()
    return normalize_time_series(
        instrument=instrument,
        dataset="ohlcv.daily",
        interval=PriceInterval.ONE_DAY,
        as_of=AS_OF,
        annualization_periods=365 if instrument.asset_class is AssetClass.CRYPTO else 252,
        bars=reversed(_bars(prices)),
    )


@pytest.mark.unit
def test_normalization_sorts_rows_and_metrics_use_adjusted_prices():
    series = _series()
    assert list(series.bars) == sorted(series.bars, key=lambda bar: bar.timestamp)
    assert series.price_basis is PriceBasis.ADJUSTED_CLOSE
    view = build_time_series_view(series)
    assert view.statistics.observations == 4
    assert view.statistics.total_return == pytest.approx(0.2)
    assert view.statistics.maximum_drawdown == pytest.approx(52 / 55 - 1)
    assert view.statistics.annualized_volatility > 0
    assert view.returns[0].simple_return is None
    assert view.returns[-1].simple_return == pytest.approx(60 / 52 - 1)


@pytest.mark.unit
def test_invalid_future_duplicate_partial_adjustment_and_price_envelope_fail_closed():
    instrument = _instrument()
    future = _bars()
    future[-1]["timestamp"] = AS_OF + timedelta(seconds=1)
    with pytest.raises(ValidationError, match="as_of"):
        normalize_time_series(
            instrument=instrument,
            dataset="ohlcv.daily",
            interval=PriceInterval.ONE_DAY,
            as_of=AS_OF,
            annualization_periods=252,
            bars=future,
        )

    duplicate = _bars()
    duplicate[1]["timestamp"] = duplicate[0]["timestamp"]
    with pytest.raises(ValidationError, match="unique"):
        normalize_time_series(
            instrument=instrument,
            dataset="ohlcv.daily",
            interval=PriceInterval.ONE_DAY,
            as_of=AS_OF,
            annualization_periods=252,
            bars=duplicate,
        )

    partial = _bars()
    partial[0]["adjusted_close"] = None
    with pytest.raises(ValidationError, match="coverage"):
        normalize_time_series(
            instrument=instrument,
            dataset="ohlcv.daily",
            interval=PriceInterval.ONE_DAY,
            as_of=AS_OF,
            annualization_periods=252,
            bars=partial,
        )

    with pytest.raises(ValidationError, match="high"):
        OHLCVBar.model_validate({**_bars()[0], "high": 1})


@pytest.mark.unit
def test_crypto_requires_utc_bar_boundaries():
    bars = _bars()
    bars[0]["timestamp"] = datetime.fromisoformat("2026-09-16T00:00:00+07:00")
    with pytest.raises(ValueError, match="UTC bar"):
        normalize_time_series(
            instrument=_instrument(crypto=True),
            dataset="ohlcv.daily",
            interval=PriceInterval.ONE_DAY,
            as_of=AS_OF,
            annualization_periods=365,
            bars=bars,
        )


@pytest.mark.unit
def test_benchmark_comparison_aligns_exact_timestamps_and_rejects_insufficient_overlap():
    asset = _series(prices=(100.0, 103.0, 102.0, 108.0))
    benchmark = _series(_instrument(), prices=(100.0, 101.0, 102.0, 104.0))
    view = build_time_series_view(asset, benchmark=benchmark)
    assert view.benchmark.aligned_observations == 4
    assert view.benchmark.asset_return == pytest.approx(0.08)
    assert view.benchmark.benchmark_return == pytest.approx(0.04)
    assert view.benchmark.excess_return == pytest.approx(0.04)

    one_bar = benchmark.model_copy(update={"bars": benchmark.bars[:1]})
    with pytest.raises(InsufficientBenchmarkCoverage):
        build_time_series_view(asset, benchmark=one_bar)


@pytest.mark.unit
def test_range_slice_is_inclusive_and_cannot_cross_snapshot_as_of():
    series = _series()
    sliced = slice_time_series(
        series,
        start=series.bars[1].timestamp,
        end=series.bars[2].timestamp,
    )
    assert sliced.bars == series.bars[1:3]
    with pytest.raises(ValueError, match="as_of"):
        slice_time_series(series, end=AS_OF + timedelta(seconds=1))
    with pytest.raises(TimeSeriesUnavailable):
        slice_time_series(series, start=AS_OF - timedelta(hours=1))


@pytest.mark.unit
def test_snapshot_round_trip_is_owner_scoped_and_point_in_time_safe(tmp_path):
    url = f"sqlite:///{tmp_path / 'timeseries.db'}"
    upgrade_database(url)
    database = Database(url)
    owner_id = uuid4()
    instrument = _instrument()
    series = _series(instrument)
    store = LocalArtifactStore(tmp_path / "artifacts")
    with database.session() as session:
        repository = PlatformRepository(session)
        repository.add_instrument(instrument)
        manifest = TimeSeriesSnapshotService(
            repository, ArtifactService(store, repository)
        ).persist(
            owner_id=owner_id,
            series=series,
            vendor="test-fixture",
            retrieved_at=AS_OF + timedelta(minutes=1),
        )
        repeated = TimeSeriesSnapshotService(
            repository, ArtifactService(store, repository)
        ).persist(
            owner_id=owner_id,
            series=series,
            vendor="test-fixture",
            retrieved_at=AS_OF + timedelta(minutes=1),
            snapshot_id=manifest.snapshot_id,
        )
        assert repeated == manifest
        assert session.scalar(
            select(func.count()).select_from(ArtifactRow).where(
                ArtifactRow.snapshot_id == manifest.snapshot_id
            )
        ) == 1

    with database.session() as session:
        repository = PlatformRepository(session)
        service = TimeSeriesSnapshotService(repository, ArtifactService(store, repository))
        loaded_manifest, loaded_series = service.load(
            owner_id=owner_id,
            instrument_id=instrument.instrument_id,
            dataset="ohlcv.daily",
            as_of=AS_OF,
        )
        assert loaded_manifest == manifest
        assert loaded_series == series
        with pytest.raises(TimeSeriesUnavailable):
            service.load(
                owner_id=uuid4(),
                instrument_id=instrument.instrument_id,
                dataset="ohlcv.daily",
                as_of=AS_OF,
            )
        with pytest.raises(TimeSeriesUnavailable):
            service.load(
                owner_id=owner_id,
                instrument_id=instrument.instrument_id,
                dataset="ohlcv.daily",
                as_of=series.bars[-1].timestamp - timedelta(seconds=1),
            )
    database.dispose()


@pytest.mark.integration
def test_postgresql_time_series_snapshot_round_trip(tmp_path):
    url = os.getenv("TEST_POSTGRES_URL")
    if not url:
        pytest.skip("TEST_POSTGRES_URL is required for the PostgreSQL integration gate")
    upgrade_database(url)
    database = Database(url)
    owner_id = uuid4()
    instrument = _instrument()
    series = _series(instrument)
    store = LocalArtifactStore(tmp_path / "postgres-artifacts")
    try:
        with database.session() as session:
            repository = PlatformRepository(session)
            repository.add_instrument(instrument)
            TimeSeriesSnapshotService(repository, ArtifactService(store, repository)).persist(
                owner_id=owner_id,
                series=series,
                vendor="postgres-fixture",
                retrieved_at=AS_OF + timedelta(minutes=1),
            )
        with database.session() as session:
            repository = PlatformRepository(session)
            _manifest, loaded = TimeSeriesSnapshotService(
                repository, ArtifactService(store, repository)
            ).load(
                owner_id=owner_id,
                instrument_id=instrument.instrument_id,
                dataset="ohlcv.daily",
                as_of=AS_OF,
            )
            assert loaded == series
    finally:
        database.dispose()
        downgrade_database(url)
