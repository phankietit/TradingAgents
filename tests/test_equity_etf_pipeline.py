"""Point-in-time equity/ETF pipeline and asset-boundary evidence."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from tradingagents.contracts import (
    AssetClass,
    DataQualityStatus,
    DatasetCoverage,
    EquityETFDataset,
    EquityETFSnapshotBundle,
    ETFProfile,
    FilingRecord,
    FundamentalFact,
    FundHolding,
    InstrumentContract,
    NewsRecord,
    PriceInterval,
    Tradability,
)
from tradingagents.platform.artifacts import ArtifactService, LocalArtifactStore
from tradingagents.platform.market_data import (
    EquityETFSnapshotPipeline,
    SourceBatch,
    TimeSeriesSnapshotService,
    TimeSeriesUnavailable,
    normalize_time_series,
)
from tradingagents.platform.persistence import (
    Database,
    PlatformRepository,
    downgrade_database,
    upgrade_database,
)

AS_OF = datetime(2026, 9, 20, 12, tzinfo=UTC)


def _instrument(asset_class=AssetClass.EQUITY):
    etf = asset_class is AssetClass.ETF
    return InstrumentContract(
        instrument_id=uuid4(),
        symbol="QQQ" if etf else "AAPL",
        canonical_symbol="QQQ" if etf else "AAPL",
        display_name="Invesco QQQ Trust" if etf else "Apple Inc.",
        asset_class=asset_class,
        tradability=Tradability.INVESTABLE,
        venue="NASDAQ",
        quote_currency="USD",
        timezone="America/New_York",
        session_calendar="XNAS",
        benchmark_symbol="^NDX" if etf else "SPY",
    )


def _filing(*, accession="0001", filed_at=AS_OF - timedelta(days=10)):
    return FilingRecord(
        accession_number=accession,
        form="10-Q",
        period_end=AS_OF - timedelta(days=40),
        filed_at=filed_at,
        vendor="sec-edgar",
        source_url="https://www.sec.gov/Archives/example",
    )


def _fact(*, source_id="fact-1", filed_at=AS_OF - timedelta(days=10)):
    return FundamentalFact(
        metric="revenue",
        value=100_000_000,
        unit="USD",
        period_end=AS_OF - timedelta(days=40),
        filed_at=filed_at,
        form="10-Q",
        vendor="sec-edgar",
        source_id=source_id,
    )


def _news(*, article_id="news-1", published_at=AS_OF - timedelta(hours=2)):
    return NewsRecord(
        article_id=article_id,
        headline="Company releases product update",
        source="Example Wire",
        vendor="news-fixture",
        published_at=published_at,
        source_url="https://example.com/article",
    )


def _profile(*, holdings_as_of=AS_OF - timedelta(days=1)):
    return ETFProfile(
        benchmark_symbol="^NDX",
        issuer="Invesco",
        expense_ratio=0.002,
        holdings_as_of=holdings_as_of,
        vendor="fund-fixture",
        holdings=(
            FundHolding(canonical_symbol="AAPL", weight=0.09),
            FundHolding(canonical_symbol="MSFT", weight=0.08),
        ),
    )


def _pipeline_context(tmp_path, instrument):
    url = f"sqlite:///{tmp_path / 'equity-etf.db'}"
    upgrade_database(url)
    database = Database(url)
    owner_id = uuid4()
    store = LocalArtifactStore(tmp_path / "artifacts")
    with database.session() as session:
        repository = PlatformRepository(session)
        repository.add_instrument(instrument)
        series = normalize_time_series(
            instrument=instrument,
            dataset="ohlcv.daily",
            interval=PriceInterval.ONE_DAY,
            as_of=AS_OF,
            annualization_periods=252,
            bars=(
                {
                    "timestamp": AS_OF - timedelta(days=2),
                    "open": 100,
                    "high": 102,
                    "low": 99,
                    "close": 101,
                    "adjusted_close": 100,
                    "volume": 1_000_000,
                },
                {
                    "timestamp": AS_OF - timedelta(days=1),
                    "open": 101,
                    "high": 103,
                    "low": 100,
                    "close": 102,
                    "adjusted_close": 101,
                    "volume": 1_100_000,
                },
            ),
        )
        TimeSeriesSnapshotService(repository, ArtifactService(store, repository)).persist(
            owner_id=owner_id,
            series=series,
            vendor="price-fixture",
            retrieved_at=AS_OF + timedelta(minutes=1),
        )
    return database, owner_id, store


@pytest.mark.unit
def test_equity_pipeline_excludes_future_sources_and_preserves_restatements(tmp_path):
    instrument = _instrument()
    database, owner_id, store = _pipeline_context(tmp_path, instrument)
    future = AS_OF + timedelta(seconds=1)
    with database.session() as session:
        repository = PlatformRepository(session)
        pipeline = EquityETFSnapshotPipeline(repository, ArtifactService(store, repository))
        manifest, bundle = pipeline.build_equity(
            owner_id=owner_id,
            instrument=instrument,
            as_of=AS_OF,
            retrieved_at=AS_OF + timedelta(hours=1),
            price_dataset="ohlcv.daily",
            filings=SourceBatch(
                "sec-edgar", DataQualityStatus.OK, (_filing(), _filing(accession="future", filed_at=future))
            ),
            fundamentals=SourceBatch(
                "sec-edgar",
                DataQualityStatus.OK,
                (_fact(), _fact(source_id="restatement", filed_at=AS_OF - timedelta(days=1)), _fact(source_id="future", filed_at=future)),
            ),
            news=SourceBatch(
                "news-fixture", DataQualityStatus.OK, (_news(), _news(article_id="future", published_at=future))
            ),
            pipeline_id="equity-composite-v1",
        )
        assert manifest.quality_status is DataQualityStatus.OK
        assert len(bundle.filings) == 1
        assert len(bundle.fundamentals) == 2
        assert len(bundle.news) == 1
        assert {item.dataset: item.excluded_future_count for item in bundle.coverage} == {
            EquityETFDataset.PRICE: 0,
            EquityETFDataset.FILINGS: 1,
            EquityETFDataset.FUNDAMENTALS: 1,
            EquityETFDataset.NEWS: 1,
        }

    with database.session() as session:
        repository = PlatformRepository(session)
        loaded_manifest, loaded = EquityETFSnapshotPipeline(
            repository, ArtifactService(store, repository)
        ).load(owner_id=owner_id, instrument_id=instrument.instrument_id, as_of=AS_OF)
        assert loaded_manifest == manifest
        assert loaded == bundle
        with pytest.raises(LookupError):
            EquityETFSnapshotPipeline(
                repository, ArtifactService(store, repository)
            ).load(owner_id=uuid4(), instrument_id=instrument.instrument_id, as_of=AS_OF)
    database.dispose()


@pytest.mark.unit
def test_future_only_source_is_coverage_gap_not_no_data(tmp_path):
    instrument = _instrument()
    database, owner_id, store = _pipeline_context(tmp_path, instrument)
    with database.session() as session:
        repository = PlatformRepository(session)
        _manifest, bundle = EquityETFSnapshotPipeline(
            repository, ArtifactService(store, repository)
        ).build_equity(
            owner_id=owner_id,
            instrument=instrument,
            as_of=AS_OF,
            retrieved_at=AS_OF + timedelta(hours=1),
            price_dataset="ohlcv.daily",
            filings=SourceBatch("sec-edgar", DataQualityStatus.OK, (_filing(filed_at=AS_OF + timedelta(days=1)),)),
            fundamentals=SourceBatch("sec-edgar", DataQualityStatus.OK, (_fact(filed_at=AS_OF + timedelta(days=1)),)),
            news=SourceBatch("news-fixture", DataQualityStatus.NO_DATA, reason="reachable but empty"),
            pipeline_id="equity-composite-v1",
        )
        coverage = {item.dataset: item.status for item in bundle.coverage}
        assert coverage[EquityETFDataset.FILINGS] is DataQualityStatus.COVERAGE_GAP
        assert coverage[EquityETFDataset.FUNDAMENTALS] is DataQualityStatus.COVERAGE_GAP
        assert coverage[EquityETFDataset.NEWS] is DataQualityStatus.NO_DATA
        assert bundle.quality_status is DataQualityStatus.COVERAGE_GAP
    database.dispose()


@pytest.mark.unit
def test_etf_pipeline_uses_point_in_time_fund_metadata_not_company_fundamentals(tmp_path):
    instrument = _instrument(AssetClass.ETF)
    database, owner_id, store = _pipeline_context(tmp_path, instrument)
    with database.session() as session:
        repository = PlatformRepository(session)
        _manifest, bundle = EquityETFSnapshotPipeline(
            repository, ArtifactService(store, repository)
        ).build_etf(
            owner_id=owner_id,
            instrument=instrument,
            as_of=AS_OF,
            retrieved_at=AS_OF + timedelta(hours=1),
            price_dataset="ohlcv.daily",
            news=SourceBatch("news-fixture", DataQualityStatus.OK, (_news(),)),
            fund_metadata=SourceBatch("fund-fixture", DataQualityStatus.OK, (_profile(),)),
            pipeline_id="etf-composite-v1",
        )
        assert bundle.quality_status is DataQualityStatus.OK
        assert bundle.fundamentals == ()
        assert bundle.fund_profile.holdings_as_of <= AS_OF
        assert bundle.fund_profile.expense_ratio == pytest.approx(0.002)
    database.dispose()


@pytest.mark.unit
def test_etf_contract_rejects_company_fundamentals_and_source_failure_cannot_carry_rows():
    with pytest.raises(ValueError, match="non-OK"):
        SourceBatch(
            "sec-edgar",
            DataQualityStatus.UNAVAILABLE,
            (_filing(),),
            "vendor outage",
        )
    with pytest.raises(ValidationError, match="company fundamentals"):
        EquityETFSnapshotBundle(
            bundle_id=uuid4(),
            instrument_id=uuid4(),
            asset_class=AssetClass.ETF,
            as_of=AS_OF,
            retrieved_at=AS_OF + timedelta(hours=1),
            price_snapshot_id=uuid4(),
            fundamentals=(_fact(),),
            fund_profile=_profile(),
            coverage=(
                DatasetCoverage(
                    dataset=EquityETFDataset.PRICE,
                    vendors=("fixture",),
                    status=DataQualityStatus.OK,
                    eligible_count=1,
                    excluded_future_count=0,
                    reason="fixture",
                ),
            ),
            quality_status=DataQualityStatus.OK,
        )


@pytest.mark.unit
def test_pipeline_requires_an_eligible_price_snapshot(tmp_path):
    instrument = _instrument()
    url = f"sqlite:///{tmp_path / 'missing-price.db'}"
    upgrade_database(url)
    database = Database(url)
    store = LocalArtifactStore(tmp_path / "missing-price-artifacts")
    with database.session() as session:
        repository = PlatformRepository(session)
        repository.add_instrument(instrument)
        with pytest.raises(TimeSeriesUnavailable):
            EquityETFSnapshotPipeline(
                repository, ArtifactService(store, repository)
            ).build_equity(
                owner_id=uuid4(),
                instrument=instrument,
                as_of=AS_OF,
                retrieved_at=AS_OF + timedelta(hours=1),
                price_dataset="ohlcv.daily",
                filings=SourceBatch("sec-edgar", DataQualityStatus.NO_DATA),
                fundamentals=SourceBatch("sec-edgar", DataQualityStatus.NO_DATA),
                news=SourceBatch("news-fixture", DataQualityStatus.NO_DATA),
                pipeline_id="equity-composite-v1",
            )
    database.dispose()


@pytest.mark.integration
def test_postgresql_equity_bundle_round_trip(tmp_path):
    url = os.getenv("TEST_POSTGRES_URL")
    if not url:
        pytest.skip("TEST_POSTGRES_URL is required for the PostgreSQL integration gate")
    upgrade_database(url)
    database = Database(url)
    owner_id = uuid4()
    instrument = _instrument()
    store = LocalArtifactStore(tmp_path / "postgres-equity-artifacts")
    try:
        with database.session() as session:
            repository = PlatformRepository(session)
            repository.add_instrument(instrument)
            series = normalize_time_series(
                instrument=instrument,
                dataset="ohlcv.daily",
                interval=PriceInterval.ONE_DAY,
                as_of=AS_OF,
                annualization_periods=252,
                bars=(
                    {
                        "timestamp": AS_OF - timedelta(days=1),
                        "open": 100,
                        "high": 102,
                        "low": 99,
                        "close": 101,
                        "adjusted_close": 101,
                        "volume": 1_000_000,
                    },
                ),
            )
            TimeSeriesSnapshotService(
                repository, ArtifactService(store, repository)
            ).persist(
                owner_id=owner_id,
                series=series,
                vendor="postgres-price-fixture",
                retrieved_at=AS_OF + timedelta(minutes=1),
            )
            manifest, bundle = EquityETFSnapshotPipeline(
                repository, ArtifactService(store, repository)
            ).build_equity(
                owner_id=owner_id,
                instrument=instrument,
                as_of=AS_OF,
                retrieved_at=AS_OF + timedelta(hours=1),
                price_dataset="ohlcv.daily",
                filings=SourceBatch("sec-edgar", DataQualityStatus.OK, (_filing(),)),
                fundamentals=SourceBatch("sec-edgar", DataQualityStatus.OK, (_fact(),)),
                news=SourceBatch("news-fixture", DataQualityStatus.OK, (_news(),)),
                pipeline_id="equity-composite-v1",
            )
        with database.session() as session:
            repository = PlatformRepository(session)
            loaded_manifest, loaded_bundle = EquityETFSnapshotPipeline(
                repository, ArtifactService(store, repository)
            ).load(owner_id=owner_id, instrument_id=instrument.instrument_id, as_of=AS_OF)
            assert loaded_manifest == manifest
            assert loaded_bundle == bundle
    finally:
        database.dispose()
        downgrade_database(url)
