"""Read-only durable evidence aggregation; never permission to continue a run."""

import math
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from tradingagents.contracts import RunEventType
from tradingagents.contracts.runs import ResearchExecutionLimits
from tradingagents.platform.events import RunEventStore
from tradingagents.platform.persistence import PlatformRepository
from tradingagents.platform.persistence.models import RunEventRow

MAX_ACCOUNTING_EVENTS = 10_000
COUNTERS = ("started_model_calls", "model_calls", "calls_with_usage", "failed_calls",
            "input_tokens", "output_tokens", "total_tokens")


class AccountingEvidenceError(ValueError):
    """Fixed diagnostic without private event content or DB exception text."""


@dataclass(frozen=True, repr=False)
class AccountingEvidence:
    evidence_status: str
    high_water_sequence: int
    attempts: tuple[int, ...]
    started_calls: int | None = None
    completed_calls: int | None = None
    unreported_started_calls: int | None = None
    reported_input_tokens: int | None = None
    reported_output_tokens: int | None = None
    reported_total_tokens: int | None = None
    elapsed_lower_bound: float | None = None
    # No remaining allowance or consent can be derived from lower-bound time.
    exact_elapsed_known: bool = False


def _usage(payload, limits):
    if set(payload) != {"usage", "attempt", "elapsed_seconds", "execution_limits"}:
        raise ValueError()
    value = payload["usage"]
    if type(value) is not dict or set(value) != set(COUNTERS) | {
            "status", "model_call_scope", "provider_request_attempts", "cost", "cost_status"}:
        raise ValueError()
    if any(type(value[key]) is not int or not 0 <= value[key] <= 2**63 - 1 for key in COUNTERS):
        raise ValueError()
    recorded_limits = ResearchExecutionLimits.model_validate(payload["execution_limits"])
    elapsed = payload["elapsed_seconds"]
    if (recorded_limits != limits or type(elapsed) not in {int, float}
            or not math.isfinite(elapsed) or elapsed < 0
            or value["model_calls"] > value["started_model_calls"]
            or value["started_model_calls"] > limits.model_calls
            or value["failed_calls"] + value["calls_with_usage"] > value["model_calls"]
            or value["input_tokens"] + value["output_tokens"] != value["total_tokens"]
            or (value["calls_with_usage"] == 0 and value["total_tokens"] != 0)
            or value["model_call_scope"] != "logical_langchain_invocations"
            or value["provider_request_attempts"] is not None or value["cost"] is not None
            or value["cost_status"] != "not_reported_by_provider"):
        raise ValueError()
    reported = (value["model_calls"] > 0
                and value["started_model_calls"] == value["model_calls"] == value["calls_with_usage"])
    if value["status"] != ("reported" if reported else "incomplete"):
        raise ValueError()
    return value, elapsed


def load_accounting_evidence(*, session, owner_id, run_id):
    """Read a bounded owner-scoped prefix, preserving missing/legacy uncertainty.

    High-water identity must be rechecked by future consent/lease transactions;
    this snapshot is not publication authority or authenticated user input.
    No historical rows are rewritten, no inferred zero-cost or exact crash time.
    """
    try:
        run = PlatformRepository(session).get_run(run_id, owner_id)
        if run is None:
            raise ValueError()
        limits = run.execution_limits or ResearchExecutionLimits()
        high = session.scalar(select(func.coalesce(func.max(RunEventRow.sequence), 0)).where(
            RunEventRow.owner_id == owner_id, RunEventRow.run_id == run_id))
        if not 0 <= high <= MAX_ACCOUNTING_EVENTS:
            raise ValueError()
        store = RunEventStore(session)
        position, current_attempt = 0, 0
        latest, seen_attempts = {}, set()
        legacy = False
        while position < high:
            batch = store.list_after(owner_id, run_id, after_sequence=position, limit=min(500, high - position))
            if not batch:
                raise ValueError()
            for event in batch:
                if event.sequence != position + 1 or event.owner_id != owner_id or event.run_id != run_id:
                    raise ValueError()
                position = event.sequence
                if event.event_type not in {RunEventType.RESEARCH_EXECUTION_STARTED, RunEventType.MODEL_USAGE}:
                    continue
                attempt = event.payload.get("attempt")
                if type(attempt) is not int or not 1 <= attempt <= 1_000_000:
                    raise ValueError()
                if event.event_type is RunEventType.RESEARCH_EXECUTION_STARTED:
                    if attempt <= current_attempt:
                        raise ValueError()
                    current_attempt = attempt
                    seen_attempts.add(attempt)
                    continue
                if attempt != current_attempt:
                    raise ValueError()
                # Old events have no pre-admission/elapsed identity. Withhold
                # all totals rather than dropping that attempt from an aggregate.
                if "elapsed_seconds" not in event.payload or "execution_limits" not in event.payload:
                    legacy = True
                    continue
                value, elapsed = _usage(event.payload, limits)
                previous = latest.get(attempt)
                if previous and (elapsed < previous[1] or any(value[key] < previous[0][key] for key in COUNTERS)):
                    raise ValueError()
                if previous and value["calls_with_usage"] == previous[0]["calls_with_usage"] and any(
                        value[key] != previous[0][key] for key in ("input_tokens", "output_tokens", "total_tokens")):
                    raise ValueError()
                latest[attempt] = (value, elapsed)
        attempts = tuple(sorted(seen_attempts))
        if legacy or not attempts or set(latest) != seen_attempts:
            return AccountingEvidence("UNVERIFIED", high, attempts)
        totals = {key: sum(value[key] for value, _ in latest.values()) for key in COUNTERS}
        elapsed_total = sum(elapsed for _, elapsed in latest.values())
        if not math.isfinite(elapsed_total):
            raise ValueError()
        return AccountingEvidence("PASS", high, attempts, totals["started_model_calls"], totals["model_calls"],
            totals["started_model_calls"] - totals["calls_with_usage"], totals["input_tokens"],
            totals["output_tokens"], totals["total_tokens"], elapsed_total)
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError, SQLAlchemyError):
        raise AccountingEvidenceError("accounting evidence requires review") from None
