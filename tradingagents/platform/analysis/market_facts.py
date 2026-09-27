"""Deterministic, provenance-bound calculations over immutable price evidence.

No vendor calls, interpolation, gap filling or LLM arithmetic. All supplied
history remains available to the analyst's read-only tools.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from math import isfinite

import pandas as pd
from stockstats import wrap

from tradingagents.contracts import NormalizedTimeSeries, PriceInterval
from tradingagents.dataflows.market_data_validator import DEFAULT_SNAPSHOT_INDICATORS

# Match the repository's indicator implementation, but explicitly withhold
# early-window values that stockstats would otherwise emit with partial data.
WARMUP = {
    "close_10_ema": 10, "close_50_sma": 50, "close_200_sma": 200,
    "rsi": 15, "boll": 20, "boll_ub": 20, "boll_lb": 20,
    "macd": 26, "macds": 35, "macdh": 35, "atr": 15, "vwma": 14,
}


class SnapshotMarketFacts:
    def __init__(self, source: dict):
        self.snapshot_id = source["snapshot_id"]
        self.provenance = source["provenance"]
        self.series = NormalizedTimeSeries.model_validate(source["data"])
        if self.series.interval is not PriceInterval.ONE_DAY:
            raise ValueError("verified market facts require daily candles")
        if str(self.series.instrument_id) != self.provenance["instrument_id"]:
            raise ValueError("price payload instrument differs from provenance")
        source_end = datetime.fromisoformat(self.provenance["source_end"].replace("Z", "+00:00"))
        retrieved = datetime.fromisoformat(self.provenance["retrieved_at"].replace("Z", "+00:00"))
        if self.series.bars[-1].timestamp > source_end or self.series.as_of > retrieved:
            raise ValueError("price payload exceeds provenance cutoff")
        self.bars = self.series.bars
        self.frame = wrap(pd.DataFrame([
            {"open": b.open, "high": b.high, "low": b.low,
             "close": b.close, "volume": b.volume} for b in self.bars
        ]))

    def point(self, index: int) -> dict:
        bar = self.bars[index]
        # Do not reinterpret old artifacts. Their timestamp is the close
        # instant, not a vendor session label; display that distinction.
        return {"closed_at": bar.timestamp.isoformat(),
                "session_date": bar.session_date.isoformat() if bar.session_date else None,
                "open": bar.open, "high": bar.high, "low": bar.low,
                "close": bar.close, "adjusted_close": bar.adjusted_close,
                "volume": bar.volume}

    def indicator(self, name: str, *, offset: int = 0, limit: int = 30) -> dict:
        if name not in WARMUP:
            raise ValueError("unsupported indicator")
        if not 0 <= offset < len(self.bars) or not 1 <= limit <= 250:
            raise ValueError("invalid indicator page")
        values = self.frame[name]
        rows = []
        for i in range(offset, min(offset + limit, len(self.bars))):
            value = float(values.iloc[i])
            ready = i + 1 >= WARMUP[name] and isfinite(value)
            rows.append({"closed_at": self.bars[i].timestamp.isoformat(),
                         "fact_id": f"history.{i}.indicator.{name}",
                         "value": value if ready else None,
                         "status": "available" if ready else "insufficient_warmup"})
        return {"snapshot_id": self.snapshot_id, "indicator": name,
                "implementation": "stockstats", "price_basis": "unadjusted_ohlcv",
                "minimum_observations": WARMUP[name], "offset": offset,
                "total_observations": len(self.bars), "rows": rows}

    def candles(self, *, offset: int = 0, limit: int = 100) -> dict:
        if not 0 <= offset < len(self.bars) or not 1 <= limit <= 250:
            raise ValueError("invalid candle page")
        end = min(offset + limit, len(self.bars))
        return {"snapshot_id": self.snapshot_id, "offset": offset,
                "total_observations": len(self.bars),
                "next_offset": end if end < len(self.bars) else None,
                "bars": [{**self.point(i), "fact_prefix": f"history.{i}.candle"} for i in range(offset, end)]}

    def calendar_return(self, days: int) -> dict:
        if not 1 <= days <= 36500:
            raise ValueError("invalid calendar return horizon")
        end = self.bars[-1]
        target = end.timestamp - timedelta(days=days)
        candidates = [i for i, b in enumerate(self.bars) if b.timestamp <= target]
        result = {"snapshot_id": self.snapshot_id, "calendar_days": days,
                  "fact_id": f"return.{days}_calendar_days.pct",
                  "target_closed_at": target.isoformat(),
                  "endpoint_rule": "last_close_on_or_before_calendar_target",
                  "price_basis": self.series.price_basis.value,
                  "end": self.point(len(self.bars) - 1)}
        if not candidates:
            return {**result, "status": "insufficient_history", "return_pct": None, "start": None}
        i = candidates[-1]
        start = self.bars[i]
        start_price = start.adjusted_close if start.adjusted_close is not None else start.close
        end_price = end.adjusted_close if end.adjusted_close is not None else end.close
        return {**result, "status": "available", "start": self.point(i),
                "return_pct": (end_price / start_price - 1) * 100,
                "elapsed_days": (end.timestamp - start.timestamp).total_seconds() / 86400}

    def summary(self) -> dict:
        n = len(self.bars)
        recent = self.bars[-5:]
        high_index = max(range(n), key=lambda i: self.bars[i].high)
        high = self.bars[high_index].high
        return {
            "calculation_version": "snapshot-market-facts-v4",
            "snapshot_id": self.snapshot_id, "provenance": self.provenance,
            "fact_catalog": self.fact_catalog(),
            "quote_currency": self.series.quote_currency,
            "observations": n, "first": self.point(0), "latest": self.point(n - 1),
            "timestamp_semantics": "candle_close_instant_not_session_date",
            "session_labels": "explicit" if self.bars[-1].session_date else "unavailable_in_legacy_snapshot",
            "indicators": {name: self.indicator(name, offset=n - 1, limit=1)
                           for name in DEFAULT_SNAPSHOT_INDICATORS},
            "calendar_returns": [self.calendar_return(days) for days in (7, 30, 90, 365)],
            "observed_window_high": {"point": self.point(high_index),
                "latest_close_vs_high_pct": (self.bars[-1].close / high - 1) * 100,
                "is_all_time_high": False, "price_basis": "unadjusted_high_and_close"},
            "recent_sequence": {
                "bars": [self.point(i) for i in range(max(0, n - 5), n)],
                "lower_high_pairs": [b.high < a.high for a, b in zip(recent, recent[1:], strict=False)],
                "lower_low_pairs": [b.low < a.low for a, b in zip(recent, recent[1:], strict=False)],
                "declining_volume_pairs": [b.volume < a.volume for a, b in zip(recent, recent[1:], strict=False)],
            },
            "limitations": [
                "Observed-window high is not an all-time high.",
                "Indicators use raw OHLCV, returns use adjusted close when supplied; do not conflate bases.",
                "No interpolation, synthetic candles, annualized return or portfolio sizing is performed.",
                "distance_from_latest_close_pct uses latest close as denominator; latest_close_vs_indicator_pct uses the indicator as denominator. They are not interchangeable.",
            ],
        }

    def fact_catalog(self) -> dict:
        n = len(self.bars)
        latest = self.bars[-1]
        facts = {f"latest.{name}": getattr(latest, name) for name in ("open", "high", "low", "close", "volume")}
        for name in DEFAULT_SNAPSHOT_INDICATORS:
            value = self.indicator(name, offset=n - 1, limit=1)["rows"][0]["value"]
            if value is not None:
                facts[f"indicator.{name}"] = value
        for days in (7, 30, 90, 365):
            result = self.calendar_return(days)
            if result["return_pct"] is not None:
                facts[f"return.{days}_calendar_days.pct"] = result["return_pct"]
        high = max(bar.high for bar in self.bars)
        facts["observed_window.high"] = high
        facts["observed_window.latest_close_vs_high_pct"] = (latest.close / high - 1) * 100
        facts["observed_window.drawdown_magnitude_pct"] = (1 - latest.close / high) * 100
        for name in DEFAULT_SNAPSHOT_INDICATORS:
            value = facts.get(f"indicator.{name}")
            if value is not None:
                # RSI is a dimensionless oscillator, not an amount in quote
                # currency. Dividing it by the close is not a price percentage.
                if self._fact_unit(f"indicator.{name}") == "price":
                    facts[f"indicator.{name}.pct_of_latest_close"] = value / latest.close * 100
                if name in {"close_10_ema", "close_50_sma", "close_200_sma", "boll", "boll_ub", "boll_lb"}:
                    facts[f"indicator.{name}.distance_from_latest_close_pct"] = (value / latest.close - 1) * 100
                    if value > 0:
                        relative = (latest.close / value - 1) * 100
                        facts[f"indicator.{name}.latest_close_vs_indicator_pct"] = relative
                        facts[f"indicator.{name}.latest_close_distance_magnitude_pct"] = abs(relative)
        return facts

    def resolve_fact(self, fact_id: str):
        """Replay explicit tool-returned fact IDs without expanding the prompt.

        History indices are immutable snapshot positions, not vendor labels.
        Unknown IDs and incomplete warmup resolve to no fact, never a default.
        """
        import re

        window = re.fullmatch(r"window\.(\d+)\.(candle|indicator)\.([a-z0-9_]+)\.(min|max)", fact_id)
        if window:
            count, kind, name, aggregation = window.groups()
            count = int(count)
            if not 1 <= count <= len(self.bars):
                return None
            # Require the entire requested observation window, including warmup.
            values = [self.resolve_fact(f"history.{index}.{kind}.{name}")
                      for index in range(len(self.bars) - count, len(self.bars))]
            if any(value is None for value in values):
                return None
            return (min if aggregation == "min" else max)(values)
        # A tiny expression language, never eval: operands must themselves be
        # immutable fact IDs. No literals, nesting, cross-snapshot mixing or
        # implicit percentage conversion is accepted.
        calculation = re.fullmatch(r"calc\.(difference|ratio|pct_change|abs_pct_change|atr_distance)\(([a-z0-9_.]+),([a-z0-9_.]+)\)", fact_id)
        if calculation:
            operation, left_id, right_id = calculation.groups()
            left, right = self.resolve_fact(left_id), self.resolve_fact(right_id)
            if left is None or right is None or self._fact_unit(left_id) != self._fact_unit(right_id):
                return None
            if operation == "difference":
                value = left - right
            elif operation == "atr_distance":
                atr = self.resolve_fact("indicator.atr")
                if self._fact_unit(left_id) != "price" or atr is None or atr <= 0:
                    return None
                value = (left - right) / atr
            elif operation == "ratio":
                if right == 0:
                    return None
                value = left / right
            else:
                # Percentage change against a non-positive baseline is not a
                # conventional return; do not emit a misleading percentage.
                if right <= 0:
                    return None
                value = (left / right - 1) * 100
                if operation == "abs_pct_change":
                    value = abs(value)
            return value if isfinite(value) else None
        match = re.fullmatch(r"history\.(\d+)\.(candle|indicator)\.([a-z0-9_]+)", fact_id)
        if match:
            index, kind, name = int(match[1]), match[2], match[3]
            if index >= len(self.bars):
                return None
            if kind == "candle" and name in {"open", "high", "low", "close", "volume", "adjusted_close"}:
                return getattr(self.bars[index], name)
            if kind == "indicator" and name in WARMUP:
                return self.indicator(name, offset=index, limit=1)["rows"][0]["value"]
            return None
        match = re.fullmatch(r"return\.(\d+)_calendar_days\.pct", fact_id)
        if match and 1 <= int(match[1]) <= 36500:
            return self.calendar_return(int(match[1]))["return_pct"]
        return self.fact_catalog().get(fact_id)

    @staticmethod
    def _fact_unit(fact_id):
        if fact_id.startswith("window."):
            fact_id = fact_id.rsplit(".", 1)[0]
        if fact_id.endswith(".pct") or fact_id.endswith("_pct") or fact_id.endswith(".pct_of_latest_close"):
            return "percent"
        if fact_id.endswith(".volume"):
            return "volume"
        if fact_id.endswith(".rsi"):
            return "oscillator"
        return "price"

    def chart(self) -> dict:
        """Full observed history for the saved report, never a live-price query."""
        return {"snapshot_id": self.snapshot_id, "quote_currency": self.series.quote_currency,
                "price_basis": self.series.price_basis.value,
                "points": [{"closed_at": bar.timestamp.isoformat(),
                            "session_date": bar.session_date.isoformat() if bar.session_date else None,
                            "price": bar.adjusted_close if bar.adjusted_close is not None else bar.close}
                           for bar in self.bars]}
