"""Structured FRED fixture evidence, not live availability or web acceptance."""

from copy import deepcopy
from datetime import datetime, timedelta

import pytest

from tests.test_price_preparation import AAPL
from tradingagents._compat import UTC
from tradingagents.contracts import DataQualityStatus
from tradingagents.dataflows.fred import FredNotConfiguredError
from tradingagents.dataflows.platform_fred import (
    FRESHNESS_DAYS,
    MAX_OBSERVATIONS,
    MacroCollection,
    collect_fred_series,
)

NOW = datetime(2026, 10, 3, 5, 0, tzinfo=UTC)  # Chicago midnight, previous day fully elapsed.
VINTAGE = "2026-10-02"


def documents(*, rows=None, frequency="D"):
    realtime = {"realtime_start": VINTAGE, "realtime_end": VINTAGE}
    info = {"id": "DGS10", "title": "Ten-Year Treasury Yield", "units": "Percent",
            "frequency": "Daily", "frequency_short": frequency,
            "seasonal_adjustment": "Not Seasonally Adjusted", **realtime}
    points = ([{"date": VINTAGE, "value": "4.25", **realtime}] if rows is None else rows)
    return {"series": {"seriess": [info], **realtime},
        "series/observations": {"observations": points, "count": len(points),
            "offset": 0, "limit": MAX_OBSERVATIONS, "units": "lin", "output_type": 1,
            "sort_order": "asc", "observation_start": "2025-10-02",
            "observation_end": VINTAGE, **realtime}}


def collect(raw=None, **kwargs):
    raw = documents() if raw is None else raw
    return collect_fred_series(AAPL, "DGS10", clock=lambda: NOW,
        request=lambda path, params: deepcopy(raw[path]), **kwargs)


def test_full_vintage_pinned_wire_requests_and_identity():
    raw, calls = documents(), []

    def request(path, params):
        calls.append((path, params))
        return deepcopy(raw[path])

    value = collect_fred_series(AAPL, "DGS10", clock=lambda: NOW, request=request)
    assert value.quality_status is DataQualityStatus.OK
    assert value.instrument_id == AAPL.instrument_id and value.canonical_symbol == "AAPL"
    assert value.observations[0].value == 4.25 and value.units == "Percent"
    assert value.vintage_available_at == NOW
    assert value.retrieved_at == NOW and value.analysis_as_of == NOW
    assert len(calls) == 2
    for _, params in calls:
        assert params["series_id"] == "DGS10"
        assert params["realtime_start"] == params["realtime_end"] == VINTAGE
        assert "api_key" not in params  # Only the existing request boundary obtains it.
    query = calls[1][1]
    assert query["observation_start"] == "2025-10-02" and query["observation_end"] == VINTAGE
    assert query["limit"] == MAX_OBSERVATIONS and query["offset"] == 0
    assert query["units"] == "lin" and query["output_type"] == 1


def test_full_history_retained_not_cli_display_cap():
    raw = documents()
    rows = [{"date": (NOW.date() - timedelta(days=101 - index)).isoformat(),
             "value": "." if index == 4 else str(index + .25),
             "realtime_start": VINTAGE, "realtime_end": VINTAGE} for index in range(101)]
    raw["series/observations"].update(observations=rows, count=len(rows))
    value = collect(raw)
    assert value.quality_status is DataQualityStatus.OK and len(value.observations) == 101
    assert value.observations[4].value is None
    assert value.observations[0].observation_date.isoformat() == rows[0]["date"]
    assert value.observations[-1].observation_date.isoformat() == VINTAGE
    assert MacroCollection.model_validate_json(value.model_dump_json()) == value


@pytest.mark.parametrize("wrong_vintage", [False, True])
def test_empty_metadata_is_validated_before_observation_fetch(wrong_vintage):
    raw = documents()
    raw["series"]["seriess"] = []
    if wrong_vintage:
        raw["series"]["realtime_end"] = "2026-10-03"

    def metadata_only(path, params):
        assert path == "series", "No observations request without valid series metadata"
        return raw[path]

    value = collect_fred_series(AAPL, "DGS10", clock=lambda: NOW, request=metadata_only)
    assert value.quality_status is (DataQualityStatus.INVALID if wrong_vintage else DataQualityStatus.NO_DATA)


@pytest.mark.parametrize("time,expected", [
    (datetime(2026, 10, 3, 4, 59, 59, tzinfo=UTC), "2026-10-01"),
    (datetime(2026, 10, 3, 5, 0, tzinfo=UTC), "2026-10-02"),
    (datetime(2026, 3, 8, 6, 0, tzinfo=UTC), "2026-03-07"),
    (datetime(2026, 3, 9, 5, 0, tzinfo=UTC), "2026-03-08"),
    (datetime(2026, 11, 2, 6, 0, tzinfo=UTC), "2026-11-01"),
])
def test_chicago_complete_vintage_boundaries_and_dst(time, expected):
    calls = []

    def offline(path, params):
        calls.append(params)
        raise RuntimeError("synthetic unavailable vendor")

    value = collect_fred_series(AAPL, "DGS10", clock=lambda: time, request=offline)
    assert value.quality_status is DataQualityStatus.UNAVAILABLE
    assert value.vintage_date.isoformat() == expected
    assert value.vintage_available_at <= time
    assert calls[0]["realtime_end"] == expected


@pytest.mark.parametrize("failure,reason", [
    (FredNotConfiguredError("PRIVATE_DO_NOT_ECHO"), "fred_not_configured"),
    (RuntimeError("https://vendor.invalid?api_key=PRIVATE_DO_NOT_ECHO"), "vendor_request_failed"),
])
def test_configuration_outage_is_not_empty_or_neutral(failure, reason):
    def offline(*_):
        raise failure

    value = collect_fred_series(AAPL, "DGS10", clock=lambda: NOW, request=offline)
    assert value.quality_status is DataQualityStatus.UNAVAILABLE and value.reason == reason
    assert value.observations == () and "PRIVATE_DO_NOT_ECHO" not in value.model_dump_json()


@pytest.mark.parametrize("case,status,reason", [
    ("series_empty", DataQualityStatus.NO_DATA, "series_not_found"),
    ("empty_window", DataQualityStatus.COVERAGE_GAP, "empty_vintage_window"),
    ("missing", DataQualityStatus.NO_DATA, "only_missing_observations"),
    ("stale", DataQualityStatus.STALE, "stale_observations"),
])
def test_distinct_missing_coverage_and_staleness(case, status, reason):
    raw = documents()
    if case == "series_empty":
        raw["series"]["seriess"] = []
    elif case == "empty_window":
        raw["series/observations"].update(observations=[], count=0)
    elif case == "missing":
        raw["series/observations"]["observations"][0]["value"] = "."
    else:
        raw["series/observations"]["observations"][0]["date"] = "2026-01-01"
    value = collect(raw)
    assert value.quality_status is status and value.reason == reason
    assert (len(value.observations) == 1) is (case in {"missing", "stale"})


@pytest.mark.parametrize("case", [
    "wrong_series", "wrong_vintage", "metadata_vintage", "missing_units", "frequency",
    "partial_page", "bool_count", "nonzero_offset", "wrong_limit", "scaled_units",
    "revision_output", "reverse_order", "future_observation", "old_observation",
    "future_revision", "duplicate", "numeric_date", "nan", "inf", "bool_value",
    "empty_value", "unknown_row", "not_dict", "oversized",
])
def test_malformed_or_future_leaking_response_withholds_all_rows(case):
    raw = documents()
    info = raw["series"]["seriess"][0]
    envelope = raw["series/observations"]
    point = envelope["observations"][0]
    if case == "wrong_series":
        info["id"] = "OTHER"
    elif case == "wrong_vintage":
        envelope["realtime_start"] = "2026-10-03"
    elif case == "metadata_vintage":
        info["realtime_end"] = "2026-10-03"
    elif case == "missing_units":
        info["units"] = ""
    elif case == "frequency":
        info["frequency_short"] = "UNKNOWN"
    elif case == "partial_page":
        envelope["count"] = 2
    elif case == "bool_count":
        envelope["count"] = True
    elif case == "nonzero_offset":
        envelope["offset"] = 1
    elif case == "wrong_limit":
        envelope["limit"] = 40
    elif case == "scaled_units":
        envelope["units"] = "pc1"
    elif case == "revision_output":
        envelope["output_type"] = 3
    elif case == "reverse_order":
        envelope["sort_order"] = "desc"
    elif case == "future_observation":
        point["date"] = "2026-10-03"
    elif case == "old_observation":
        point["date"] = "2020-01-01"
    elif case == "future_revision":
        point["realtime_start"] = "2026-10-03"
    elif case == "duplicate":
        envelope["observations"].append(deepcopy(point))
        envelope["count"] = 2
    elif case == "numeric_date":
        point["date"] = 0
    elif case in {"nan", "inf", "bool_value", "empty_value"}:
        point["value"] = {"nan": "NaN", "inf": "1e309", "bool_value": True, "empty_value": ""}[case]
    elif case == "unknown_row":
        envelope["observations"] = [{}]
    elif case == "not_dict":
        raw["series"] = []
    else:
        raw["series"]["untrusted_text"] = "x" * 2_000_000
    value = collect(raw)
    assert value.quality_status is DataQualityStatus.INVALID
    assert value.reason == "invalid_vendor_response" and value.observations == ()


@pytest.mark.parametrize("kwargs", [
    {"series_id": "../DGS10"}, {"series_id": "https://other.invalid"},
    {"series_id": "DGS10?api_key=synthetic"}, {"series_id": "dgs10"},
    {"lookback_days": True}, {"lookback_days": 0}, {"lookback_days": 36526},
    {"analysis_as_of": NOW + timedelta(seconds=1)}, {"analysis_as_of": NOW.replace(tzinfo=None)},
])
def test_invalid_input_refuses_before_network(kwargs):
    kwargs = dict(kwargs)
    series_id = kwargs.pop("series_id", "DGS10")

    def forbidden(*_):
        pytest.fail("invalid input invoked vendor")

    with pytest.raises(ValueError):
        collect_fred_series(AAPL, series_id, clock=lambda: NOW, request=forbidden, **kwargs)


@pytest.mark.parametrize("update", [
    {"quality_status": DataQualityStatus.INVALID, "observations": ()},
    {"vintage_available_at": NOW - timedelta(seconds=1)},
    {"analysis_as_of": NOW - timedelta(seconds=1)},
    {"quality_status": DataQualityStatus.NO_DATA},
])
def test_copied_collection_must_revalidate_derived_status_and_vintage(update):
    value = collect().model_copy(update=update)
    with pytest.raises(ValueError):
        MacroCollection.model_validate(value.model_dump())


@pytest.mark.parametrize("frequency,limit", FRESHNESS_DAYS.items())
@pytest.mark.parametrize("extra_days", [0, 1])
def test_fresh_vintage_does_not_hide_stale_observation_period(frequency, limit, extra_days):
    raw = documents(frequency=frequency)
    raw["series/observations"]["observations"][0]["date"] = (
        NOW.date() - timedelta(days=1 + limit + extra_days)).isoformat()
    # Wider explicit window only for low-frequency period tests, never a truncation.
    raw["series/observations"]["observation_start"] = "2021-10-03"
    value = collect(raw, lookback_days=1825)
    assert value.quality_status is (DataQualityStatus.STALE if extra_days else DataQualityStatus.OK)
    assert len(value.observations) == 1 and value.vintage_available_at == NOW


@pytest.mark.parametrize("field", ["title", "units", "frequency", "frequency_short", "seasonal_adjustment"])
@pytest.mark.parametrize("all_missing", [False, True])
def test_collection_copy_requires_metadata_even_for_missing_rows(field, all_missing):
    raw = documents()
    if all_missing:
        raw["series/observations"]["observations"][0]["value"] = "."
    value = collect(raw).model_copy(update={field: ""})
    with pytest.raises(ValueError, match="metadata"):
        MacroCollection.model_validate(value.model_dump())


@pytest.mark.parametrize("failure,reason", [
    (FredNotConfiguredError("PRIVATE_DO_NOT_ECHO"), "fred_not_configured"),
    (RuntimeError("https://vendor.invalid?api_key=PRIVATE_DO_NOT_ECHO"), "vendor_request_failed"),
])
def test_observation_request_failure_discards_metadata_and_rows(failure, reason):
    raw = documents()

    def fail_observations(path, params):
        if path == "series":
            return raw[path]
        raise failure

    value = collect_fred_series(AAPL, "DGS10", clock=lambda: NOW, request=fail_observations)
    assert value.quality_status is DataQualityStatus.UNAVAILABLE and value.reason == reason
    assert value.observations == () and "PRIVATE_DO_NOT_ECHO" not in value.model_dump_json()
