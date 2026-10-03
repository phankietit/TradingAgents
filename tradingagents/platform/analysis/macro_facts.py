"""Read-only FRED fact replay; observation labels are not publication times.

Native metadata is quoted source data, never authority to change instructions.
No live fetch, inferred missing observations or invented inflation/growth rates.
"""

import hashlib
import json
import math
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from uuid import UUID

from tradingagents.contracts import DataQualityStatus, InstrumentContract, SnapshotManifest
from tradingagents.dataflows.platform_fred import MacroCollection

FREQUENCIES = {"D": ("daily", "hằng ngày"), "W": ("weekly", "hằng tuần"),
    "BW": ("biweekly", "hai tuần"), "M": ("monthly", "hằng tháng"),
    "Q": ("quarterly", "hằng quý"), "SA": ("semiannual", "nửa năm"), "A": ("annual", "hằng năm")}
FACT = re.compile(r"fred\.([A-Z0-9_]{1,30})\.(value|difference|pct_change)\."
    r"(\d{4}-\d{2}-\d{2})(?:\.(\d{4}-\d{2}-\d{2}))?\.native\."
    r"([0-9a-f]{16})\.vintage\.(\d{4}-\d{2}-\d{2})")


class SnapshotMacroFacts:
    def __init__(self, source: dict):
        from tradingagents.platform.market_data.macro import _manifest

        self.collection = MacroCollection.model_validate(source["data"])
        manifest = SnapshotManifest.model_validate(source["provenance"])
        if (source["snapshot_id"] != str(manifest.snapshot_id)
                or manifest != _manifest(self.collection, manifest.snapshot_id)
                or self.collection.quality_status is not DataQualityStatus.OK):
            raise ValueError("macro fact payload differs from eligible snapshot provenance")
        self.snapshot_id = str(UUID(source["snapshot_id"]))
        self.provenance = manifest.model_dump(mode="json")
        self._points = {point.observation_date.isoformat(): point for point in self.collection.observations}
        self._unit = hashlib.sha256(json.dumps({"units": self.collection.units,
            "frequency_short": self.collection.frequency_short,
            "seasonal_adjustment": self.collection.seasonal_adjustment}, sort_keys=True).encode()).hexdigest()[:16]

    def require_instrument(self, instrument):
        instrument = InstrumentContract.model_validate(instrument.model_dump())
        if any(getattr(self.collection, key) != value for key, value in {
                "instrument_id": instrument.instrument_id, "canonical_symbol": instrument.canonical_symbol,
                "asset_class": instrument.asset_class.value, "venue": instrument.venue,
                "quote_currency": instrument.quote_currency, "timezone": instrument.timezone}.items()):
            raise ValueError("macro fact instrument identity mismatch")

    def fact_id(self, operation, left, right=None):
        periods = left if right is None else left + "." + right
        return f"fred.{self.collection.series_id}.{operation}.{periods}.native.{self._unit}.vintage.{self.collection.vintage_date}"

    def resolve_fact(self, fact_id):
        if type(fact_id) is not str or len(fact_id) > 200:
            return None
        match = FACT.fullmatch(fact_id)
        if not match:
            return None
        series, operation, left, right, unit, vintage = match.groups()
        if (series != self.collection.series_id or unit != self._unit
                or vintage != self.collection.vintage_date.isoformat()
                or (operation == "value") != (right is None)):
            return None
        a, b = self._points.get(left), self._points.get(right)
        if a is None or a.value is None:
            return None
        if operation == "value":
            return a.value
        if b is None or b.value is None or (operation == "pct_change" and b.value <= 0):
            return None
        value = a.value - b.value if operation == "difference" else (a.value / b.value - 1) * 100
        return value if math.isfinite(value) else None

    def fact_catalog(self):
        latest = next(point for point in reversed(self.collection.observations) if point.value is not None)
        return {self.fact_id("value", latest.observation_date.isoformat()): latest.value}

    def _view(self, point):
        return {"observation_label": point.observation_date.isoformat(), "value": point.value,
            "fact_id": self.fact_id("value", point.observation_date.isoformat()),
            "status": "missing" if point.value is None else "available",
            "realtime_start": point.realtime_start.isoformat(), "realtime_end": point.realtime_end.isoformat()}

    def page(self, *, offset=0, limit=100):
        if (type(offset) is not int or type(limit) is not int
                or not 0 <= offset < len(self.collection.observations) or not 1 <= limit <= 250):
            raise ValueError("invalid macro page")
        end = min(offset + limit, len(self.collection.observations))
        return {"snapshot_id": self.snapshot_id, "series_id": self.collection.series_id,
            "units": self.collection.units, "frequency": self.collection.frequency,
            "frequency_short": self.collection.frequency_short,
            "vintage_date": self.collection.vintage_date.isoformat(),
            "vintage_available_at": self.collection.vintage_available_at.isoformat(),
            "availability": "complete_chicago_vintage_day_not_exact_release_time",
            "offset": offset, "total_observations": len(self.collection.observations),
            "next_offset": end if end < len(self.collection.observations) else None,
            "observations": [self._view(point) for point in self.collection.observations[offset:end]]}

    def calculation(self, *, operation, left_period, right_period):
        if type(operation) is not str or operation not in {"difference", "pct_change"}:
            raise ValueError("invalid macro operation")
        for period in (left_period, right_period):
            if (type(period) is not str or re.fullmatch(r"\d{4}-\d{2}-\d{2}", period) is None
                    or not self.collection.observation_start <= date.fromisoformat(period) <= self.collection.observation_end):
                raise ValueError("invalid macro period")
        fact_id = self.fact_id(operation, left_period, right_period)
        value = self.resolve_fact(fact_id)
        return {"snapshot_id": self.snapshot_id, "fact_id": fact_id, "value": value,
            "status": "available" if value is not None else "unavailable",
            "operation": operation, "left_period": left_period, "reference_period": right_period,
            "native_input_unit": self.collection.units,
            "output_unit": ("percent" if operation == "pct_change" else
                "percentage points" if self.collection.units == "Percent" else self.collection.units),
            "meaning": "arithmetic comparison of supplied observations, not an inferred economic statistic or asset return"}

    def summary(self):
        latest = next(point for point in reversed(self.collection.observations) if point.value is not None)
        return {"snapshot_id": self.snapshot_id, "provenance": self.provenance,
            "series_id": self.collection.series_id, "title": self.collection.title,
            "units": self.collection.units, "frequency": self.collection.frequency,
            "seasonal_adjustment": self.collection.seasonal_adjustment,
            "coverage": self.collection.coverage, "total_observations": len(self.collection.observations),
            "missing_observations": sum(point.value is None for point in self.collection.observations),
            "latest_present": self._view(latest), "last_observation": self._view(self.collection.observations[-1]),
            "full_history_tool": "get_snapshot_macro",
            "limitations": "Observation labels are not release times; native levels are not automatically inflation/growth rates; this series is not headline or exhaustive macro coverage."}

    def statement(self, fact_id, number, *, vi=False):
        value = self.resolve_fact(fact_id)
        if value is None or type(number) is not str or re.fullmatch(r"-?\d+(?:\.\d+)?", number) is None:
            raise ValueError("unsupported macro statement")
        places = len(number.split(".")[1]) if "." in number else 0
        try:
            if not 0 <= places <= 8 or Decimal(number) != Decimal(str(value)).quantize(Decimal(1).scaleb(-places)):
                raise ValueError("unsupported macro statement value")
        except InvalidOperation:
            raise ValueError("unsupported macro statement value") from None
        _, operation, left, right, _, vintage = FACT.fullmatch(fact_id).groups()
        unit = json.dumps(self.collection.units, ensure_ascii=False)
        frequency = FREQUENCIES[self.collection.frequency_short][int(vi)]
        series = self.collection.series_id
        if operation == "value":
            return (f"Chuỗi FRED {series}, nhãn kỳ quan sát {left} ({frequency}; vintage {vintage}): {number} (đơn vị gốc {unit})." if vi
                else f"FRED series {series}, observation label {left} ({frequency}; vintage {vintage}): {number} (native unit {unit}).")
        if operation == "difference":
            output_unit = ("điểm phần trăm" if vi else "percentage points") if self.collection.units == "Percent" else unit
            return (f"Chênh lệch số học của chuỗi FRED {series} tại nhãn {left} trừ nhãn {right} ({frequency}; vintage {vintage}): {number} {output_unit}." if vi
                else f"Arithmetic difference of FRED series {series} at label {left} minus label {right} ({frequency}; vintage {vintage}): {number} {output_unit}.")
        return (f"Thay đổi phần trăm số học của chuỗi FRED {series} tại nhãn {left} so với nhãn {right}, lấy giá trị tại {right} làm mẫu số ({frequency}; đơn vị đầu vào {unit}; vintage {vintage}): {number}%." if vi
            else f"Arithmetic percentage change of FRED series {series} at label {left} relative to label {right}, using the value at {right} as denominator ({frequency}; input unit {unit}; vintage {vintage}): {number}%.")
