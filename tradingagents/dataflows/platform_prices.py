"""Bounded Yahoo daily-price acquisition for current, immutable research evidence.

No model calls, historical-vintage claim, arbitrary symbols, or vendor fallback.
The subprocess isolates Yahoo's session/cache and enforces a total time budget.
"""

from __future__ import annotations

import contextlib
import json
import subprocess
import sys
from datetime import datetime, timedelta

import exchange_calendars
from dateutil.relativedelta import relativedelta

from tradingagents._compat import UTC
from tradingagents.contracts import (
    AssetClass,
    InstrumentContract,
    NormalizedTimeSeries,
    PriceInterval,
)
from tradingagents.platform.instruments.catalog import INITIAL_INSTRUMENT_CATALOG
from tradingagents.platform.market_data.timeseries import normalize_time_series

from .history_window import OHLCV_HISTORY_YEARS

# Acquisition-contract version prevents reusing the old one-year snapshots.
VENDOR = "yfinance.daily.v2"
DATASET = "ohlcv.daily"


def history_start(now: datetime) -> datetime:
    return now - relativedelta(years=OHLCV_HISTORY_YEARS)


class PricePreparationError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def approved_symbol(instrument: InstrumentContract) -> str:
    for seed in INITIAL_INSTRUMENT_CATALOG:
        if (
            seed.instrument == instrument
            and instrument.asset_class is not AssetClass.REFERENCE_FUTURE
        ):
            return dict(seed.aliases)["yfinance"]
    raise PricePreparationError("unsupported")


def session_closes(instrument: InstrumentContract, now: datetime) -> dict:
    approved_symbol(instrument)
    start = (history_start(now) - timedelta(days=2)).date()
    if instrument.asset_class is AssetClass.CRYPTO:
        return {
            start + timedelta(days=i): datetime.combine(
                start + timedelta(days=i + 1), datetime.min.time(), tzinfo=UTC
            )
            for i in range((now.date() - start).days + 3)
        }
    calendar = exchange_calendars.get_calendar(
        instrument.session_calendar,
        start=start.isoformat(),
        end=(now + timedelta(days=2)).date().isoformat(),
    )
    return {
        label.date(): close.to_pydatetime().astimezone(UTC)
        for label, close in calendar.closes.items()
    }


def normalize_yahoo(instrument, frame, metadata, *, now):
    symbol = approved_symbol(instrument)
    expected_type = {
        AssetClass.EQUITY: "EQUITY",
        AssetClass.ETF: "ETF",
        AssetClass.CASH_INDEX: "INDEX",
        AssetClass.CRYPTO: "CRYPTOCURRENCY",
    }[instrument.asset_class]
    if (
        metadata.get("symbol") != symbol
        or metadata.get("currency") != instrument.quote_currency
        or metadata.get("instrumentType") != expected_type
        or metadata.get("exchangeTimezoneName") != instrument.timezone
    ):
        raise PricePreparationError("invalid")
    if frame.empty:
        raise PricePreparationError("no_data")
    if (
        len(frame) > OHLCV_HISTORY_YEARS * 366 + 5
        or frame.index.tz is None
        or frame.index.has_duplicates
    ):
        raise PricePreparationError("invalid")
    closes = session_closes(instrument, now)
    # A completed session is usable only after a one-hour publication allowance.
    cutoff = now - timedelta(hours=1)
    expected = {
        day: close for day, close in closes.items() if history_start(now) <= close <= cutoff
    }
    bars = []
    try:
        for label, row in frame.iterrows():
            day = label.tz_convert(instrument.timezone).date()
            close = closes.get(day)
            if close is None:
                raise PricePreparationError("invalid")
            if close > cutoff or close < history_start(now):
                continue
            bars.append(
                {
                    "timestamp": close,
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": float(row["Volume"]),
                    "adjusted_close": float(row["Adj Close"]),
                }
            )
        if not bars:
            raise PricePreparationError("no_data")
        actual = {bar["timestamp"] for bar in bars}
        if max(actual) < max(expected.values()):
            raise PricePreparationError("stale")
        if actual != set(expected.values()):
            raise PricePreparationError("coverage_gap")
        return normalize_time_series(
            instrument=instrument,
            dataset=DATASET,
            interval=PriceInterval.ONE_DAY,
            as_of=now,
            annualization_periods=365 if instrument.asset_class is AssetClass.CRYPTO else 252,
            bars=bars,
        )
    except PricePreparationError:
        raise
    except (KeyError, TypeError, ValueError, OverflowError) as error:
        raise PricePreparationError("invalid") from error


def fetch_daily_prices(instrument: InstrumentContract) -> NormalizedTimeSeries:
    approved_symbol(instrument)
    try:
        result = subprocess.run(
            [sys.executable, "-m", __name__],
            input=instrument.model_dump_json(),
            text=True,
            capture_output=True,
            timeout=45,
            check=False,
        )
        if result.returncode or len(result.stdout) > 2_000_000:
            raise PricePreparationError("unavailable")
        value = json.loads(result.stdout)
        if "error" in value:
            code = value["error"]
            raise PricePreparationError(
                code
                if code
                in {"invalid", "no_data", "stale", "coverage_gap", "rate_limited", "unavailable"}
                else "unavailable"
            )
        series = NormalizedTimeSeries.model_validate(value)
        if series.instrument_id != instrument.instrument_id or series.dataset != DATASET:
            raise PricePreparationError("invalid")
        return series
    except PricePreparationError:
        raise
    except (subprocess.TimeoutExpired, OSError, ValueError) as error:
        raise PricePreparationError("unavailable") from error


def main():
    import yfinance as yf
    from yfinance.exceptions import YFPricesMissingError, YFRateLimitError

    try:
        instrument = InstrumentContract.model_validate_json(sys.stdin.read(16_384))
        with contextlib.redirect_stdout(sys.stderr):
            ticker = yf.Ticker(approved_symbol(instrument))
            frame = ticker.history(
                period=f"{OHLCV_HISTORY_YEARS}y",
                interval="1d",
                auto_adjust=False,
                actions=False,
                raise_errors=True,
                timeout=10,
            )
            series = normalize_yahoo(
                instrument, frame, ticker.history_metadata, now=datetime.now(UTC)
            )
        output = series.model_dump(mode="json")
    except YFRateLimitError:
        output = {"error": "rate_limited"}
    except YFPricesMissingError:
        # Yahoo also uses this exception for malformed/error responses. Only a
        # verified, empty history above establishes NO_DATA.
        output = {"error": "unavailable"}
    except PricePreparationError as error:
        output = {"error": error.code}
    except Exception:
        output = {"error": "unavailable"}
    print(json.dumps(output, allow_nan=False))


if __name__ == "__main__":
    main()
