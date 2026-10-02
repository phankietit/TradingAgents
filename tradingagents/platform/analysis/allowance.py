"""Read-only original-allowance arithmetic, never owner consent or admission."""

from dataclasses import dataclass
from time import monotonic

from tradingagents.contracts.runs import ResearchExecutionLimits

from .accounting import AccountingEvidence, AccountingEvidenceError, load_accounting_evidence
from .observer import ResearchBudgetExceeded, ResearchObserver


@dataclass(frozen=True, repr=False)
class RemainingAllowanceObservation:
    accounting: AccountingEvidence
    assessment_status: str
    reason: str
    remaining_wall_seconds: float | None = None
    remaining_model_calls: int | None = None


@dataclass(frozen=True, repr=False)
class _RetainedObserverBinding:
    """Local construction identity, not a consent token or DB writer fence."""

    observer: ResearchObserver
    accounting: AccountingEvidence
    started: float
    clock: object
    check_cancelled: object
    emit: object
    save_stage: object


def validate_retained_observer(*, observer, run):
    """Require the original debit and an unused attempt before restore/spawn.

    Only the builder installs this private binding after a full DB recheck.
    This catches accidental fresh/reset/substituted observers at the trusted
    parent boundary. It neither authenticates callers nor fences later DB
    writes, and must not be exposed as permission to continue paid research.
    """
    try:
        if type(observer) is not ResearchObserver:
            raise ValueError()
        with observer.lock:
            binding = getattr(observer, "_retained_binding", None)
            if type(binding) is not _RetainedObserverBinding or binding.observer is not observer:
                raise ValueError()
            evidence = binding.accounting
            limits = run.execution_limits or ResearchExecutionLimits()
            if (type(evidence) is not AccountingEvidence or evidence.evidence_status != "PASS"
                    or evidence.owner_id != run.owner_id or evidence.run_id != run.run_id
                    or evidence.config_hash != run.config_hash
                    or evidence.original_wall_seconds != limits.wall_seconds
                    or evidence.original_model_calls != limits.model_calls
                    or type(observer.max_seconds) is not int or type(observer.max_calls) is not int
                    or observer.max_seconds != evidence.original_wall_seconds
                    or observer.max_calls != evidence.original_model_calls
                    or type(observer._retained_elapsed_seconds) is not type(evidence.elapsed_upper_bound)
                    or type(observer._retained_started_calls) is not int
                    or observer._retained_elapsed_seconds != evidence.elapsed_upper_bound
                    or observer._retained_started_calls != evidence.started_calls
                    or type(observer.started) is not type(binding.started)
                    or observer.started != binding.started or observer.clock is not binding.clock
                    or observer.check_cancelled is not binding.check_cancelled
                    or observer.emit is not binding.emit or observer.save_stage is not binding.save_stage
                    or observer.started_calls != 0 or any(observer.usage.values())
                    or observer.active or observer.completed or observer.seen_model_runs
                    or observer._execution_stopped):
                raise ValueError()
    except (ValueError, TypeError, AttributeError):
        raise AccountingEvidenceError("retained observer requires review") from None


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


def build_retained_observer(*, session, owner_id, run_id, expected_accounting, check_cancelled,
                            emit, clock=monotonic, save_stage=None):
    """Internal budget enforcement, NOT consent/checkpoint/dispatch authority.

    Reload original evidence and refuse stale observation before construction.
    Caller must separately authenticate, lock consent/execution and restore a
    trusted checkpoint. This is not wired to any default worker or API route.
    """
    if (type(expected_accounting) is not AccountingEvidence
            or expected_accounting.owner_id != owner_id or expected_accounting.run_id != run_id):
        raise AccountingEvidenceError("accounting evidence requires review") from None
    observation = load_remaining_allowance(session=session, owner_id=owner_id, run_id=run_id)
    if observation.accounting != expected_accounting:
        raise AccountingEvidenceError("accounting evidence requires review") from None
    if observation.assessment_status == "BLOCKED":
        raise ResearchBudgetExceeded("original research allowance exhausted")
    if observation.assessment_status != "PASS":
        raise AccountingEvidenceError("accounting evidence requires review") from None
    evidence = observation.accounting
    observer = ResearchObserver(check_cancelled=check_cancelled, emit=emit, clock=clock,
        max_seconds=evidence.original_wall_seconds, max_calls=evidence.original_model_calls, save_stage=save_stage)
    observer._retained_elapsed_seconds = evidence.elapsed_upper_bound
    observer._retained_started_calls = evidence.started_calls
    observer._retained_binding = _RetainedObserverBinding(observer, evidence, observer.started,
        observer.clock, observer.check_cancelled, observer.emit, observer.save_stage)
    observer.remaining_seconds()
    return observer
