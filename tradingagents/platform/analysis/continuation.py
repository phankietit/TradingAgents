"""Transactional owner consent/link recording; NOT enabled paid dispatch.

No queue, observer, model, result, historical lifecycle or checkpoint is
modified. Future dispatch must consume/recheck this identity under its own
lease fence, reload original sources/clients and retain original accounting.
"""

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from math import isfinite
from uuid import UUID, uuid4

from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError

from tradingagents._compat import UTC
from tradingagents.contracts import JobKind, JobStatus, RunStatus
from tradingagents.platform.auth import OwnerAuth
from tradingagents.platform.jobs.queue import DurableJobQueue
from tradingagents.platform.persistence import PlatformRepository
from tradingagents.platform.persistence.models import (
    ArtifactRow,
    DecisionRow,
    JobRow,
    ResearchCheckpointRow,
    ResearchContinuationRow,
    RunRow,
)

from .accounting import AccountingEvidence
from .allowance import load_remaining_allowance
from .checkpoint_codec import SnapshotCheckpointCodec
from .checkpoint_store import PrivateCheckpointStore


class ContinuationConsentError(ValueError):
    """Fixed review diagnostic, never raw data, credentials or database errors."""


def _reject():
    raise ContinuationConsentError("continuation consent requires review") from None


def _uuid_json(value):
    if type(value) is UUID:
        return str(value)
    raise ValueError()


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False, default=_uuid_json).encode()


def _digest(value):
    return hashlib.sha256(_canonical(value)).hexdigest()


def _db_utc(value):
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _check_lock_timeout(value):
    if type(value) not in (int, float) or not isfinite(value) or not 0 < value <= 60:
        _reject()


@dataclass(frozen=True, repr=False)
class ContinuationObservation:
    owner_id: UUID
    run_id: UUID
    source_job_id: UUID
    source_attempt: int
    source_run_hash: str
    source_job_hash: str
    checkpoint_record_id: UUID
    checkpoint_sequence: int
    checkpoint_id: UUID
    checkpoint_fingerprint: str
    checkpoint_content_hash: str
    accounting: AccountingEvidence


@dataclass(frozen=True, repr=False)
class ContinuationConsent:
    execution_id: UUID
    observation: ContinuationObservation
    idempotency_key: UUID
    consented_at: datetime


def _payload(observation):
    return json.loads(_canonical({"format": "research-continuation-consent-v1",
        "observation": asdict(observation),
        "acknowledged_disclosures": ["original_allowance_retained", "provider_cost_unknown",
                                     "prior_research_unvalidated"],
        "dispatch_enabled": False}))


class ContinuationConsentStore:
    """Trusted internal loader and authenticated atomic consent reservation.

    No browser endpoint/default worker calls this store. The reviewed codec
    is supplied by trusted setup, not a caller-controlled hash. Consent/link
    recording is not final original-context/client attestation or model entry.
    An execution ID alone is never a bearer authorization token.
    """

    def __init__(self, database, *, codec, clock=lambda: datetime.now(UTC), lock_timeout_seconds=5.0):
        if type(codec) is not SnapshotCheckpointCodec:
            _reject()
        _check_lock_timeout(lock_timeout_seconds)
        self.database, self.codec = database, codec
        self.clock, self.lock_timeout_seconds = clock, lock_timeout_seconds

    def observe(self, *, session, owner_id, run_id):
        """Bound latest original checkpoint and complete accounting; no grant.

        Caller authorization is separate for this internal read. Record below
        derives owner from a locked authenticated session and reloads here.
        """
        try:
            if type(owner_id) is not UUID or type(run_id) is not UUID:
                _reject()
            now = self.clock()
            if type(now) is not datetime or now.tzinfo is None or now.utcoffset() is None:
                _reject()
            # Job-then-run lock order matches publication. SQLite record()
            # starts BEGIN IMMEDIATE before all reads; observe alone is NOT
            # a SQLite writer fence or a check-then-dispatch permission.
            job_row = session.scalar(select(JobRow).where(JobRow.run_id == run_id, JobRow.owner_id == owner_id)
                .with_for_update().execution_options(populate_existing=True))
            run_row = session.scalar(select(RunRow).where(RunRow.run_id == run_id, RunRow.owner_id == owner_id)
                .with_for_update().execution_options(populate_existing=True))
            if job_row is None or run_row is None:
                _reject()
            repository = PlatformRepository(session)
            run = repository.get_run(run_id, owner_id)
            job = DurableJobQueue(session).get(job_row.job_id, owner_id)
            expected_status = {JobStatus.FAILED: RunStatus.FAILED, JobStatus.CANCELLED: RunStatus.CANCELLED}
            if (run is None or job is None or job.kind is not JobKind.ANALYSIS_RUN
                    or job.status not in expected_status or run.status is not expected_status[job.status]
                    or run.decision_inputs is None or run.owner_id != owner_id or run.run_id != run_id
                    or run_row.status != run.status.value or run_row.instrument_id != run.instrument_id
                    or _db_utc(run_row.analysis_as_of) != run.analysis_as_of
                    or job.lease_owner is not None or job.lease_expires_at is not None
                    or job.completed_at != run.completed_at or run.completed_at > now
                    or job.attempt < 1):
                _reject()
            expected_payload = {"instrument_id": str(run.instrument_id),
                "analysis_as_of": run.analysis_as_of.astimezone(UTC).isoformat(),
                "selected_analysts": list(run.selected_analysts), "config_hash": run.config_hash,
                "decision_inputs": run.decision_inputs.model_dump(mode="json")}
            if run.report_language is not None:
                expected_payload["report_language"] = run.report_language
            if run.execution_limits is not None:
                expected_payload["execution_limits"] = run.execution_limits.model_dump(mode="json")
            if (_canonical(job.payload) != _canonical(expected_payload) or job.output_artifact_ids
                    or session.scalar(select(DecisionRow.decision_id).where(DecisionRow.run_id == run_id).limit(1)) is not None
                    or session.scalar(select(ArtifactRow.artifact_id).where(ArtifactRow.run_id == run_id,
                        ArtifactRow.kind == "analysis_report").limit(1)) is not None):
                _reject()
            allowance = load_remaining_allowance(session=session, owner_id=owner_id, run_id=run_id)
            evidence = allowance.accounting
            if (allowance.assessment_status != "PASS" or not evidence.attempts
                    or evidence.attempts[-1] != job.attempt):
                _reject()
            row = session.scalar(select(ResearchCheckpointRow).where(ResearchCheckpointRow.run_id == run_id)
                .order_by(ResearchCheckpointRow.sequence.desc()).limit(1))
            if (row is None or row.owner_id != owner_id or row.job_id != job.job_id
                    or row.attempt != job.attempt or row.sequence < 1
                    or _db_utc(row.created_at) > run.completed_at):
                _reject()
            value = PrivateCheckpointStore(codec=self.codec).load_latest(session=session, owner_id=owner_id, run_id=run_id)
            if value is None:
                _reject()
            return ContinuationObservation(owner_id, run_id, job.job_id, job.attempt,
                _digest(run.model_dump(mode="json")), _digest(job.model_dump(mode="json")),
                row.record_id, row.sequence, row.checkpoint_id, row.fingerprint, row.content_hash, evidence)
        except (ValueError, TypeError, AttributeError, KeyError, SQLAlchemyError):
            _reject()

    def record(self, *, session_token, csrf_token, expected_observation, idempotency_key, confirm_continue):
        """Append one consent identity and return only after durable commit.

        Explicit literal confirmation must follow UI disclosure in a future
        reviewed API. This internal service is not that browser/UX evidence.
        It creates no new job/run, modifies no old research rows and spends no
        allowance. Future dispatch MUST recheck/consume the link transactionally.
        """
        if (type(expected_observation) is not ContinuationObservation or type(idempotency_key) is not UUID
                or confirm_continue is not True):
            _reject()
        try:
            _check_lock_timeout(self.lock_timeout_seconds)
            timestamp = self.clock()
            if type(timestamp) is not datetime or timestamp.tzinfo is None or timestamp.utcoffset() is None:
                _reject()
            with self.database.session(lock_timeout_seconds=self.lock_timeout_seconds) as session:
                if session.bind.dialect.name == "sqlite":
                    session.execute(text("BEGIN IMMEDIATE"))
                elif session.bind.dialect.name != "postgresql":
                    _reject()
                principal = OwnerAuth(session).lock_authenticated_consent(session_token, csrf_token, now=timestamp)
                if principal.owner_id != expected_observation.owner_id:
                    _reject()
                current = self.observe(session=session, owner_id=principal.owner_id, run_id=expected_observation.run_id)
                if (type(expected_observation.accounting) is not AccountingEvidence
                        or _canonical(_payload(current)) != _canonical(_payload(expected_observation))):
                    _reject()
                payload = _payload(current)
                digest = _digest(payload)
                row = session.scalar(select(ResearchContinuationRow).where(
                    ResearchContinuationRow.owner_id == principal.owner_id,
                    ResearchContinuationRow.idempotency_key == str(idempotency_key)))
                if row is not None:
                    if (row.source_run_id != current.run_id or row.source_job_id != current.source_job_id
                            or row.checkpoint_record_id != current.checkpoint_record_id
                            or row.source_event_sequence != current.accounting.high_water_sequence
                            or row.observation_hash != digest or _digest(row.payload) != row.observation_hash
                            or row.payload != payload or _db_utc(row.created_at) > timestamp):
                        _reject()
                    result = ContinuationConsent(row.execution_id, current, idempotency_key, _db_utc(row.created_at))
                else:
                    execution_id = uuid4()
                    session.add(ResearchContinuationRow(execution_id=execution_id, owner_id=principal.owner_id,
                        source_run_id=current.run_id, source_job_id=current.source_job_id,
                        checkpoint_record_id=current.checkpoint_record_id,
                        source_event_sequence=current.accounting.high_water_sequence,
                        idempotency_key=str(idempotency_key), observation_hash=digest,
                        payload=payload, created_at=timestamp))
                    session.flush()
                    result = ContinuationConsent(execution_id, current, idempotency_key, timestamp)
            return result  # Never acknowledge an uncommitted reservation.
        except (ValueError, TypeError, AttributeError, KeyError, SQLAlchemyError):
            _reject()
