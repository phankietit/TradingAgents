"""Read-only original-allowance arithmetic, never owner consent or admission."""

from dataclasses import dataclass

from .accounting import AccountingEvidence, load_accounting_evidence


@dataclass(frozen=True, repr=False)
class RemainingAllowanceObservation:
    accounting: AccountingEvidence
    assessment_status: str
    reason: str
    remaining_wall_seconds: float | None = None
    remaining_model_calls: int | None = None


def load_remaining_allowance(*, session, owner_id, run_id):
    """Derive arithmetic from authoritative original limits and durable events.

    No supplied cap, duration, fingerprint or consent is accepted. Logical
    starts, including unreported/failed reservations, consume the original cap.
    PASS means bounded arithmetic only: a transaction, trusted checkpoint and
    explicit consent remain mandatory before any separately governed execution.
    """
    evidence = load_accounting_evidence(session=session, owner_id=owner_id, run_id=run_id)
    if evidence.evidence_status != "PASS":
        return RemainingAllowanceObservation(evidence, "UNVERIFIED", "accounting_unavailable")
    calls = max(0, evidence.original_model_calls - evidence.started_calls)
    seconds = (None if evidence.elapsed_upper_bound is None
               else max(0.0, evidence.original_wall_seconds - evidence.elapsed_upper_bound))
    if calls == 0 or evidence.elapsed_lower_bound >= evidence.original_wall_seconds:
        return RemainingAllowanceObservation(evidence, "BLOCKED", "original_allowance_exhausted", seconds, calls)
    if seconds is None:
        return RemainingAllowanceObservation(evidence, "UNVERIFIED", "elapsed_upper_bound_unavailable", None, calls)
    return RemainingAllowanceObservation(evidence, "PASS", "bounded_arithmetic_only", seconds, calls)
