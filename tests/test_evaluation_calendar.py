from datetime import datetime

import pytest

from tests.test_analysis_engine import _instrument
from tradingagents._compat import UTC
from tradingagents.contracts import AssetClass
from tradingagents.platform.evaluation.calendar import evaluation_session_window


def stamp(text):
    return datetime.fromisoformat(text).replace(tzinfo=UTC)


def window(start, end, count=1, instrument=None):
    return evaluation_session_window(instrument=instrument or _instrument(),
        decision_at=stamp(start), evaluated_at=stamp(end), holding_sessions=count)


def test_thanksgiving_and_early_close_are_calendar_driven():
    result = window("2026-11-25T21:00", "2026-12-01T22:00")
    assert result.session_closes == (stamp("2026-11-27T18:00"), stamp("2026-11-30T21:00"))
    assert result.engine_version == "exchange-calendars:4.12"
    assert result == window("2026-11-25T21:00", "2026-12-01T22:00")
    assert result.content_hash.startswith("sha256:")


def test_dst_changes_utc_close_and_entry_is_strictly_after_decision():
    result = window("2026-03-06T20:59", "2026-03-10T21:00")
    assert result.session_closes == (stamp("2026-03-06T21:00"), stamp("2026-03-09T20:00"))


def test_crypto_keeps_weekend_sessions_at_utc_midnight():
    result = window("2026-09-25T12:00", "2026-09-28T01:00", instrument=_instrument(AssetClass.CRYPTO))
    assert result.session_closes == (stamp("2026-09-26T00:00"), stamp("2026-09-27T00:00"))


def test_unsettled_or_invalid_windows_fail_closed():
    with pytest.raises(ValueError, match="not settled"):
        window("2026-11-25T21:00", "2026-11-27T17:59")
    with pytest.raises(ValueError, match="integer"):
        window("2026-09-25T12:00", "2026-09-28T01:00", count=True)
    with pytest.raises(ValueError, match="calendar identity"):
        window("2026-09-25T12:00", "2026-09-28T01:00",
               instrument=_instrument().model_copy(update={"session_calendar": "unknown"}))


def test_calendar_bound_outcome_uses_expected_sessions_and_hashes():
    from datetime import timedelta

    from tests.test_evaluation_outcomes import _snapshot
    from tests.test_historical_evaluation import NOW, _decision
    from tradingagents.platform.evaluation.outcomes import calendar_snapshot_outcome

    decision = _decision()
    instrument = _instrument(AssetClass.CRYPTO).model_copy(update={"instrument_id": decision.instrument_id})
    benchmark = _instrument(AssetClass.CRYPTO)
    args = {"decision": decision, "instrument": instrument, "benchmark_instrument": benchmark,
            "asset": _snapshot(instrument.instrument_id),
            "benchmark": _snapshot(benchmark.instrument_id, (100, 101, 102)),
            "holding_sessions": 1, "evaluated_at": NOW + timedelta(days=4)}
    observation, windows = calendar_snapshot_outcome(**args)
    assert observation.raw_return == pytest.approx(.05)
    assert observation.benchmark_return == pytest.approx(.01)
    assert len(windows[0].session_closes) == 2
    assert calendar_snapshot_outcome(**args) == (observation, windows)
