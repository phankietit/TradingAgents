"""BTC/ETH UTC, venue-quality, liquidity, and benchmark evidence."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta, timezone
from uuid import uuid4

import pytest

from tradingagents.contracts import (
    AssetClass,
    CryptoQualityThresholds,
    CryptoVenueObservation,
    DataQualityStatus,
    InstrumentContract,
    PriceInterval,
    Tradability,
)
from tradingagents.platform.artifacts import ArtifactService, LocalArtifactStore
from tradingagents.platform.market_data import (
    CryptoSnapshotPipeline,
    TimeSeriesSnapshotService,
    normalize_time_series,
)
from tradingagents.platform.persistence import (
    Database,
    PlatformRepository,
    downgrade_database,
    upgrade_database,
)

AS_OF = datetime(2026, 9, 20, 12, tzinfo=UTC)


def _instrument(symbol):
    return InstrumentContract(
        instrument_id=uuid4(),
        symbol=symbol,
        canonical_symbol=symbol,
        display_name="Bitcoin" if symbol == "BTC-USD" else "Ether",
        asset_class=AssetClass.CRYPTO,
        tradability=Tradability.INVESTABLE,
        venue="AGGREGATE",
        quote_currency="USD",
        timezone="UTC",
        session_calendar="24/7",
        benchmark_symbol=None if symbol == "BTC-USD" else "BTC-USD",
    )


def _venue(name, base, *, observed_at=AS_OF - timedelta(minutes=2), volume=5_000_000):
    return CryptoVenueObservation(
        venue=name,
        base_asset=base,
        quote_asset="USD",
        observed_at=observed_at,
        last_price=100,
        bid=99.9,
        ask=100.1,
        quote_volume_24h=volume,
        vendor="crypto-fixture",
    )


def _seed_price(repository, store, owner_id, instrument, prices):
    series = normalize_time_series(
        instrument=instrument,
        dataset="ohlcv.crypto.1d",
        interval=PriceInterval.ONE_DAY,
        as_of=AS_OF,
        annualization_periods=365,
        bars=tuple(
            {
                "timestamp": AS_OF - timedelta(days=len(prices) - index),
                "open": price,
                "high": price * 1.01,
                "low": price * 0.99,
                "close": price,
                "volume": 10_000,
            }
            for index, price in enumerate(prices)
        ),
    )
    return TimeSeriesSnapshotService(repository, ArtifactService(store, repository)).persist(
        owner_id=owner_id,
        series=series,
        vendor="crypto-price-fixture",
        retrieved_at=AS_OF + timedelta(minutes=1),
    )


def _context(tmp_path):
    url = f"sqlite:///{tmp_path / 'crypto.db'}"
    upgrade_database(url)
    database = Database(url)
    owner_id = uuid4()
    store = LocalArtifactStore(tmp_path / "artifacts")
    btc = _instrument("BTC-USD")
    eth = _instrument("ETH-USD")
    with database.session() as session:
        repository = PlatformRepository(session)
        repository.add_instrument(btc)
        repository.add_instrument(eth)
        _seed_price(repository, store, owner_id, btc, (100, 105, 110))
        _seed_price(repository, store, owner_id, eth, (50, 54, 60))
    return database, owner_id, store, btc, eth


@pytest.mark.unit
def test_btc_snapshot_uses_utc_multi_venue_quality_and_no_self_benchmark(tmp_path):
    database, owner_id, store, btc, _eth = _context(tmp_path)
    with database.session() as session:
        repository = PlatformRepository(session)
        manifest, snapshot = CryptoSnapshotPipeline(
            repository, ArtifactService(store, repository)
        ).build(
            owner_id=owner_id,
            instrument=btc,
            as_of=AS_OF,
            retrieved_at=AS_OF + timedelta(hours=1),
            price_dataset="ohlcv.crypto.1d",
            venue_observations=(_venue("venue-a", "BTC"), _venue("venue-b", "BTC")),
            thresholds=CryptoQualityThresholds(),
            pipeline_id="crypto-composite-v1",
        )
        assert manifest.quality_status is DataQualityStatus.OK
        assert snapshot.quality_status is DataQualityStatus.OK
        assert snapshot.benchmark is None
        assert snapshot.liquidity.observed_venues == 2
        assert snapshot.liquidity.aggregate_quote_volume_24h == 10_000_000
        assert snapshot.price_statistics.annualized_volatility > 0

    with database.session() as session:
        repository = PlatformRepository(session)
        loaded_manifest, loaded = CryptoSnapshotPipeline(
            repository, ArtifactService(store, repository)
        ).load(owner_id=owner_id, instrument_id=btc.instrument_id, as_of=AS_OF)
        assert loaded_manifest == manifest
        assert loaded == snapshot
    database.dispose()


@pytest.mark.unit
def test_eth_requires_and_uses_btc_benchmark(tmp_path):
    database, owner_id, store, btc, eth = _context(tmp_path)
    with database.session() as session:
        repository = PlatformRepository(session)
        _manifest, snapshot = CryptoSnapshotPipeline(
            repository, ArtifactService(store, repository)
        ).build(
            owner_id=owner_id,
            instrument=eth,
            as_of=AS_OF,
            retrieved_at=AS_OF + timedelta(hours=1),
            price_dataset="ohlcv.crypto.1d",
            venue_observations=(_venue("venue-a", "ETH"), _venue("venue-b", "ETH")),
            thresholds=CryptoQualityThresholds(),
            benchmark_instrument=btc,
            pipeline_id="crypto-composite-v1",
        )
        assert snapshot.benchmark.benchmark_instrument_id == btc.instrument_id
        assert snapshot.benchmark.aligned_observations == 3
        assert snapshot.benchmark_price_snapshot_id is not None
    database.dispose()


@pytest.mark.unit
def test_insufficient_or_stale_venues_degrade_without_inventing_coverage(tmp_path):
    database, owner_id, store, btc, _eth = _context(tmp_path)
    with database.session() as session:
        repository = PlatformRepository(session)
        _manifest, snapshot = CryptoSnapshotPipeline(
            repository, ArtifactService(store, repository)
        ).build(
            owner_id=owner_id,
            instrument=btc,
            as_of=AS_OF,
            retrieved_at=AS_OF + timedelta(hours=1),
            price_dataset="ohlcv.crypto.1d",
            venue_observations=(
                _venue("venue-a", "BTC", observed_at=AS_OF - timedelta(hours=2)),
                _venue("future", "BTC", observed_at=AS_OF + timedelta(seconds=1)),
            ),
            thresholds=CryptoQualityThresholds(min_venues=2),
            pipeline_id="crypto-composite-v1",
        )
        assert snapshot.quality_status is DataQualityStatus.COVERAGE_GAP
        assert snapshot.liquidity.observed_venues == 1
        assert snapshot.liquidity.excluded_future_observations == 1
        assert any("venue coverage" in reason for reason in snapshot.quality_reasons)
        assert any("stale" in reason for reason in snapshot.quality_reasons)
    database.dispose()


@pytest.mark.unit
def test_crypto_identity_and_utc_boundaries_fail_closed(tmp_path):
    database, owner_id, store, btc, eth = _context(tmp_path)
    with database.session() as session:
        repository = PlatformRepository(session)
        pipeline = CryptoSnapshotPipeline(repository, ArtifactService(store, repository))
        with pytest.raises(ValueError, match="identity"):
            pipeline.build(
                owner_id=owner_id,
                instrument=btc,
                as_of=AS_OF,
                retrieved_at=AS_OF + timedelta(hours=1),
                price_dataset="ohlcv.crypto.1d",
                venue_observations=(_venue("venue-a", "ETH"),),
                thresholds=CryptoQualityThresholds(),
                pipeline_id="crypto-composite-v1",
            )
        with pytest.raises(ValueError, match="BTC-USD benchmark"):
            pipeline.build(
                owner_id=owner_id,
                instrument=eth,
                as_of=AS_OF,
                retrieved_at=AS_OF + timedelta(hours=1),
                price_dataset="ohlcv.crypto.1d",
                venue_observations=(_venue("venue-a", "ETH"), _venue("venue-b", "ETH")),
                thresholds=CryptoQualityThresholds(),
                pipeline_id="crypto-composite-v1",
            )
        non_utc = _venue("venue-a", "BTC").model_copy(
            update={
                "observed_at": datetime(
                    2026, 9, 20, 19, tzinfo=timezone(timedelta(hours=7))
                )
            }
        )
        with pytest.raises(ValueError, match="must use UTC"):
            pipeline.build(
                owner_id=owner_id,
                instrument=btc,
                as_of=AS_OF,
                retrieved_at=AS_OF + timedelta(hours=1),
                price_dataset="ohlcv.crypto.1d",
                venue_observations=(non_utc,),
                thresholds=CryptoQualityThresholds(),
                pipeline_id="crypto-composite-v1",
            )
    database.dispose()


@pytest.mark.unit
def test_non_whitelisted_crypto_is_rejected_before_snapshot_lookup(tmp_path):
    url = f"sqlite:///{tmp_path / 'other-crypto.db'}"
    upgrade_database(url)
    database = Database(url)
    other = _instrument("SOL-USD")
    store = LocalArtifactStore(tmp_path / "other-artifacts")
    with database.session() as session:
        repository = PlatformRepository(session)
        repository.add_instrument(other)
        with pytest.raises(ValueError, match="limited"):
            CryptoSnapshotPipeline(repository, ArtifactService(store, repository)).build(
                owner_id=uuid4(),
                instrument=other,
                as_of=AS_OF,
                retrieved_at=AS_OF + timedelta(hours=1),
                price_dataset="ohlcv.crypto.1d",
                venue_observations=(),
                thresholds=CryptoQualityThresholds(),
                pipeline_id="crypto-composite-v1",
            )
    database.dispose()


@pytest.mark.unit
def test_low_liquidity_and_wide_spread_are_explicit_coverage_gaps(tmp_path):
    database, owner_id, store, btc, _eth = _context(tmp_path)
    wide = _venue("venue-a", "BTC", volume=100).model_copy(
        update={"bid": 90.0, "ask": 110.0}
    )
    with database.session() as session:
        repository = PlatformRepository(session)
        _manifest, snapshot = CryptoSnapshotPipeline(
            repository, ArtifactService(store, repository)
        ).build(
            owner_id=owner_id,
            instrument=btc,
            as_of=AS_OF,
            retrieved_at=AS_OF + timedelta(hours=1),
            price_dataset="ohlcv.crypto.1d",
            venue_observations=(wide,),
            thresholds=CryptoQualityThresholds(min_venues=1),
            pipeline_id="crypto-composite-v1",
        )
        assert snapshot.quality_status is DataQualityStatus.COVERAGE_GAP
        assert any("volume" in reason for reason in snapshot.quality_reasons)
        assert any("spread" in reason for reason in snapshot.quality_reasons)
    database.dispose()


@pytest.mark.integration
def test_postgresql_crypto_snapshot_round_trip(tmp_path):
    url = os.getenv("TEST_POSTGRES_URL")
    if not url:
        pytest.skip("TEST_POSTGRES_URL is required for the PostgreSQL integration gate")
    upgrade_database(url)
    database = Database(url)
    owner_id = uuid4()
    store = LocalArtifactStore(tmp_path / "postgres-crypto-artifacts")
    btc = _instrument("BTC-USD")
    try:
        with database.session() as session:
            repository = PlatformRepository(session)
            repository.add_instrument(btc)
            _seed_price(repository, store, owner_id, btc, (100, 105, 110))
            manifest, snapshot = CryptoSnapshotPipeline(
                repository, ArtifactService(store, repository)
            ).build(
                owner_id=owner_id,
                instrument=btc,
                as_of=AS_OF,
                retrieved_at=AS_OF + timedelta(hours=1),
                price_dataset="ohlcv.crypto.1d",
                venue_observations=(_venue("venue-a", "BTC"), _venue("venue-b", "BTC")),
                thresholds=CryptoQualityThresholds(),
                pipeline_id="crypto-composite-v1",
            )
        with database.session() as session:
            repository = PlatformRepository(session)
            loaded_manifest, loaded_snapshot = CryptoSnapshotPipeline(
                repository, ArtifactService(store, repository)
            ).load(owner_id=owner_id, instrument_id=btc.instrument_id, as_of=AS_OF)
            assert loaded_manifest == manifest
            assert loaded_snapshot == snapshot
    finally:
        database.dispose()
        downgrade_database(url)
