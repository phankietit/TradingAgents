"""NQ/ES reference identity, sessions, rollovers, and gap evidence."""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from tradingagents._compat import UTC
from tradingagents.contracts import (
    AssetClass,
    DataQualityStatus,
    FuturesContractReference,
    FuturesDataGap,
    FuturesGapKind,
    FuturesSessionWindow,
    GapDisposition,
    InstrumentContract,
    PriceInterval,
    RollAdjustmentMethod,
    RolloverMetadata,
    Tradability,
)
from tradingagents.platform.artifacts import ArtifactService, LocalArtifactStore
from tradingagents.platform.market_data import (
    FuturesReferencePipeline,
    TimeSeriesSnapshotService,
    normalize_time_series,
)
from tradingagents.platform.persistence import (
    Database,
    PlatformRepository,
    downgrade_database,
    upgrade_database,
)

AS_OF = datetime(2026, 9, 18, 22, tzinfo=UTC)


def _instrument(symbol="NQ=F"):
    return InstrumentContract(
        instrument_id=uuid4(),
        symbol=symbol,
        canonical_symbol=symbol,
        display_name=f"{symbol} reference",
        asset_class=AssetClass.REFERENCE_FUTURE,
        tradability=Tradability.REFERENCE_ONLY,
        venue="CME",
        quote_currency="USD",
        timezone="America/Chicago",
        session_calendar="CME_Equity",
        benchmark_symbol="^NDX" if symbol == "NQ=F" else "^GSPC",
    )


def _contract(symbol="NQU26", *, observed_at=AS_OF - timedelta(days=30)):
    return FuturesContractReference(
        root_symbol=symbol[:2],
        contract_symbol=symbol,
        expiry_date=date(2026, 9, 18) if symbol.endswith("U26") else date(2026, 12, 18),
        last_trade_at=(
            datetime(2026, 9, 18, 20, tzinfo=UTC)
            if symbol.endswith("U26")
            else datetime(2026, 12, 18, 20, tzinfo=UTC)
        ),
        observed_at=observed_at,
        vendor="cme-reference-fixture",
    )


def _session():
    return FuturesSessionWindow(
        trading_date=date(2026, 9, 18),
        observed_at=AS_OF - timedelta(days=30),
        overnight_open=datetime(2026, 9, 17, 22, tzinfo=UTC),
        rth_open=datetime(2026, 9, 18, 13, 30, tzinfo=UTC),
        rth_close=datetime(2026, 9, 18, 20, tzinfo=UTC),
        session_close=datetime(2026, 9, 18, 21, tzinfo=UTC),
    )


def _roll():
    return RolloverMetadata(
        from_contract="NQU26",
        to_contract="NQZ26",
        effective_at=datetime(2026, 9, 17, 21, tzinfo=UTC),
        observed_at=datetime(2026, 9, 1, tzinfo=UTC),
        method=RollAdjustmentMethod.BACKWARD_DIFFERENCE,
        adjustment_value=12.25,
        vendor="cme-reference-fixture",
    )


def _context(tmp_path, instrument):
    url = f"sqlite:///{tmp_path / 'futures.db'}"
    upgrade_database(url)
    database = Database(url)
    owner_id = uuid4()
    store = LocalArtifactStore(tmp_path / "artifacts")
    with database.session() as session:
        repository = PlatformRepository(session)
        repository.add_instrument(instrument)
        series = normalize_time_series(
            instrument=instrument,
            dataset="ohlcv.continuous.1d",
            interval=PriceInterval.ONE_DAY,
            as_of=AS_OF,
            annualization_periods=252,
            bars=(
                {
                    "timestamp": AS_OF - timedelta(days=2),
                    "open": 24000,
                    "high": 24200,
                    "low": 23900,
                    "close": 24100,
                    "volume": 500_000,
                },
                {
                    "timestamp": AS_OF - timedelta(days=1),
                    "open": 24100,
                    "high": 24300,
                    "low": 24000,
                    "close": 24250,
                    "volume": 550_000,
                },
            ),
        )
        TimeSeriesSnapshotService(repository, ArtifactService(store, repository)).persist(
            owner_id=owner_id,
            series=series,
            vendor="continuous-fixture",
            retrieved_at=AS_OF + timedelta(minutes=1),
        )
    return database, owner_id, store


@pytest.mark.unit
def test_nq_reference_round_trip_preserves_contract_roll_and_sessions(tmp_path):
    instrument = _instrument()
    database, owner_id, store = _context(tmp_path, instrument)
    with database.session() as session:
        repository = PlatformRepository(session)
        pipeline = FuturesReferencePipeline(repository, ArtifactService(store, repository))
        manifest, reference = pipeline.build(
            owner_id=owner_id,
            instrument=instrument,
            as_of=AS_OF,
            retrieved_at=AS_OF + timedelta(hours=1),
            continuous_dataset="ohlcv.continuous.1d",
            active_contract=_contract("NQU26"),
            next_contract=_contract("NQZ26"),
            rollovers=(_roll(),),
            sessions=(_session(),),
            gaps=(
                FuturesDataGap(
                    start=datetime(2026, 9, 17, 21, tzinfo=UTC),
                    end=datetime(2026, 9, 17, 22, tzinfo=UTC),
                    kind=FuturesGapKind.SESSION_BREAK,
                    disposition=GapDisposition.EXPECTED,
                    reason="daily CME maintenance break",
                ),
            ),
            pipeline_id="cme-reference-v1",
        )
        assert manifest.quality_status is DataQualityStatus.OK
        assert reference.root_symbol == "NQ"
        assert reference.active_contract.contract_symbol == "NQU26"
        assert reference.rollovers[0].adjustment_value == pytest.approx(12.25)
        assert reference.sessions[0].calendar == "CME_Equity"

    with database.session() as session:
        repository = PlatformRepository(session)
        loaded_manifest, loaded = FuturesReferencePipeline(
            repository, ArtifactService(store, repository)
        ).load(owner_id=owner_id, instrument_id=instrument.instrument_id, as_of=AS_OF)
        assert loaded_manifest == manifest
        assert loaded == reference
    database.dispose()


@pytest.mark.unit
def test_unavailable_gap_degrades_quality_without_filling_price(tmp_path):
    instrument = _instrument("ES=F")
    database, owner_id, store = _context(tmp_path, instrument)
    active = FuturesContractReference(
        root_symbol="ES",
        contract_symbol="ESU26",
        expiry_date=date(2026, 9, 18),
        last_trade_at=datetime(2026, 9, 18, 20, tzinfo=UTC),
        observed_at=AS_OF - timedelta(days=30),
        vendor="cme-reference-fixture",
    )
    with database.session() as session:
        repository = PlatformRepository(session)
        _manifest, reference = FuturesReferencePipeline(
            repository, ArtifactService(store, repository)
        ).build(
            owner_id=owner_id,
            instrument=instrument,
            as_of=AS_OF,
            retrieved_at=AS_OF + timedelta(hours=1),
            continuous_dataset="ohlcv.continuous.1d",
            active_contract=active,
            next_contract=None,
            rollovers=(),
            sessions=(_session(),),
            gaps=(
                FuturesDataGap(
                    start=AS_OF - timedelta(hours=3),
                    end=AS_OF - timedelta(hours=2),
                    kind=FuturesGapKind.MISSING_BAR,
                    disposition=GapDisposition.UNAVAILABLE,
                    reason="vendor did not return the expected bar",
                ),
            ),
            pipeline_id="cme-reference-v1",
        )
        assert reference.quality_status is DataQualityStatus.COVERAGE_GAP
        assert "unresolved" in reference.quality_reasons[0]
    database.dispose()


@pytest.mark.unit
def test_reference_pipeline_rejects_other_futures_and_wrong_calendar(tmp_path):
    instrument = _instrument("YM=F")
    database, owner_id, store = _context(tmp_path, instrument)
    with database.session() as session:
        repository = PlatformRepository(session)
        with pytest.raises(ValueError, match="limited"):
            FuturesReferencePipeline(repository, ArtifactService(store, repository)).build(
                owner_id=owner_id,
                instrument=instrument,
                as_of=AS_OF,
                retrieved_at=AS_OF + timedelta(hours=1),
                continuous_dataset="ohlcv.continuous.1d",
                active_contract=_contract(),
                next_contract=None,
                rollovers=(),
                sessions=(_session(),),
                pipeline_id="cme-reference-v1",
            )
    database.dispose()


@pytest.mark.unit
def test_roll_and_gap_contracts_fail_closed():
    with pytest.raises(ValidationError, match="adjustment value"):
        RolloverMetadata(
            from_contract="NQU26",
            to_contract="NQZ26",
            effective_at=AS_OF,
            observed_at=AS_OF - timedelta(days=1),
            method=RollAdjustmentMethod.BACKWARD_RATIO,
            vendor="fixture",
        )
    with pytest.raises(ValidationError, match="session breaks"):
        FuturesDataGap(
            start=AS_OF - timedelta(hours=2),
            end=AS_OF - timedelta(hours=1),
            kind=FuturesGapKind.SESSION_BREAK,
            disposition=GapDisposition.UNAVAILABLE,
            reason="invalid classification",
        )


@pytest.mark.unit
def test_future_observed_contract_identity_is_rejected(tmp_path):
    instrument = _instrument()
    database, owner_id, store = _context(tmp_path, instrument)
    with database.session() as session:
        repository = PlatformRepository(session)
        with pytest.raises(ValidationError, match="observable"):
            FuturesReferencePipeline(repository, ArtifactService(store, repository)).build(
                owner_id=owner_id,
                instrument=instrument,
                as_of=AS_OF,
                retrieved_at=AS_OF + timedelta(hours=1),
                continuous_dataset="ohlcv.continuous.1d",
                active_contract=_contract(observed_at=AS_OF + timedelta(seconds=1)),
                next_contract=None,
                rollovers=(),
                sessions=(_session(),),
                pipeline_id="cme-reference-v1",
            )
    database.dispose()


@pytest.mark.integration
def test_postgresql_futures_reference_round_trip(tmp_path):
    url = os.getenv("TEST_POSTGRES_URL")
    if not url:
        pytest.skip("TEST_POSTGRES_URL is required for the PostgreSQL integration gate")
    upgrade_database(url)
    database = Database(url)
    owner_id = uuid4()
    instrument = _instrument()
    store = LocalArtifactStore(tmp_path / "postgres-futures-artifacts")
    try:
        with database.session() as session:
            repository = PlatformRepository(session)
            repository.add_instrument(instrument)
            series = normalize_time_series(
                instrument=instrument,
                dataset="ohlcv.continuous.1d",
                interval=PriceInterval.ONE_DAY,
                as_of=AS_OF,
                annualization_periods=252,
                bars=(
                    {
                        "timestamp": AS_OF - timedelta(days=1),
                        "open": 24000,
                        "high": 24200,
                        "low": 23900,
                        "close": 24100,
                        "volume": 500_000,
                    },
                ),
            )
            TimeSeriesSnapshotService(
                repository, ArtifactService(store, repository)
            ).persist(
                owner_id=owner_id,
                series=series,
                vendor="postgres-continuous-fixture",
                retrieved_at=AS_OF + timedelta(minutes=1),
            )
            manifest, reference = FuturesReferencePipeline(
                repository, ArtifactService(store, repository)
            ).build(
                owner_id=owner_id,
                instrument=instrument,
                as_of=AS_OF,
                retrieved_at=AS_OF + timedelta(hours=1),
                continuous_dataset="ohlcv.continuous.1d",
                active_contract=_contract(),
                next_contract=_contract("NQZ26"),
                rollovers=(_roll(),),
                sessions=(_session(),),
                pipeline_id="cme-reference-v1",
            )
        with database.session() as session:
            repository = PlatformRepository(session)
            loaded_manifest, loaded_reference = FuturesReferencePipeline(
                repository, ArtifactService(store, repository)
            ).load(owner_id=owner_id, instrument_id=instrument.instrument_id, as_of=AS_OF)
            assert loaded_manifest == manifest
            assert loaded_reference == reference
    finally:
        database.dispose()
        downgrade_database(url)
