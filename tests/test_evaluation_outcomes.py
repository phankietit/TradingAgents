import hashlib
import json
from datetime import timedelta
from uuid import uuid4

import pytest

from tests.test_historical_evaluation import NOW, _decision
from tradingagents.contracts import (
    DataQualityStatus,
    NormalizedTimeSeries,
    OHLCVBar,
    SnapshotManifest,
)
from tradingagents.platform.evaluation.outcomes import snapshot_outcome


def _snapshot(instrument, prices=(100, 105, 110), **overrides):
    bars = tuple(OHLCVBar(timestamp=NOW + timedelta(days=i + 1),
                          open=p, high=p, low=p, close=p, volume=100)
                 for i, p in enumerate(prices))
    series = NormalizedTimeSeries(instrument_id=instrument, dataset="daily_prices",
                                  interval="1d", timezone="UTC", quote_currency="USD",
                                  as_of=bars[-1].timestamp, annualization_periods=365,
                                  bars=bars, **overrides)
    payload = json.dumps(series.model_dump(mode="json"), sort_keys=True,
                         separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    manifest = SnapshotManifest(snapshot_id=uuid4(), instrument_id=instrument,
                                dataset=series.dataset, vendor="fixture",
                                as_of=series.as_of, retrieved_at=series.as_of,
                                source_start=bars[0].timestamp, source_end=bars[-1].timestamp,
                                content_hash="sha256:" + hashlib.sha256(payload).hexdigest(),
                                quality_status="OK")
    return manifest, series


def _inputs():
    decision = _decision()
    return {"decision": decision, "asset": _snapshot(decision.instrument_id),
            "benchmark": _snapshot(uuid4(), (100, 101, 102)),
            "session_closes": tuple(NOW + timedelta(days=i) for i in (1, 2, 3)),
            "evaluated_at": NOW + timedelta(days=4)}


def test_verified_outcome_returns_and_replay():
    inputs = _inputs()
    result = snapshot_outcome(**inputs)
    assert result == snapshot_outcome(**inputs)
    assert result.raw_return == pytest.approx(.10)
    assert result.benchmark_return == pytest.approx(.02)
    assert result.holding_period_days == 2
    assert result.outcome_snapshot_ids == (inputs["asset"][0].snapshot_id,
                                           inputs["benchmark"][0].snapshot_id)


@pytest.mark.parametrize("mutation,match", [
    ({"content_hash": "sha256:" + "0" * 64}, "hash mismatch"),
    ({"retrieved_at": NOW + timedelta(days=5)}, "not available"),
    ({"retrieved_at": NOW}, "time mismatch"),
    ({"quality_status": DataQualityStatus.STALE}, "not available"),
    ({"source_start": NOW}, "time mismatch"),
])
def test_invalid_provenance_fails_closed(mutation, match):
    inputs = _inputs()
    manifest, series = inputs["asset"]
    inputs["asset"] = (manifest.model_copy(update=mutation), series)
    with pytest.raises(ValueError, match=match):
        snapshot_outcome(**inputs)


def test_missing_sessions_and_future_window_are_rejected():
    inputs = _inputs()
    inputs["session_closes"] = (NOW + timedelta(days=1, hours=1), NOW + timedelta(days=3))
    with pytest.raises(ValueError, match="coverage"):
        snapshot_outcome(**inputs)
    inputs["session_closes"] = (NOW, NOW + timedelta(days=3))
    with pytest.raises(ValueError, match="window"):
        snapshot_outcome(**inputs)


def test_benchmark_must_be_distinct():
    inputs = _inputs()
    inputs["benchmark"] = inputs["asset"]
    with pytest.raises(ValueError, match="distinct"):
        snapshot_outcome(**inputs)
