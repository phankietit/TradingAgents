"""Instrument master identity, alias, catalog, and lookup evidence."""

from __future__ import annotations

import os
from uuid import uuid4

import pytest
from pydantic import ValidationError

from tradingagents.contracts import (
    AssetClass,
    InstrumentAliasContract,
    InstrumentContract,
    Tradability,
    normalize_instrument_alias,
)
from tradingagents.platform.instruments import (
    INITIAL_INSTRUMENT_CATALOG,
    InstrumentMaster,
    stable_instrument_id,
)
from tradingagents.platform.persistence import (
    AmbiguousInstrumentAlias,
    Database,
    ImmutableRecordConflict,
    PlatformRepository,
    downgrade_database,
    upgrade_database,
)


def _instrument(symbol: str, *, asset_class: AssetClass = AssetClass.EQUITY):
    return InstrumentContract(
        instrument_id=uuid4(),
        symbol=symbol,
        canonical_symbol=symbol,
        display_name=f"{symbol} instrument",
        asset_class=asset_class,
        tradability=Tradability.INVESTABLE,
        venue="NASDAQ",
        quote_currency="USD",
        timezone="America/New_York",
        session_calendar="XNAS",
        benchmark_symbol="SPY",
    )


@pytest.mark.unit
def test_alias_normalization_is_stable_and_rejects_control_characters():
    alias = InstrumentAliasContract.create(
        instrument_id=uuid4(), namespace="common", alias="  ＢＴＣ  "
    )
    assert alias.normalized_alias == "btc"
    assert normalize_instrument_alias("AaPl") == "aapl"
    with pytest.raises((ValidationError, ValueError), match="control"):
        InstrumentAliasContract.create(
            instrument_id=uuid4(), namespace="common", alias="BTC\nUSD"
        )


@pytest.mark.unit
def test_catalog_has_stable_ids_and_enforces_asset_boundaries():
    assert stable_instrument_id(
        asset_class=AssetClass.EQUITY, venue="nasdaq", canonical_symbol="aapl"
    ) == stable_instrument_id(
        asset_class=AssetClass.EQUITY, venue="NASDAQ", canonical_symbol="AAPL"
    )
    instruments = {seed.instrument.canonical_symbol: seed.instrument for seed in INITIAL_INSTRUMENT_CATALOG}
    assert instruments["NQ=F"].tradability is Tradability.REFERENCE_ONLY
    assert instruments["ES=F"].tradability is Tradability.REFERENCE_ONLY
    assert instruments["BTC-USD"].timezone == "UTC"
    assert instruments["ETH-USD"].session_calendar == "24/7"
    assert {symbol for symbol, item in instruments.items() if item.asset_class is AssetClass.CRYPTO} == {
        "BTC-USD",
        "ETH-USD",
    }


@pytest.mark.unit
def test_bootstrap_is_idempotent_and_supports_filters_and_alias_resolution(tmp_path):
    url = f"sqlite:///{tmp_path / 'instrument-master.db'}"
    upgrade_database(url)
    database = Database(url)
    with database.session() as session:
        master = InstrumentMaster(PlatformRepository(session))
        assert master.bootstrap() == len(INITIAL_INSTRUMENT_CATALOG)
        assert master.bootstrap() == len(INITIAL_INSTRUMENT_CATALOG)

    with database.session() as session:
        repository = PlatformRepository(session)
        master = InstrumentMaster(repository)
        assert master.resolve("  xBt  ").canonical_symbol == "BTC-USD"
        assert master.resolve("NQ", namespace="common").canonical_symbol == "NQ=F"
        assert master.resolve("missing") is None
        crypto = master.list(asset_class=AssetClass.CRYPTO)
        assert [item.canonical_symbol for item in crypto] == ["BTC-USD", "ETH-USD"]
        references = master.list(tradability=Tradability.REFERENCE_ONLY)
        assert {item.canonical_symbol for item in references} == {
            "ES=F",
            "NQ=F",
            "^GSPC",
            "^NDX",
        }
        assert {item.canonical_symbol for item in master.list(venue="CME")} == {
            "ES=F",
            "NQ=F",
        }
        btc = master.resolve("BTC")
        assert btc is not None
        aliases = repository.list_instrument_aliases(btc.instrument_id)
        assert {(item.namespace, item.alias) for item in aliases} >= {
            ("canonical", "BTC-USD"),
            ("common", "BTC"),
            ("common", "XBT"),
        }
    database.dispose()


@pytest.mark.unit
def test_unqualified_ambiguous_alias_fails_closed(tmp_path):
    url = f"sqlite:///{tmp_path / 'ambiguous.db'}"
    upgrade_database(url)
    database = Database(url)
    first = _instrument("FIRST")
    second = _instrument("SECOND")
    with database.session() as session:
        master = InstrumentMaster(PlatformRepository(session))
        master.register(first, (("vendor_one", "DUP"),))
        master.register(second, (("vendor_two", "DUP"),))

    with database.session() as session:
        master = InstrumentMaster(PlatformRepository(session))
        with pytest.raises(AmbiguousInstrumentAlias, match="namespace"):
            master.resolve("dup")
        assert master.resolve("dup", namespace="vendor_one") == first
        assert master.resolve("dup", namespace="vendor_two") == second
    database.dispose()


@pytest.mark.unit
def test_alias_cannot_shadow_another_canonical_instrument(tmp_path):
    url = f"sqlite:///{tmp_path / 'collision.db'}"
    upgrade_database(url)
    database = Database(url)
    first = _instrument("FIRST")
    second = _instrument("SECOND")
    with database.session() as session:
        master = InstrumentMaster(PlatformRepository(session))
        master.register(first)
        master.register(second)
        with pytest.raises(ImmutableRecordConflict, match="canonical"):
            master.register(first, (("common", "SECOND"),))
    database.dispose()


@pytest.mark.integration
def test_postgresql_instrument_master_bootstrap_lookup_and_filters():
    url = os.getenv("TEST_POSTGRES_URL")
    if not url:
        pytest.skip("TEST_POSTGRES_URL is required for the PostgreSQL integration gate")
    upgrade_database(url)
    database = Database(url)
    try:
        with database.session() as session:
            master = InstrumentMaster(PlatformRepository(session))
            master.bootstrap()
        with database.session() as session:
            master = InstrumentMaster(PlatformRepository(session))
            assert master.resolve("ETH", namespace="common").canonical_symbol == "ETH-USD"
            assert {item.canonical_symbol for item in master.list(venue="CME")} == {
                "ES=F",
                "NQ=F",
            }
    finally:
        database.dispose()
        downgrade_database(url)
