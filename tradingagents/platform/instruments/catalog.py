"""Deterministic bootstrap catalog for the initial private-platform boundary."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid5

from tradingagents.contracts import AssetClass, InstrumentContract, Tradability

INSTRUMENT_ID_NAMESPACE = UUID("9b20c71f-c1b0-4a02-a9a3-85d02be45c24")


def stable_instrument_id(
    *, asset_class: AssetClass, venue: str, canonical_symbol: str
) -> UUID:
    identity = f"{asset_class.value}|{venue.upper()}|{canonical_symbol.upper()}"
    return uuid5(INSTRUMENT_ID_NAMESPACE, identity)


@dataclass(frozen=True)
class InstrumentSeed:
    instrument: InstrumentContract
    aliases: tuple[tuple[str, str], ...] = ()


def _instrument(
    *,
    canonical_symbol: str,
    display_name: str,
    asset_class: AssetClass,
    tradability: Tradability,
    venue: str,
    quote_currency: str,
    timezone: str,
    session_calendar: str,
    benchmark_symbol: str | None,
    aliases: tuple[tuple[str, str], ...] = (),
) -> InstrumentSeed:
    return InstrumentSeed(
        instrument=InstrumentContract(
            instrument_id=stable_instrument_id(
                asset_class=asset_class,
                venue=venue,
                canonical_symbol=canonical_symbol,
            ),
            symbol=canonical_symbol,
            canonical_symbol=canonical_symbol,
            display_name=display_name,
            asset_class=asset_class,
            tradability=tradability,
            venue=venue,
            quote_currency=quote_currency,
            timezone=timezone,
            session_calendar=session_calendar,
            benchmark_symbol=benchmark_symbol,
        ),
        aliases=aliases,
    )


INITIAL_INSTRUMENT_CATALOG = (
    _instrument(
        canonical_symbol="AAPL",
        display_name="Apple Inc.",
        asset_class=AssetClass.EQUITY,
        tradability=Tradability.INVESTABLE,
        venue="NASDAQ",
        quote_currency="USD",
        timezone="America/New_York",
        session_calendar="XNAS",
        benchmark_symbol="SPY",
        aliases=(("yfinance", "AAPL"),),
    ),
    _instrument(
        canonical_symbol="SPY",
        display_name="SPDR S&P 500 ETF Trust",
        asset_class=AssetClass.ETF,
        tradability=Tradability.INVESTABLE,
        venue="NYSE_ARCA",
        quote_currency="USD",
        timezone="America/New_York",
        session_calendar="XNYS",
        benchmark_symbol="^GSPC",
        aliases=(("yfinance", "SPY"),),
    ),
    _instrument(
        canonical_symbol="QQQ",
        display_name="Invesco QQQ Trust",
        asset_class=AssetClass.ETF,
        tradability=Tradability.INVESTABLE,
        venue="NASDAQ",
        quote_currency="USD",
        timezone="America/New_York",
        session_calendar="XNAS",
        benchmark_symbol="^NDX",
        aliases=(("yfinance", "QQQ"),),
    ),
    _instrument(
        canonical_symbol="^GSPC",
        display_name="S&P 500 Index",
        asset_class=AssetClass.CASH_INDEX,
        tradability=Tradability.REFERENCE_ONLY,
        venue="INDEX",
        quote_currency="USD",
        timezone="America/New_York",
        session_calendar="XNYS",
        benchmark_symbol=None,
        aliases=(("yfinance", "^GSPC"), ("common", "SPX")),
    ),
    _instrument(
        canonical_symbol="^NDX",
        display_name="Nasdaq-100 Index",
        asset_class=AssetClass.CASH_INDEX,
        tradability=Tradability.REFERENCE_ONLY,
        venue="INDEX",
        quote_currency="USD",
        timezone="America/New_York",
        session_calendar="XNAS",
        benchmark_symbol="^GSPC",
        aliases=(("yfinance", "^NDX"), ("common", "NDX")),
    ),
    _instrument(
        canonical_symbol="NQ=F",
        display_name="E-mini Nasdaq-100 Futures Reference",
        asset_class=AssetClass.REFERENCE_FUTURE,
        tradability=Tradability.REFERENCE_ONLY,
        venue="CME",
        quote_currency="USD",
        timezone="America/Chicago",
        session_calendar="CME_Equity",
        benchmark_symbol="^NDX",
        aliases=(("yfinance", "NQ=F"), ("common", "NQ")),
    ),
    _instrument(
        canonical_symbol="ES=F",
        display_name="E-mini S&P 500 Futures Reference",
        asset_class=AssetClass.REFERENCE_FUTURE,
        tradability=Tradability.REFERENCE_ONLY,
        venue="CME",
        quote_currency="USD",
        timezone="America/Chicago",
        session_calendar="CME_Equity",
        benchmark_symbol="^GSPC",
        aliases=(("yfinance", "ES=F"), ("common", "ES")),
    ),
    _instrument(
        canonical_symbol="BTC-USD",
        display_name="Bitcoin",
        asset_class=AssetClass.CRYPTO,
        tradability=Tradability.INVESTABLE,
        venue="AGGREGATE",
        quote_currency="USD",
        timezone="UTC",
        session_calendar="24/7",
        benchmark_symbol=None,
        aliases=(("yfinance", "BTC-USD"), ("common", "BTC"), ("common", "XBT")),
    ),
    _instrument(
        canonical_symbol="ETH-USD",
        display_name="Ether",
        asset_class=AssetClass.CRYPTO,
        tradability=Tradability.INVESTABLE,
        venue="AGGREGATE",
        quote_currency="USD",
        timezone="UTC",
        session_calendar="24/7",
        benchmark_symbol="BTC-USD",
        aliases=(("yfinance", "ETH-USD"), ("common", "ETH")),
    ),
)
