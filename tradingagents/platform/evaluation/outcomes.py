"""Compute outcomes from hash-verified snapshots and explicit session closes."""

import hashlib
import json
from datetime import UTC, datetime

from tradingagents.contracts import (
    DataQualityStatus,
    DecisionCandidate,
    NormalizedTimeSeries,
    PriceInterval,
    SnapshotManifest,
)

from .service import EvaluationObservation


def calendar_snapshot_outcome(*, decision, instrument, benchmark_instrument, asset,
                              benchmark, holding_sessions, evaluated_at):
    """Return an outcome plus exact calendar windows needed for persisted replay."""
    from .calendar import evaluation_session_window

    if instrument.instrument_id != decision.instrument_id or benchmark_instrument.instrument_id != benchmark[1].instrument_id:
        raise ValueError("evaluation calendar instrument identity mismatch")
    windows = tuple(evaluation_session_window(instrument=item, decision_at=decision.as_of,
        holding_sessions=holding_sessions, evaluated_at=evaluated_at)
        for item in (instrument, benchmark_instrument))
    if windows[0].session_closes != windows[1].session_closes:
        raise ValueError("asset and benchmark evaluation calendars do not align")
    observation = snapshot_outcome(decision=decision, asset=asset, benchmark=benchmark,
        session_closes=windows[0].session_closes, evaluated_at=evaluated_at)
    binding = {"outcome_hash": observation.outcome_hash,
               "calendar_hashes": [window.content_hash for window in windows]}
    digest = "sha256:" + hashlib.sha256(json.dumps(binding, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return observation.model_copy(update={"outcome_hash": digest}), windows


def snapshot_outcome(
    *, decision: DecisionCandidate,
    asset: tuple[SnapshotManifest, NormalizedTimeSeries],
    benchmark: tuple[SnapshotManifest, NormalizedTimeSeries],
    session_closes: tuple[datetime, ...],
    evaluated_at: datetime,
) -> EvaluationObservation:
    """Session closes include entry then each holding session; no padded bars.

    The caller supplies closes from the asset's exchange/24x7 calendar. Entry is
    strictly after the decision; every expected close must exist in both series.
    """
    if evaluated_at.tzinfo is None or evaluated_at.utcoffset() is None:
        raise ValueError("evaluation clock requires timezone")
    decision = DecisionCandidate.model_validate(decision.model_dump())
    asset, benchmark = tuple(
        (SnapshotManifest.model_validate(manifest.model_dump()),
         NormalizedTimeSeries.model_validate(series.model_dump()))
        for manifest, series in (asset, benchmark)
    )
    if len(session_closes) < 2 or any(time.tzinfo is None or time.utcoffset() is None for time in session_closes):
        raise ValueError("at least two timezone-aware session closes are required")
    if tuple(sorted(set(session_closes))) != session_closes:
        raise ValueError("session closes must be ordered and unique")
    if session_closes[0] <= decision.as_of or session_closes[-1] > evaluated_at:
        raise ValueError("outcome window must follow decision and precede evaluation")
    session_closes = tuple(close.astimezone(UTC) for close in session_closes)
    returns = []
    hashes = []
    for manifest, series in (asset, benchmark):
        payload = json.dumps(series.model_dump(mode="json"), allow_nan=False,
                             ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
        digest = "sha256:" + hashlib.sha256(payload).hexdigest()
        if digest != manifest.content_hash:
            raise ValueError("outcome snapshot content hash mismatch")
        if manifest.instrument_id != series.instrument_id or manifest.dataset != series.dataset:
            raise ValueError("outcome snapshot identity mismatch")
        if (manifest.as_of != series.as_of
                or manifest.source_start != series.bars[0].timestamp
                or manifest.source_end != series.bars[-1].timestamp
                or manifest.retrieved_at < series.bars[-1].timestamp):
            raise ValueError("outcome snapshot time mismatch")
        if manifest.quality_status is not DataQualityStatus.OK or manifest.as_of > evaluated_at or manifest.retrieved_at > evaluated_at:
            raise ValueError("outcome snapshot not available at evaluation time")
        if series.interval is not PriceInterval.ONE_DAY:
            raise ValueError("decision evaluation requires daily prices")
        bars = {bar.timestamp: bar for bar in series.bars}
        if any(close not in bars for close in session_closes):
            raise ValueError("incomplete expected session coverage")
        first, last = bars[session_closes[0]], bars[session_closes[-1]]
        start = first.adjusted_close if first.adjusted_close is not None else first.close
        end = last.adjusted_close if last.adjusted_close is not None else last.close
        returns.append(end / start - 1)
        hashes.append(manifest.content_hash)
    if asset[1].instrument_id != decision.instrument_id or asset[1].instrument_id == benchmark[1].instrument_id:
        raise ValueError("asset and benchmark identities must be distinct and match decision")
    if asset[1].quote_currency != benchmark[1].quote_currency or asset[1].price_basis != benchmark[1].price_basis:
        raise ValueError("asset and benchmark price bases/currencies must match")
    binding = {"hashes": hashes, "sessions": [close.isoformat() for close in session_closes],
               "decision_id": str(decision.decision_id)}
    return EvaluationObservation(
        decision_id=decision.decision_id, evaluated_at=session_closes[-1],
        holding_period_days=len(session_closes) - 1,
        raw_return=returns[0], benchmark_return=returns[1],
        outcome_snapshot_ids=(asset[0].snapshot_id, benchmark[0].snapshot_id),
        outcome_hash="sha256:" + hashlib.sha256(json.dumps(binding, sort_keys=True).encode()).hexdigest(),
    )
