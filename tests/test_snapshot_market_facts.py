"""Regression receipts for calendar endpoints, labels and grounded indicators."""

from datetime import timedelta
from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage

from tests.test_normalized_time_series import AS_OF, _instrument
from tradingagents.contracts import NormalizedTimeSeries
from tradingagents.graph.snapshot_analysis import snapshot_analyst_nodes
from tradingagents.platform.analysis.market_facts import SnapshotMarketFacts


def source(count=400, *, labels=True):
    instrument = _instrument(crypto=True)
    bars = []
    for i in range(count):
        timestamp = AS_OF - timedelta(days=count - i)
        price = 100 + i
        bars.append(dict(timestamp=timestamp.isoformat(), open=price, high=price + 2,
                         low=price - 2, close=price, volume=1000 + i,
                         **({"session_date": (timestamp - timedelta(days=1)).date().isoformat()} if labels else {})))
    return {"snapshot_id": str(uuid4()), "provenance": {
        "instrument_id": str(instrument.instrument_id), "dataset": "ohlcv.daily",
        "source_end": bars[-1]["timestamp"], "retrieved_at": AS_OF.isoformat()},
        "data": {"schema_version": "1.1" if labels else "1.0",
                 "instrument_id": str(instrument.instrument_id), "dataset": "ohlcv.daily",
                 "interval": "1d", "timezone": "UTC", "quote_currency": "USD",
                 "as_of": AS_OF.isoformat(), "annualization_periods": 365, "bars": bars}}


def test_session_label_is_not_close_instant_and_legacy_remains_readable():
    new = SnapshotMarketFacts(source()).summary()
    assert new["latest"]["session_date"] == "2026-09-18"
    assert new["latest"]["closed_at"].startswith("2026-09-19")
    old = SnapshotMarketFacts(source(labels=False)).summary()
    assert old["latest"]["session_date"] is None
    assert old["session_labels"] == "unavailable_in_legacy_snapshot"


@pytest.mark.parametrize("change", ["mixed", "duplicate", "old_schema", "missing"])
def test_session_schema_fails_closed(change):
    data = source()["data"]
    if change == "mixed":
        data["bars"][0].pop("session_date")
    elif change == "duplicate":
        data["bars"][0]["session_date"] = data["bars"][1]["session_date"]
    elif change == "old_schema":
        data["schema_version"] = "1.0"
    else:
        for bar in data["bars"]:
            bar.pop("session_date")
    with pytest.raises(ValueError):
        NormalizedTimeSeries.model_validate(data)


def test_calendar_returns_use_exact_explicit_endpoints_and_no_partial_history():
    facts = SnapshotMarketFacts(source())
    result = facts.calendar_return(365)
    assert result["start"]["close"] == 134
    assert result["end"]["close"] == 499
    assert result["return_pct"] == pytest.approx((499 / 134 - 1) * 100)
    assert result["elapsed_days"] == 365
    assert facts.calendar_return(500)["status"] == "insufficient_history"


def test_alternating_highs_lows_and_volume_are_not_consecutive_declines():
    value = source(5)
    highs = [120, 119, 121, 118, 122]
    lows = [90, 91, 89, 88, 92]
    for i, bar in enumerate(value["data"]["bars"]):
        bar.update(high=highs[i], low=lows[i], volume=[50, 40, 45, 30, 20][i])
    result = SnapshotMarketFacts(value).summary()
    assert result["recent_sequence"]["lower_high_pairs"] == [True, False, True, False]
    assert result["recent_sequence"]["lower_low_pairs"] == [False, True, True, False]
    assert result["recent_sequence"]["declining_volume_pairs"] == [True, False, True, True]
    assert result["observed_window_high"]["is_all_time_high"] is False


def test_indicator_uses_all_history_but_withholds_short_warmup():
    facts = SnapshotMarketFacts(source())
    assert facts.indicator("close_200_sma", offset=399, limit=1)["rows"][0]["value"] == pytest.approx(399.5)
    assert facts.indicator("close_200_sma", offset=198, limit=1)["rows"][0]["value"] is None
    assert facts.candles(offset=250, limit=250)["bars"][-1]["close"] == 499
    with pytest.raises(ValueError):
        facts.indicator("made_up_indicator")


def test_future_payload_cannot_hide_behind_valid_manifest():
    value = source()
    value["provenance"]["source_end"] = value["data"]["bars"][-2]["timestamp"]
    with pytest.raises(ValueError, match="cutoff"):
        SnapshotMarketFacts(value)


def test_snapshot_market_tools_run_without_fetching_live_data():
    import json
    value = source()
    calls = []

    class Model:
        def bind_tools(self, tools):
            assert {tool.name for tool in tools} == {"get_snapshot_candles", "get_snapshot_indicator", "get_snapshot_return"}
            return self

        def invoke(self, messages):
            calls.append(list(messages))
            if len(calls) == 1:
                return AIMessage(content="", tool_calls=[{"name": "get_snapshot_return", "id": "r1",
                    "args": {"snapshot_id": value["snapshot_id"], "calendar_days": 365}}])
            result = json.loads(messages[-1].content)
            assert result["return_pct"] == pytest.approx((499 / 134 - 1) * 100)
            return AIMessage(content="Evidence-based market report")

    node = snapshot_analyst_nodes(Model(), {"market": json.dumps([value])})["market"]
    result = node({"trade_date": "2026-09-20"})
    assert result["market_report"] == "Evidence-based market report"
    assert len(calls) == 2
    assert len(calls[0][1].content) < 20000
