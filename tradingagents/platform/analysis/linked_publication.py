"""Trusted parent-only linked publication, not an enabled worker/API route.

No model or child is started here. The retained observer and every durable
write are fenced separately; a private lease is not a report/decision grant.
"""

import math
from contextlib import contextmanager
from time import monotonic

from tradingagents.contracts import RunEventType
from tradingagents.platform.events import RunEventStore
from tradingagents.platform.persistence import PlatformRepository
from tradingagents.platform.persistence.models import (
    ResearchExecutionCompletionRow,
    ResearchExecutionEntryRow,
    ResearchExecutionEventRow,
    RunEventRow,
)

from .accounting import load_accounting_evidence
from .allowance import build_retained_observer, validate_retained_observer
from .continuation import _canonical
from .linked_execution import LinkedExecutionLease, LinkedExecutionStore, _reject
from .observer import STAGES, ResearchObserver


def validate_entry(session, execution):
    """Validate actual marker and its actor link, not just the FK's existence."""
    entry = session.get(ResearchExecutionEntryRow, execution.execution_id)
    event = session.get(RunEventRow, entry.event_id) if entry else None
    actor = session.get(ResearchExecutionEventRow, entry.event_id) if entry else None
    if (event is None or actor is None or actor.execution_id != execution.execution_id
            or event.owner_id != execution.owner_id or event.run_id != execution.source_run_id
            or event.event_type != RunEventType.RESEARCH_EXECUTION_STARTED.value
            or _canonical(event.payload) != _canonical({"attempt": execution.attempt})):
        _reject()


class LinkedPublicationContext:
    """Internal exact retained observer + same-transaction publication fence.

    prepare builds an unused observer, then rechecks all consent high-water
    evidence under the lease locks before the one-time actual parent entry.
    Failed/lost entry ACK never permits another entry. Default routes stay off.
    """

    def __init__(self, store, lease):
        if type(store) is not LinkedExecutionStore or type(lease) is not LinkedExecutionLease:
            _reject()
        self._store, self._lease = store, lease
        self.database = store.database
        self.job_id = lease.reservation.source_job_id
        self.owner_id = lease.reservation.owner_id
        self.run_id = lease.reservation.source_run_id
        self.execution_id = lease.reservation.execution_id
        self._check_callback = self.raise_if_cancelled
        self._emit_callback = self._emit
        self.observer = None
        self._binding = None
        self._renewal_failed = False

    def __repr__(self):
        return object.__repr__(self)

    def clock(self):
        return self._store._now()

    @classmethod
    def prepare(cls, store, lease, *, observer_clock=monotonic, save_stage=None):
        context = cls(store, lease)
        # Read-only construction is outside writer locks: the builder checks
        # this context's lease on its own connection. The entry transaction
        # below reloads the exact full observation; no check-then-write grant.
        with store.database.session() as session:
            prior = load_accounting_evidence(session=session, owner_id=context.owner_id, run_id=context.run_id)
            context.observer = build_retained_observer(session=session,
                owner_id=context.owner_id, run_id=context.run_id, expected_accounting=prior,
                check_cancelled=context._check_callback, emit=context._emit_callback,
                clock=observer_clock, save_stage=save_stage)
        context._binding = context.observer._retained_binding
        context._begin()
        return context

    def _observer(self):
        # Exact binding identity is also needed for control-plane stop proof.
        # Renewal uncertainty blocks normal callbacks/publication separately;
        # it must not erase observed reaping or grant remote-stop/cost authority.
        observer, binding = self.observer, self._binding
        if (type(self._renewal_failed) is not bool
                or type(self._store) is not LinkedExecutionStore or type(self._lease) is not LinkedExecutionLease
                or self.database is not self._store.database
                or (self.job_id, self.owner_id, self.run_id, self.execution_id) != (
                    self._lease.reservation.source_job_id, self._lease.reservation.owner_id,
                    self._lease.reservation.source_run_id, self._lease.reservation.execution_id)
                or type(observer) is not ResearchObserver or binding is None
                or observer._retained_binding is not binding or binding.observer is not observer
                or observer.check_cancelled is not self._check_callback
                or observer.emit is not self._emit_callback
                or observer.clock is not binding.clock or observer.started != binding.started
                or type(observer.started) is not type(binding.started)
                or observer.save_stage is not binding.save_stage
                or type(observer.max_calls) is not int or type(observer.max_seconds) is not int
                or observer.max_calls != binding.accounting.original_model_calls
                or observer.max_seconds != binding.accounting.original_wall_seconds
                or type(observer._retained_started_calls) is not int
                or observer._retained_started_calls != binding.accounting.started_calls
                or type(observer._retained_elapsed_seconds) is not type(binding.accounting.elapsed_upper_bound)
                or observer._retained_elapsed_seconds != binding.accounting.elapsed_upper_bound):
            _reject()
        return observer

    def _check_renewal(self):
        if self._renewal_failed is not False:
            _reject()

    def _append(self, session, event_type, payload, now):
        event = RunEventStore(session).append(owner_id=self.owner_id, run_id=self.run_id,
            event_type=event_type, payload={**payload, "attempt": self._lease.reservation.attempt}, occurred_at=now)
        session.add(ResearchExecutionEventRow(event_id=event.event_id, execution_id=self.execution_id))
        session.flush()
        return event

    def _usage(self, payload, now):
        # Parent claim/prepare/cleanup time also consumes the original wall
        # allowance. Never undercount it by using a later observer start alone.
        return {**payload, "elapsed_seconds": max(payload["elapsed_seconds"],
            (now - self._lease.started_at).total_seconds())}

    def _check_accounting(self, session):
        evidence = load_accounting_evidence(session=session, owner_id=self.owner_id, run_id=self.run_id)
        if (evidence.evidence_status != "PASS" or evidence.attempts[-1] != self._lease.reservation.attempt
                or evidence.started_calls > evidence.original_model_calls):
            _reject()

    def _begin(self):
        self._check_renewal()
        observer = self._observer()
        with self._store._transaction() as (session, now):
            execution, current = self._store._fence(session, self._lease, now, recheck=True)
            run = PlatformRepository(session).get_run(self.run_id, self.owner_id)
            validate_retained_observer(observer=observer, run=run)
            if (current.accounting != self._binding.accounting
                    or session.get(ResearchExecutionEntryRow, self.execution_id) is not None):
                _reject()
            event = self._append(session, RunEventType.RESEARCH_EXECUTION_STARTED, {}, now)
            session.add(ResearchExecutionEntryRow(execution_id=self.execution_id, event_id=event.event_id))
            self._append(session, RunEventType.MODEL_USAGE, self._usage(observer._usage_payload(), now), now)
            self._check_accounting(session)
            final_now = self.clock()
            self._store._fence(session, self._lease, final_now)
            execution.updated_at = final_now
        # Return only after commit. Missing ACK is not permission to re-enter.

    def raise_if_cancelled(self):
        self._check_renewal()
        if self.observer is not None:
            self._observer()
        with self._store._transaction() as (session, now):
            self._store._fence(session, self._lease, now)
            if session.get(ResearchExecutionCompletionRow, self.execution_id) is not None:
                _reject()

    def heartbeat(self, *, lease_seconds=300):
        self._check_renewal()
        self._observer()
        self._lease = self._store.heartbeat(self._lease, lease_seconds=lease_seconds)

    def commit_checkpoint(self, raw):
        from .checkpoint_store import PrivateCheckpointStore

        return PrivateCheckpointStore(codec=self._store.consents.codec).commit(
            context=self, owner_id=self.owner_id, run_id=self.run_id, raw=raw)

    @contextmanager
    def publication_session(self, *, lock_timeout_seconds=5.0):
        self._check_renewal()
        self._observer()
        with self._store._transaction(lock_timeout_seconds=lock_timeout_seconds) as (session, now):
            execution, _ = self._store._fence(session, self._lease, now)
            if session.get(ResearchExecutionCompletionRow, self.execution_id) is not None:
                _reject()
            validate_entry(session, execution)
            yield session
            self._check_renewal()
            # Lock acquisition / serialization / flush may consume the lease.
            # A pre-write check alone must not ACK a late publication.
            final_now = self.clock()
            self._store._fence(session, self._lease, final_now)
            execution.updated_at = final_now

    def _emit(self, event_type, payload):
        observer = self._observer()
        if type(payload) is not dict:
            _reject()
        kind = RunEventType(event_type)
        if kind is RunEventType.MODEL_USAGE:
            expected = observer._usage_payload()
            if observer._execution_stopped:
                expected = {**expected, "execution_stopped": True}
            elapsed = payload.get("elapsed_seconds")
            # A captured monotonic receipt necessarily precedes this second
            # clock read. Counters/flags must match exactly; elapsed must be a
            # finite already-observed duration, never a future/reset clock.
            if (type(elapsed) not in (int, float) or not math.isfinite(elapsed)
                    or not 0 <= elapsed <= expected["elapsed_seconds"]
                    or _canonical({key: value for key, value in payload.items() if key != "elapsed_seconds"})
                        != _canonical({key: value for key, value in expected.items() if key != "elapsed_seconds"})):
                _reject()
        elif kind in {RunEventType.STAGE_STARTED, RunEventType.STAGE_COMPLETED}:
            allowed = {"stage"} if kind is RunEventType.STAGE_STARTED else {"stage", "research_artifact_id"}
            if (observer._execution_stopped or type(payload) is not dict
                    or set(payload) - allowed or payload.get("stage") not in STAGES):
                _reject()
        else:
            _reject()  # No arbitrary errors, report, decision, approval or stop flag.
        with self.publication_session() as session:
            now = self.clock()
            self._append(session, kind, self._usage(payload, now) if kind is RunEventType.MODEL_USAGE else payload, now)
            self._check_accounting(session)
