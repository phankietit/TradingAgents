"""Current-vintage, filed-date-aware SEC facts for the approved AAPL web path.

The platform observes EDGAR at retrieval time. Filing dates describe the
underlying facts; they never make today's companyfacts response historical.
No vendor fallback or company-accounting inference is performed here.
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime, time
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, FiniteFloat, model_validator

from tradingagents._compat import UTC
from tradingagents.contracts import AssetClass, DataQualityStatus, InstrumentContract
from tradingagents.dataflows import sec_edgar


class SecPreparationError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class SecFact(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    metric: str = Field(min_length=1, max_length=80)
    tag: str = Field(min_length=1, max_length=120)
    frequency: Literal["annual", "quarterly"]
    period_start: date | None
    period_end: date
    filed_at: date
    form: str = Field(pattern=r"^10-[KQ](?:/A)?$")
    accession: str = Field(pattern=r"^\d{10}-\d{2}-\d{6}$")
    unit: Literal["USD", "USD/shares"]
    value: FiniteFloat

    @model_validator(mode="after")
    def valid_period(self):
        if self.period_end > self.filed_at or (self.period_start and self.period_start >= self.period_end):
            raise ValueError("SEC fact period is not eligible")
        return self


class SecCollection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    dataset: Literal["fundamentals"] = "fundamentals"
    vendor: Literal["sec_edgar"] = "sec_edgar"
    retrieval_path: Literal["companyfacts/us-gaap"] = "companyfacts/us-gaap"
    instrument_id: UUID
    canonical_symbol: Literal["AAPL"]
    asset_class: Literal["equity"] = "equity"
    venue: str
    quote_currency: Literal["USD"] = "USD"
    timezone: str
    cik: str = Field(pattern=r"^\d{10}$")
    requested_at: AwareDatetime
    retrieved_at: AwareDatetime
    quality_status: DataQualityStatus
    reason: str = Field(min_length=1, max_length=100)
    facts: tuple[SecFact, ...] = ()
    invalid_records: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def valid_collection(self):
        if self.requested_at > self.retrieved_at:
            raise ValueError("SEC retrieval precedes request")
        if any(datetime.combine(fact.filed_at, time.min, tzinfo=UTC) > self.requested_at
               for fact in self.facts):
            raise ValueError("SEC fact filed after request")
        if (self.quality_status is DataQualityStatus.OK) != bool(self.facts):
            raise ValueError("only nonempty SEC collections may be OK")
        if self.invalid_records and self.quality_status is DataQualityStatus.OK:
            raise ValueError("malformed SEC facts cannot be marked OK")
        keys = [(fact.metric, fact.frequency, fact.period_end) for fact in self.facts]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate SEC metric-period")
        return self


def _approved(instrument: InstrumentContract) -> None:
    if (instrument.asset_class is not AssetClass.EQUITY
            or instrument.canonical_symbol != "AAPL"
            or instrument.quote_currency != "USD"):
        raise SecPreparationError("unsupported")


def _contact_configured() -> bool:
    value = os.getenv("SEC_EDGAR_USER_AGENT", "").strip()
    return (bool(re.search(r"\S+@\S+\.\S+", value))
            and "contact@example.com" not in value
            and "\r" not in value and "\n" not in value)


def collect_sec_facts(instrument: InstrumentContract, *, clock=lambda: datetime.now(UTC),
                      fetch_cik=None, fetch_facts=None) -> SecCollection:
    """Read existing SEC adapter once and select the latest filed vintage per period.

    Test injection does not change production vendor routing. No time-based
    truncation: every eligible annual/quarterly period in companyfacts survives.
    """
    _approved(instrument)
    if not _contact_configured() and fetch_cik is None:
        raise SecPreparationError("unavailable")
    requested = clock()
    if requested.tzinfo is None or requested.utcoffset() is None:
        raise ValueError("SEC clock must be timezone aware")
    try:
        cik = (fetch_cik or sec_edgar.cik_for)(instrument.canonical_symbol)
        if cik is None:
            raise SecPreparationError("no_data")
        document = (fetch_facts or (lambda value: sec_edgar._cached_json(
            sec_edgar._FACTS_URL.format(cik=value), f"CIK{value}.json")))(cik)
    except SecPreparationError:
        raise
    except Exception as error:
        raise SecPreparationError("unavailable") from error
    retrieved = clock()
    if not isinstance(document, dict) or str(document.get("cik", "")).zfill(10) != cik:
        raise SecPreparationError("invalid")
    gaap = (document.get("facts") or {}).get("us-gaap")
    if not isinstance(gaap, dict):
        raise SecPreparationError("invalid")
    cutoff = requested.date()
    selected: dict[tuple[str, str, date], SecFact] = {}
    invalid = 0
    for statement in sec_edgar._STATEMENTS.values():
        for metric, tags in statement:
            for tag in tags:
                tagged = gaap.get(tag) or {}
                if not isinstance(tagged, dict):
                    invalid += 1
                    continue
                units = tagged.get("units", {})
                if not isinstance(units, dict):
                    invalid += 1
                    continue
                for unit, rows in units.items():
                    if unit not in {"USD", "USD/shares"}:
                        continue
                    if not isinstance(rows, list):
                        invalid += 1
                        continue
                    for row in rows:
                        try:
                            if row["filed"] > cutoff.isoformat():
                                continue
                            period_end = date.fromisoformat(row["end"])
                            start = date.fromisoformat(row["start"]) if "start" in row else None
                            if start is None:
                                frequency = "annual" if row["form"].startswith("10-K") else "quarterly"
                            else:
                                days = (period_end - start).days
                                frequency = next((name for name, (low, high) in sec_edgar._SPANS.items()
                                                  if low <= days <= high), None)
                            if frequency is None or not row["form"].startswith(("10-K", "10-Q")):
                                continue
                            fact = SecFact(metric=metric, tag=tag, frequency=frequency,
                                period_start=start, period_end=period_end,
                                filed_at=date.fromisoformat(row["filed"]), form=row["form"],
                                accession=row["accn"], unit=unit, value=row["val"])
                        except (AttributeError, KeyError, TypeError, ValueError, OverflowError):
                            invalid += 1
                            continue
                        key = (metric, frequency, period_end)
                        old = selected.get(key)
                        # Tags are ordered by preference as in the CLI; within
                        # that tag, the latest eligible amendment wins.
                        if old is None or (old.tag == tag and fact.filed_at >= old.filed_at):
                            selected[key] = fact
    facts = tuple(sorted(selected.values(), key=lambda fact: (
        fact.metric, fact.frequency, fact.period_end))) if not invalid else ()
    status = (DataQualityStatus.INVALID if invalid else DataQualityStatus.OK if facts
              else DataQualityStatus.NO_DATA)
    reason = ("malformed_companyfacts" if invalid else "eligible_filed_facts"
              if facts else "no_eligible_filed_facts")
    return SecCollection(instrument_id=instrument.instrument_id,
        canonical_symbol="AAPL", venue=instrument.venue, timezone=instrument.timezone,
        cik=cik, requested_at=requested, retrieved_at=retrieved,
        quality_status=status, reason=reason, facts=facts, invalid_records=invalid)


def fetch_current_sec_facts(instrument: InstrumentContract) -> SecCollection:
    _approved(instrument)
    if not _contact_configured():
        raise SecPreparationError("unavailable")
    try:
        result = subprocess.run([sys.executable, "-m", __name__],
            input=instrument.model_dump_json(), text=True, capture_output=True,
            timeout=75, check=False)
        if result.returncode or len(result.stdout) > 2_000_000:
            raise SecPreparationError("unavailable")
        value = json.loads(result.stdout)
        if "error" in value:
            raise SecPreparationError(value["error"] if value["error"] in
                {"no_data", "invalid", "unsupported"} else "unavailable")
        collection = SecCollection.model_validate(value)
        if collection.instrument_id != instrument.instrument_id:
            raise SecPreparationError("invalid")
        return collection
    except SecPreparationError:
        raise
    except (subprocess.TimeoutExpired, OSError, ValueError) as error:
        raise SecPreparationError("unavailable") from error


def main():
    try:
        instrument = InstrumentContract.model_validate_json(sys.stdin.read(16_384))
        with contextlib.redirect_stdout(sys.stderr):
            collection = collect_sec_facts(instrument)
        output = collection.model_dump(mode="json")
    except SecPreparationError as error:
        output = {"error": error.code}
    except Exception:
        output = {"error": "unavailable"}
    print(json.dumps(output, allow_nan=False))


if __name__ == "__main__":
    main()
