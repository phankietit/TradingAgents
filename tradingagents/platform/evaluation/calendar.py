"""Versioned exchange-session windows; never infer missing sessions from prices."""

import hashlib
import json
from datetime import timedelta
from importlib.metadata import version

import exchange_calendars
from pydantic import AwareDatetime, BaseModel, ConfigDict

from tradingagents._compat import UTC
from tradingagents.contracts import AssetClass, InstrumentContract


class EvaluationSessionWindow(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    calendar_name: str
    engine_version: str
    session_closes: tuple[AwareDatetime, ...]

    @property
    def content_hash(self):
        payload = json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":")).encode()
        return "sha256:" + hashlib.sha256(payload).hexdigest()


def evaluation_session_window(*, instrument, decision_at, holding_sessions, evaluated_at):
    instrument = InstrumentContract.model_validate(instrument.model_dump())
    if any(t.tzinfo is None or t.utcoffset() is None for t in (decision_at, evaluated_at)):
        raise ValueError("evaluation calendar requires aware timestamps")
    if isinstance(holding_sessions, bool) or not isinstance(holding_sessions, int) or not 1 <= holding_sessions <= 2520:
        raise ValueError("holding_sessions must be an integer between 1 and 2520")
    decision_at, evaluated_at = decision_at.astimezone(UTC), evaluated_at.astimezone(UTC)
    if not timedelta(0) < evaluated_at - decision_at <= timedelta(days=366 * 11):
        raise ValueError("evaluation calendar window must be positive and bounded")
    if instrument.asset_class in {AssetClass.EQUITY, AssetClass.ETF, AssetClass.CASH_INDEX}:
        if instrument.session_calendar not in {"XNYS", "XNAS"} or instrument.timezone != "America/New_York":
            raise ValueError("unsupported US market calendar identity")
        calendar_name = instrument.session_calendar
    elif instrument.asset_class is AssetClass.CRYPTO:
        if instrument.session_calendar != "24/7" or instrument.timezone != "UTC":
            raise ValueError("crypto evaluation requires UTC 24/7 sessions")
        calendar_name = "24/7"
    else:
        if instrument.session_calendar != "CME_Equity" or instrument.timezone != "America/Chicago":
            raise ValueError("unsupported reference future calendar identity")
        calendar_name = "CMES"
    calendar = exchange_calendars.get_calendar(calendar_name,
        start=(decision_at - timedelta(days=2)).date().isoformat(),
        end=(evaluated_at + timedelta(days=2)).date().isoformat())
    closes = tuple(t.to_pydatetime().astimezone(UTC) for t in calendar.closes
                   if decision_at < t <= evaluated_at)
    if len(closes) < holding_sessions + 1:
        raise ValueError("requested holding window has not settled")
    return EvaluationSessionWindow(calendar_name=calendar_name,
        engine_version="exchange-calendars:" + version("exchange-calendars"),
        session_closes=closes[:holding_sessions + 1])
