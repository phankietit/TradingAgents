"""Structured FRED collection; no default web/CLI activation or historical rewrite.

Reuse the existing configured FRED request boundary. A complete Chicago vintage
day is conservative availability, not an exact publication/revision timestamp.
Full returned history is retained, including explicit missing observations.
"""

import json
import math
import re
from datetime import date, datetime, time, timedelta
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from tradingagents._compat import UTC
from tradingagents.contracts import DataQualityStatus, InstrumentContract
from tradingagents.dataflows.fred import (
    DEFAULT_LOOKBACK_DAYS,
    FRED_TZ,
    FredNotConfiguredError,
    _request,
)

MAX_OBSERVATIONS = 100_000
MAX_RESPONSE_BYTES = 2_000_000
FRESHNESS_DAYS = {"D": 14, "W": 28, "BW": 42, "M": 100, "Q": 210, "SA": 400, "A": 800}


def vintage_available_at(vintage: date) -> datetime:
    # pytz localize, not replace(tzinfo=...), preserves actual DST offsets.
    return FRED_TZ.localize(datetime.combine(vintage + timedelta(days=1), time.min)).astimezone(UTC)


class MacroObservation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    observation_date: date
    value: float | None = Field(allow_inf_nan=False, strict=True)
    realtime_start: date
    realtime_end: date


class MacroCollection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    dataset: Literal["macro"] = "macro"
    vendor: Literal["fred"] = "fred"
    retrieval_path: Literal["series+series/observations"] = "series+series/observations"
    instrument_id: UUID
    canonical_symbol: str
    asset_class: str
    venue: str
    quote_currency: str
    timezone: str
    series_id: str = Field(pattern=r"^[A-Z0-9_]{1,30}$")
    title: str = Field(default="", max_length=1000)
    units: str = Field(default="", max_length=200)
    frequency: str = Field(default="", max_length=100)
    frequency_short: str = Field(default="", max_length=2)
    seasonal_adjustment: str = Field(default="", max_length=200)
    requested_at: AwareDatetime
    analysis_as_of: AwareDatetime
    retrieved_at: AwareDatetime
    vintage_date: date
    vintage_available_at: AwareDatetime
    observation_start: date
    observation_end: date
    coverage: Literal["requested_series_vintage_not_all_macro"] = "requested_series_vintage_not_all_macro"
    quality_status: DataQualityStatus
    reason: Literal["eligible_complete_vintage", "fred_not_configured", "vendor_request_failed",
                    "invalid_vendor_response", "series_not_found", "empty_vintage_window",
                    "only_missing_observations", "stale_observations"]
    observations: tuple[MacroObservation, ...] = ()

    @model_validator(mode="after")
    def eligible(self):
        if (not self.analysis_as_of <= self.requested_at <= self.retrieved_at
                or self.observation_end != self.vintage_date
                or self.observation_start > self.observation_end
                or self.vintage_available_at != vintage_available_at(self.vintage_date)
                or self.vintage_available_at > self.analysis_as_of):
            raise ValueError("invalid macro vintage/window")
        dates = [point.observation_date for point in self.observations]
        if (dates != sorted(set(dates)) or len(dates) > MAX_OBSERVATIONS
                or any(not self.observation_start <= point.observation_date <= self.observation_end
                       or not point.realtime_start <= self.vintage_date <= point.realtime_end
                       for point in self.observations)):
            raise ValueError("invalid macro observation provenance")
        present = [point for point in self.observations if point.value is not None]
        if self.observations and (not self.title or not self.units or not self.frequency
                or not self.seasonal_adjustment or self.frequency_short not in FRESHNESS_DAYS):
            raise ValueError("missing macro metadata")
        if present:
            stale = (self.vintage_date - present[-1].observation_date).days > FRESHNESS_DAYS[self.frequency_short]
            expected = DataQualityStatus.STALE if stale else DataQualityStatus.OK
            reason = "stale_observations" if stale else "eligible_complete_vintage"
            if self.quality_status is not expected or self.reason != reason:
                raise ValueError("macro freshness/status mismatch")
        elif (self.quality_status in {DataQualityStatus.OK, DataQualityStatus.STALE}
              or self.reason in {"eligible_complete_vintage", "stale_observations"}):
            raise ValueError("empty macro coverage is not usable")
        allowed = {
            "fred_not_configured": DataQualityStatus.UNAVAILABLE,
            "vendor_request_failed": DataQualityStatus.UNAVAILABLE,
            "invalid_vendor_response": DataQualityStatus.INVALID,
            "series_not_found": DataQualityStatus.NO_DATA,
            "empty_vintage_window": DataQualityStatus.COVERAGE_GAP,
            "only_missing_observations": DataQualityStatus.NO_DATA,
        }
        if self.reason in allowed and (self.quality_status is not allowed[self.reason] or present):
            raise ValueError("macro failure/status mismatch")
        if self.observations and self.reason not in {
                "eligible_complete_vintage", "stale_observations", "only_missing_observations"}:
            raise ValueError("failed macro response must not retain usable-looking rows")
        if self.reason == "only_missing_observations" and not self.observations:
            raise ValueError("missing-observation status requires actual missing rows")
        return self


def collect_fred_series(instrument: InstrumentContract, series_id: str, *,
                        analysis_as_of=None, lookback_days=DEFAULT_LOOKBACK_DAYS,
                        clock=lambda: datetime.now(UTC), request=None):
    """One explicit configured series, two timeout-bound requests, no fallback.

    Injected clock/request are test seams, not production provider configuration.
    No future as-of, data truncation, value inference or raw error retention.
    The existing request boundary buffers JSON before this parser's size check;
    this is not a streaming/network-memory or whole-acquisition deadline bound.
    The CLI and default web preparation flow remain unchanged.
    """
    instrument = InstrumentContract.model_validate(instrument.model_dump())
    if (type(series_id) is not str or re.fullmatch(r"[A-Z0-9_]{1,30}", series_id) is None
            or type(lookback_days) is not int or not 1 <= lookback_days <= 36525):
        raise ValueError("invalid macro collection request")
    started = clock()
    cutoff = started if analysis_as_of is None else analysis_as_of
    if (type(started) is not datetime or started.utcoffset() is None
            or type(cutoff) is not datetime or cutoff.utcoffset() is None or cutoff > started):
        raise ValueError("invalid macro collection clock")
    vintage = cutoff.astimezone(FRED_TZ).date() - timedelta(days=1)
    start = vintage - timedelta(days=lookback_days)
    base = {"instrument_id": instrument.instrument_id, "canonical_symbol": instrument.canonical_symbol,
        "asset_class": instrument.asset_class.value, "venue": instrument.venue,
        "quote_currency": instrument.quote_currency, "timezone": instrument.timezone,
        "series_id": series_id, "requested_at": started, "analysis_as_of": cutoff,
        "vintage_date": vintage, "vintage_available_at": vintage_available_at(vintage),
        "observation_start": start, "observation_end": vintage}

    def failed(status, reason):
        return MacroCollection(**base, retrieved_at=clock(), quality_status=status, reason=reason)

    fetch = _request if request is None else request
    realtime = {"realtime_start": vintage.isoformat(), "realtime_end": vintage.isoformat()}
    try:
        meta = fetch("series", {"series_id": series_id, **realtime})
    except FredNotConfiguredError:
        return failed(DataQualityStatus.UNAVAILABLE, "fred_not_configured")
    except Exception:
        return failed(DataQualityStatus.UNAVAILABLE, "vendor_request_failed")
    try:
        if (type(meta) is not dict or len(json.dumps(meta, allow_nan=False).encode()) > MAX_RESPONSE_BYTES
                or any(meta.get(key) != expected for key, expected in realtime.items())):
            raise ValueError()
        entries = meta["seriess"]
        if type(entries) is not list:
            raise ValueError()
        if not entries:
            return failed(DataQualityStatus.NO_DATA, "series_not_found")
        if len(entries) != 1 or entries[0]["id"] != series_id:
            raise ValueError()
        info = entries[0]
        if (any(info.get(key) != expected for key, expected in realtime.items())
                or any(type(info[key]) is not str or not info[key]
                       for key in ("title", "units", "frequency", "frequency_short", "seasonal_adjustment"))
                or info["frequency_short"] not in FRESHNESS_DAYS):
            raise ValueError()
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
        return failed(DataQualityStatus.INVALID, "invalid_vendor_response")
    try:
        raw = fetch("series/observations", {"series_id": series_id, **realtime,
            "observation_start": start.isoformat(), "observation_end": vintage.isoformat(),
            "sort_order": "asc", "units": "lin", "output_type": 1,
            "limit": MAX_OBSERVATIONS, "offset": 0})
    except FredNotConfiguredError:
        return failed(DataQualityStatus.UNAVAILABLE, "fred_not_configured")
    except Exception:
        return failed(DataQualityStatus.UNAVAILABLE, "vendor_request_failed")
    try:
        if (type(raw) is not dict or len(json.dumps(raw, allow_nan=False).encode()) > MAX_RESPONSE_BYTES
                or any(raw.get(key) != expected for key, expected in realtime.items())):
            raise ValueError()
        rows = raw["observations"]
        if (type(rows) is not list or type(raw["count"]) is not int or raw["count"] != len(rows)
                or len(rows) > MAX_OBSERVATIONS or type(raw["offset"]) is not int or raw["offset"] != 0
                or type(raw["limit"]) is not int or raw["limit"] != MAX_OBSERVATIONS
                or raw["units"] != "lin" or raw["sort_order"] != "asc"
                or type(raw["output_type"]) is not int or raw["output_type"] != 1
                or raw["observation_start"] != start.isoformat()
                or raw["observation_end"] != vintage.isoformat()):
            raise ValueError()
        points = []
        for row in rows:
            if any(type(row[key]) is not str or re.fullmatch(r"\d{4}-\d{2}-\d{2}", row[key]) is None
                   for key in ("date", "realtime_start", "realtime_end")):
                raise ValueError()
            value = row["value"]
            if type(value) is not str or not value.strip():
                raise ValueError()
            parsed = None if value == "." else float(value)
            if parsed is not None and not math.isfinite(parsed):
                raise ValueError()
            points.append(MacroObservation(observation_date=row["date"], value=parsed,
                realtime_start=row["realtime_start"], realtime_end=row["realtime_end"]))
        present = [point for point in points if point.value is not None]
        if not points:
            return failed(DataQualityStatus.COVERAGE_GAP, "empty_vintage_window")
        if not present:
            status, reason = DataQualityStatus.NO_DATA, "only_missing_observations"
        else:
            stale = (vintage - present[-1].observation_date).days > FRESHNESS_DAYS[info["frequency_short"]]
            status = DataQualityStatus.STALE if stale else DataQualityStatus.OK
            reason = "stale_observations" if stale else "eligible_complete_vintage"
        return MacroCollection(**base, retrieved_at=clock(), title=info["title"], units=info["units"],
            frequency=info["frequency"], frequency_short=info["frequency_short"],
            seasonal_adjustment=info["seasonal_adjustment"], observations=tuple(points),
            quality_status=status, reason=reason)
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
        return failed(DataQualityStatus.INVALID, "invalid_vendor_response")
