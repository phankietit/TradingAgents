"""Authenticated allocation and separate lease fence, NOT model admission.

No default queue/worker consumes this table. It does not start accounting,
publish checkpoints/results, deserialize original context or invoke a model.
Those integrations must preserve the original thread and retained allowance.
"""

import hashlib
import math
import re
import secrets
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError

from tradingagents._compat import UTC
from tradingagents.platform.auth import OwnerAuth
from tradingagents.platform.jobs import DurableJobQueue
from tradingagents.platform.persistence import PlatformRepository
from tradingagents.platform.persistence.models import (
    JobRow,
    OwnerRow,
    ResearchContinuationRow,
    ResearchExecutionCompletionRow,
    ResearchExecutionRow,
    RunRow,
)

from .continuation import (
    ContinuationConsentStore,
    _canonical,
    _check_lock_timeout,
    _db_utc,
    _digest,
    _payload,
)


class LinkedExecutionError(ValueError):
    """Fixed diagnostic, no private identities or database exception text."""


def _reject():
    raise LinkedExecutionError("linked execution requires review") from None


def _token_hash(value):
    if type(value) is not UUID:
        _reject()
    return hashlib.sha256(str(value).encode()).hexdigest()


@dataclass(frozen=True, repr=False)
class ExecutionReservation:
    execution_id: UUID
    owner_id: UUID
    source_run_id: UUID
    source_job_id: UUID
    observation_hash: str
    attempt: int
    status: str


@dataclass(frozen=True, repr=False)
class LinkedExecutionLease:
    reservation: ExecutionReservation
    worker_id: str
    token: UUID
    started_at: datetime
    deadline_at: datetime
    expires_at: datetime


def _reservation(row):
    return ExecutionReservation(row.execution_id, row.owner_id, row.source_run_id,
        row.source_job_id, row.observation_hash, row.attempt, row.status)


class LinkedExecutionStore:
    """Consume a consent identity into one separately fenced internal allocation.

    A lease is not a paid grant or publication context. Default worker/API and
    terminal-context guards stay unchanged. Expiration never auto-requeues;
    unknown termination goes to review, not a fabricated stop/refund.
    """

    def __init__(self, consents):
        if type(consents) is not ContinuationConsentStore:
            _reject()
        self.consents, self.database = consents, consents.database

    def _now(self):
        now = self.consents.clock()
        if type(now) is not datetime or now.tzinfo is None or now.utcoffset() is None:
            _reject()
        return now.astimezone(UTC)

    @contextmanager
    def _transaction(self, *, lock_timeout_seconds=None):
        try:
            _check_lock_timeout(self.consents.lock_timeout_seconds)
            timeout = self.consents.lock_timeout_seconds
            if lock_timeout_seconds is not None:
                _check_lock_timeout(lock_timeout_seconds)
                timeout = min(timeout, lock_timeout_seconds)
            with self.database.session(lock_timeout_seconds=timeout) as session:
                if session.bind.dialect.name == "sqlite":
                    session.execute(text("BEGIN IMMEDIATE"))
                elif session.bind.dialect.name != "postgresql":
                    _reject()
                yield session, self._now()
        except (ValueError, TypeError, AttributeError, KeyError, OverflowError, SQLAlchemyError):
            _reject()

    def _source(self, session, execution_id, now, *, owner_id=None, recheck=False, active=True):
        if type(execution_id) is not UUID:
            _reject()
        row = session.get(ResearchContinuationRow, execution_id)
        if row is None or (owner_id is not None and row.owner_id != owner_id):
            _reject()
        # Global order: owner (then request session), original job/run, execution.
        # Original job is locked, not restarted or assigned a new lease.
        owner = session.scalar(select(OwnerRow).where(OwnerRow.owner_id == row.owner_id)
            .with_for_update().execution_options(populate_existing=True))
        if owner is None or (active and owner.status != "active"):
            _reject()
        session.scalar(select(JobRow).where(JobRow.job_id == row.source_job_id)
            .with_for_update().execution_options(populate_existing=True))
        session.scalar(select(RunRow).where(RunRow.run_id == row.source_run_id)
            .with_for_update().execution_options(populate_existing=True))
        payload = row.payload
        observation = payload["observation"]
        run = PlatformRepository(session).get_run(row.source_run_id, row.owner_id)
        job = DurableJobQueue(session).get(row.source_job_id, row.owner_id)
        if (payload["format"] != "research-continuation-consent-v1" or payload["dispatch_enabled"] is not False
                or _digest(payload) != row.observation_hash or _db_utc(row.created_at) > now
                or observation["owner_id"] != str(row.owner_id) or observation["run_id"] != str(row.source_run_id)
                or observation["source_job_id"] != str(row.source_job_id)
                or observation["checkpoint_record_id"] != str(row.checkpoint_record_id)
                or observation["accounting"]["high_water_sequence"] != row.source_event_sequence
                or type(observation["source_attempt"]) is not int or not 1 <= observation["source_attempt"] < 1_000_000
                or run is None or job is None or job.run_id != run.run_id
                or _digest(run.model_dump(mode="json")) != observation["source_run_hash"]
                or _digest(job.model_dump(mode="json")) != observation["source_job_hash"]):
            _reject()
        current = None
        if recheck:
            current = self.consents.observe(session=session, owner_id=row.owner_id, run_id=row.source_run_id)
            if _canonical(payload) != _canonical(_payload(current)):
                _reject()
        return row, observation, current

    def _execution(self, session, consent, observation, now):
        row = session.scalar(select(ResearchExecutionRow).where(
            ResearchExecutionRow.execution_id == consent.execution_id).with_for_update()
            .execution_options(populate_existing=True))
        if row is None:
            return None
        if (row.owner_id != consent.owner_id or row.source_run_id != consent.source_run_id
                or row.source_job_id != consent.source_job_id or row.observation_hash != consent.observation_hash
                or type(row.attempt) is not int or row.attempt != observation["source_attempt"] + 1
                or _db_utc(row.created_at) > _db_utc(row.updated_at) or _db_utc(row.updated_at) > now):
            _reject()
        if row.status in {"reserved", "cancelled"}:
            if any(getattr(row, key) is not None for key in (
                    "worker_id", "lease_token_hash", "started_at", "deadline_at", "lease_expires_at")):
                _reject()
        elif row.status in {"leased", "cancel_requested", "review_required"}:
            accounting = observation["accounting"]
            elapsed = accounting["elapsed_upper_bound"]
            cap = accounting["original_wall_seconds"]
            if (type(cap) is not int or type(elapsed) not in (int, float)
                    or not math.isfinite(elapsed) or not 0 <= elapsed < cap):
                _reject()
            if (type(row.worker_id) is not str or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", row.worker_id) is None
                    or type(row.lease_token_hash) is not str or re.fullmatch(r"[0-9a-f]{64}", row.lease_token_hash) is None
                    or any(getattr(row, key) is None for key in ("started_at", "deadline_at", "lease_expires_at"))
                    or not _db_utc(row.created_at) <= _db_utc(row.started_at) <= _db_utc(row.updated_at)
                    or not _db_utc(row.started_at) < _db_utc(row.lease_expires_at) <= _db_utc(row.deadline_at)
                    or _db_utc(row.deadline_at) != _db_utc(row.started_at) + timedelta(seconds=cap - elapsed)):
                _reject()
        else:
            _reject()
        return row

    def allocate(self, *, execution_id, session_token, csrf_token):
        with self._transaction() as (session, now):
            principal = OwnerAuth(session).lock_authenticated_consent(session_token, csrf_token, now=now)
            consent, observation, _ = self._source(session, execution_id, now, owner_id=principal.owner_id, recheck=True)
            row = self._execution(session, consent, observation, now)
            if row is None:
                row = ResearchExecutionRow(execution_id=execution_id, owner_id=consent.owner_id,
                    source_run_id=consent.source_run_id, source_job_id=consent.source_job_id,
                    observation_hash=consent.observation_hash, attempt=observation["source_attempt"] + 1,
                    status="reserved", created_at=now, updated_at=now)
                session.add(row)
                session.flush()
            result = _reservation(row)
        return result

    def claim(self, *, execution_id, worker_id, lease_seconds=300):
        if (type(worker_id) is not str or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", worker_id) is None
                or type(lease_seconds) is not int or not 1 <= lease_seconds <= 300):
            _reject()
        with self._transaction() as (session, now):
            consent, observation, current = self._source(session, execution_id, now, recheck=True)
            row = self._execution(session, consent, observation, now)
            if row is None or row.status != "reserved":
                _reject()
            accounting = current.accounting
            remaining = accounting.original_wall_seconds - accounting.elapsed_upper_bound
            row.status, row.worker_id, row.started_at = "leased", worker_id, now
            row.deadline_at = now + timedelta(seconds=remaining)
            if row.deadline_at <= now:
                _reject()
            row.lease_expires_at = min(now + timedelta(seconds=lease_seconds), row.deadline_at)
            row.updated_at = now
            token = uuid4()
            row.lease_token_hash = _token_hash(token)
            session.flush()
            result = LinkedExecutionLease(_reservation(row), worker_id, token,
                now, row.deadline_at, row.lease_expires_at)
        return result  # Lost ACK cannot re-claim or reset this attempt.

    def _fence(self, session, lease, now, *, recheck=False):
        """Validate the private lease inside the caller's publication transaction."""
        if type(lease) is not LinkedExecutionLease or type(lease.reservation) is not ExecutionReservation:
            _reject()
        if (any(type(getattr(lease.reservation, field)) is not UUID for field in (
                    "execution_id", "owner_id", "source_run_id", "source_job_id"))
                or type(lease.reservation.attempt) is not int
                or type(lease.worker_id) is not str
                or any(type(getattr(lease, field)) is not datetime or getattr(lease, field).utcoffset() is None
                       for field in ("started_at", "deadline_at", "expires_at"))):
            _reject()
        consent, observation, current = self._source(session, lease.reservation.execution_id, now, recheck=recheck)
        row = self._execution(session, consent, observation, now)
        fresh = self._now()  # Acquiring owner/job/run locks can consume the lease.
        if (row is None or row.status != "leased"
                or _canonical(asdict(_reservation(row))) != _canonical(asdict(lease.reservation))
                or row.worker_id != lease.worker_id or not secrets.compare_digest(row.lease_token_hash, _token_hash(lease.token))
                or _db_utc(row.started_at) != lease.started_at or _db_utc(row.deadline_at) != lease.deadline_at
                or fresh < now or fresh >= _db_utc(row.lease_expires_at)):
            _reject()
        return row, current

    def heartbeat(self, lease, *, lease_seconds=300):
        if type(lease_seconds) is not int or not 1 <= lease_seconds <= 300:
            _reject()
        with self._transaction() as (session, now):
            row, _ = self._fence(session, lease, now)
            if session.get(ResearchExecutionCompletionRow, row.execution_id) is not None:
                _reject()
            now = self._now()
            if now >= _db_utc(row.lease_expires_at):
                _reject()
            row.lease_expires_at = min(now + timedelta(seconds=lease_seconds), _db_utc(row.deadline_at))
            row.updated_at = now
            result = LinkedExecutionLease(_reservation(row), row.worker_id, lease.token,
                _db_utc(row.started_at), _db_utc(row.deadline_at), row.lease_expires_at)
        return result

    def request_cancel(self, *, execution_id, session_token, csrf_token):
        with self._transaction() as (session, now):
            principal = OwnerAuth(session).lock_authenticated_consent(session_token, csrf_token, now=now)
            consent, observation, _ = self._source(session, execution_id, now, owner_id=principal.owner_id)
            row = self._execution(session, consent, observation, now)
            if row is None or session.get(ResearchExecutionCompletionRow, execution_id) is not None:
                _reject()
            if row.status == "reserved":
                row.status = "cancelled"
            elif row.status == "leased":
                row.status = "cancel_requested"
            row.updated_at = now
            result = _reservation(row)
        return result

    def mark_expired_for_review(self, *, execution_id):
        with self._transaction() as (session, now):
            consent, observation, _ = self._source(session, execution_id, now, active=False)
            row = self._execution(session, consent, observation, now)
            if row is not None and session.get(ResearchExecutionCompletionRow, execution_id) is not None:
                # Do not automatically relabel a committed output marker.
                # The separate owner reader must still verify all its evidence.
                result = _reservation(row)
            else:
                if (row is None or row.status not in {"leased", "cancel_requested", "review_required"}
                        or now < _db_utc(row.lease_expires_at)):
                    _reject()
                row.status, row.updated_at = "review_required", now
                result = _reservation(row)
        return result
