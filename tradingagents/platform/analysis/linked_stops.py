"""Actual parent local-stop reconciliation, not accounting/refund/model authority.

Normal cancelled/expired publication fences remain untouched. This separate
append-only fact records a reaped local child and closed reader/pipes. It never
claims remote provider termination, known billing or permission to continue.
"""

import json
import math
import os
import secrets
from dataclasses import asdict, dataclass
from datetime import datetime
from multiprocessing.process import BaseProcess
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError

from tradingagents.platform.persistence.models import (
    ResearchExecutionDispatchRow,
    ResearchExecutionEntryRow,
    ResearchExecutionStopRow,
    RunEventRow,
)

from .accounting import load_accounting_evidence
from .continuation import _canonical, _db_utc, _digest
from .linked_execution import LinkedExecutionStore, _token_hash
from .linked_publication import LinkedPublicationContext, validate_entry


class LinkedStopError(ValueError):
    """Fixed diagnostic; never an SDK, database, credential or private payload."""


def _reject():
    raise LinkedStopError("linked local stop requires review") from None


@dataclass(frozen=True, repr=False)
class LinkedLocalStop:
    execution_id: UUID
    owner_id: UUID
    source_run_id: UUID
    attempt: int
    stopped_at: datetime
    local_elapsed_seconds: float
    child_exitcode: int
    accounting_high_water_sequence: int
    continuation_authorized: bool = False
    provider_cost_known: bool = False


class LinkedStopStore:
    def __init__(self, executions):
        if type(executions) is not LinkedExecutionStore:
            _reject()
        self.executions = executions

    @staticmethod
    def _source(session, execution_id, now, *, owner_id, through_sequence=None):
        consent, observation = LinkedExecutionStore._control_source(session, execution_id, now,
            owner_id=owner_id, active=False)
        execution = LinkedExecutionStore._execution(session, consent, observation, now)
        if execution is None or execution.status not in {"leased", "cancel_requested", "review_required"}:
            _reject()
        validate_entry(session, execution)
        entry = session.get(ResearchExecutionEntryRow, execution_id)
        event = session.get(RunEventRow, entry.event_id)
        dispatch = session.get(ResearchExecutionDispatchRow, execution_id)
        if (dispatch is None or dispatch.checkpoint_record_id != consent.checkpoint_record_id
                or dispatch.checkpoint_hash != observation["checkpoint_content_hash"]
                or not _db_utc(execution.started_at) <= _db_utc(event.occurred_at)
                    <= _db_utc(dispatch.created_at) <= now):
            _reject()
        evidence = load_accounting_evidence(session=session, owner_id=owner_id,
            run_id=execution.source_run_id, through_sequence=through_sequence)
        if evidence.evidence_status != "PASS" or evidence.attempts[-1] != execution.attempt:
            _reject()
        return execution, entry, dispatch, evidence

    @staticmethod
    def _read(session, row, source, now):
        execution, entry, dispatch, evidence = source
        value = row.payload
        elapsed = value.get("local_elapsed_seconds") if type(value) is dict else None
        exitcode = value.get("child_exitcode") if type(value) is dict else None
        if (type(elapsed) not in (float, int) or not math.isfinite(elapsed) or elapsed < 0
                or type(exitcode) is not int or not -(2**31) <= exitcode < 2**31
                or row.execution_id != execution.execution_id or row.owner_id != execution.owner_id
                or row.source_run_id != execution.source_run_id
                or not _db_utc(dispatch.created_at) <= _db_utc(row.stopped_at) <= now
                or elapsed < (_db_utc(row.stopped_at) - _db_utc(execution.started_at)).total_seconds()):
            _reject()
        expected = {"format": "linked-local-stop-v1", "execution_id": str(execution.execution_id),
            "owner_id": str(execution.owner_id), "source_run_id": str(execution.source_run_id),
            "source_job_id": str(execution.source_job_id), "attempt": execution.attempt,
            "observation_hash": execution.observation_hash, "entry_event_id": str(entry.event_id),
            "checkpoint_record_id": str(dispatch.checkpoint_record_id), "checkpoint_hash": dispatch.checkpoint_hash,
            "accounting": asdict(evidence), "stopped_at": _db_utc(row.stopped_at).isoformat(),
            "local_elapsed_seconds": elapsed, "child_exitcode": exitcode,
            "child_reaped": True, "reader_closed": True,
            "continuation_authorized": False, "provider_cost_known": False}
        if _canonical(value) != _canonical(expected) or row.payload_hash != _digest(expected):
            _reject()
        return LinkedLocalStop(execution.execution_id, execution.owner_id, execution.source_run_id,
            execution.attempt, _db_utc(row.stopped_at), float(elapsed), exitcode, evidence.high_water_sequence)

    def read(self, *, owner_id, execution_id):
        """Internal owner-scoped verified read; not a bearer/admission grant.

        Caller authentication belongs to the future API, not this internal UUID.
        Lost committed ACK can be resolved without a child, nonce or model call.
        """
        try:
            if type(owner_id) is not UUID or type(execution_id) is not UUID:
                _reject()
            with self.executions._transaction() as (session, now):
                row = session.get(ResearchExecutionStopRow, execution_id)
                through_sequence = None
                if row is not None:
                    if row.owner_id != owner_id:
                        _reject()
                    through_sequence = row.payload["accounting"]["high_water_sequence"]
                    if type(through_sequence) is not int or through_sequence < 1:
                        _reject()
                source = self._source(session, execution_id, now, owner_id=owner_id,
                    through_sequence=through_sequence)
                if row is None:
                    return None
                return self._read(session, row, source, self.executions._now())
        except (ValueError, TypeError, AttributeError, KeyError, IndexError, SQLAlchemyError):
            _reject()
    def record_supervised(self, engine):
        """Trusted supervisor only, before closing its joined Process handle.

        Check the real parent-owned process/reader/pipe objects from this exact
        dispatch. No browser JSON, booleans or caller elapsed/counters accepted.
        Expiry/cancel permits only this separate stop fact, not normal writes.
        """
        from .engine import AnalysisEngine
        from .supervision import SupervisedAnalysisEngine

        try:
            if type(engine) is not SupervisedAnalysisEngine:
                _reject()
            context = engine.linked_context
            if (type(context) is not LinkedPublicationContext or context._store is not self.executions
                    or engine.engine_factory is not AnalysisEngine
                    or type(engine._linked_native_scope) is not tuple or len(engine._linked_native_scope) != 5):
                _reject()
            process, reader, parent, child, stopped = engine._linked_native_scope
            observer = context._observer()
            binding = engine._linked_native_binding
            if (type(binding) is not tuple or len(binding) != 3
                    or binding[0] is not context or binding[1] is not observer
                    or binding[2].execution_observer is not observer
                    or _digest(binding[2].model_dump(mode="json")) != context._linked_source_binding.request_hash):
                _reject()
            if (not isinstance(process, BaseProcess) or process._parent_pid != os.getpid()
                    or process.pid is None or process.is_alive() or process.exitcode is None
                    or reader.is_alive() or not stopped.is_set() or not parent.closed or not child.closed
                    or observer._execution_stopped is not True):
                _reject()
            captured_elapsed = observer._usage_payload()["elapsed_seconds"]
            if type(captured_elapsed) not in (float, int) or not math.isfinite(captured_elapsed) or captured_elapsed < 0:
                _reject()
            with self.executions._transaction() as (session, now):
                source = self._source(session, context.execution_id, now, owner_id=context.owner_id)
                execution, entry, dispatch, evidence = source
                lease = context._lease
                if (type(lease.reservation.attempt) is not int
                        or execution.execution_id != lease.reservation.execution_id
                        or execution.owner_id != lease.reservation.owner_id
                        or execution.source_run_id != lease.reservation.source_run_id
                        or execution.source_job_id != lease.reservation.source_job_id
                        or execution.attempt != lease.reservation.attempt
                        or execution.observation_hash != lease.reservation.observation_hash
                        or execution.worker_id != lease.worker_id
                        or not secrets.compare_digest(execution.lease_token_hash, _token_hash(lease.token))
                        or _db_utc(execution.started_at) != lease.started_at
                        or _db_utc(execution.deadline_at) != lease.deadline_at):
                    _reject()  # Status may change; private dispatch identity may not.
                row = session.get(ResearchExecutionStopRow, context.execution_id)
                if row is not None:
                    return self._read(session, row, source, self.executions._now())
                elapsed = max(float(captured_elapsed), (now - lease.started_at).total_seconds())
                payload = {"format": "linked-local-stop-v1", "execution_id": str(execution.execution_id),
                    "owner_id": str(execution.owner_id), "source_run_id": str(execution.source_run_id),
                    "source_job_id": str(execution.source_job_id), "attempt": execution.attempt,
                    "observation_hash": execution.observation_hash, "entry_event_id": str(entry.event_id),
                    "checkpoint_record_id": str(dispatch.checkpoint_record_id), "checkpoint_hash": dispatch.checkpoint_hash,
                    "accounting": asdict(evidence), "stopped_at": now.isoformat(),
                    "local_elapsed_seconds": elapsed, "child_exitcode": process.exitcode,
                    "child_reaped": True, "reader_closed": True,
                    "continuation_authorized": False, "provider_cost_known": False}
                row = ResearchExecutionStopRow(execution_id=execution.execution_id, owner_id=execution.owner_id,
                    source_run_id=execution.source_run_id, payload_hash=_digest(payload),
                    payload=json.loads(_canonical(payload)), stopped_at=now)
                session.add(row)
                session.flush()
                result = self._read(session, row, source, self.executions._now())
            return result  # Never acknowledge before commit; no old row/event rewrite.
        except (ValueError, TypeError, AttributeError, KeyError, IndexError, SQLAlchemyError):
            _reject()


def read_linked_local_stop(*, session, owner_id, execution_id, clock):
    """Read-only receipt validation; caller must authenticate the owner first.

    Reuse the complete internal source/entry/dispatch/accounting/hash validation.
    An absent receipt grants nothing. No codec, SDK, lease nonce or writer needed.
    """
    try:
        if type(owner_id) is not UUID or type(execution_id) is not UUID:
            _reject()
        row = session.get(ResearchExecutionStopRow, execution_id)
        if row is None:
            return None
        if row.owner_id != owner_id:
            _reject()
        through_sequence = row.payload["accounting"]["high_water_sequence"]
        if type(through_sequence) is not int or through_sequence < 1:
            _reject()
        source = LinkedStopStore._source(session, execution_id, clock(), owner_id=owner_id,
            through_sequence=through_sequence)
        return LinkedStopStore._read(session, row, source, clock())
    except (ValueError, TypeError, AttributeError, KeyError, IndexError, OverflowError, SQLAlchemyError):
        _reject()
