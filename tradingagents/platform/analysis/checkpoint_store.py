"""Parent-owned private checkpoint commits, not an enabled recovery route.

Only restricted JSON bytes are stored. No artifact reader, raw messages,
automatic replay, model invocation or continuation authority is introduced.
"""

import hashlib
from contextlib import contextmanager
from dataclasses import dataclass
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from tradingagents.platform.persistence.models import JobRow, ResearchCheckpointRow, RunRow

from .checkpoint_codec import CheckpointCodecError, SnapshotCheckpointCodec


class CheckpointStoreError(ValueError):
    """Fixed diagnostic without private state or raw storage errors."""


class CheckpointDatabaseError(CheckpointStoreError):
    """A failed/uncertain DB transaction is not permission to retry or ACK."""


@contextmanager
def _checkpoint_session(context, lock_timeout_seconds):
    if lock_timeout_seconds is None:
        raise ValueError("checkpoint lock timeout is required")
    try:
        with context.publication_session(lock_timeout_seconds=lock_timeout_seconds) as session:
            yield session
    except SQLAlchemyError:
        raise CheckpointDatabaseError("checkpoint database commit requires review") from None


def _reject():
    raise CheckpointStoreError("private checkpoint is unavailable or incompatible")


@dataclass(frozen=True)
class CheckpointCommit:
    record_id: UUID
    sequence: int
    content_hash: str


class PrivateCheckpointStore:
    """No secret/runtime data is put into the generic artifact table.

    Caller must supply a trusted original fingerprint and reviewed node set.
    Fenced commit returns only after publication_session has actually committed.
    A readable checkpoint is not an authorization to resume or reset a budget.
    """

    def __init__(self, *, codec: SnapshotCheckpointCodec):
        self.codec = codec

    def _decode(self, raw, run_id):
        value = self.codec.decode(raw)
        fields = value.config["configurable"]
        if fields["thread_id"] != str(run_id):
            _reject()
        if "run_id" in value.metadata and UUID(value.metadata["run_id"]) != run_id:
            _reject()
        return value

    def commit(self, *, context, owner_id: UUID, run_id: UUID, raw: bytes,
               lock_timeout_seconds=5.0) -> CheckpointCommit:
        value = self._decode(raw, run_id)
        digest = hashlib.sha256(raw).hexdigest()
        with _checkpoint_session(context, lock_timeout_seconds) as session:
            # publication_session already locks/renews the job and rejects
            # cancellation/expired or lost lease in this same transaction.
            job = session.get(JobRow, context.job_id)
            run = session.get(RunRow, run_id)
            if (run is None or run.owner_id != owner_id or job is None
                    or job.owner_id != owner_id or job.run_id != run_id):
                _reject()
            existing = session.scalar(select(ResearchCheckpointRow).where(
                ResearchCheckpointRow.run_id == run_id,
                ResearchCheckpointRow.content_hash == digest))
            if existing is not None:
                if (existing.owner_id != owner_id or existing.payload != raw
                        or existing.fingerprint != self.codec.fingerprint):
                    _reject()
                receipt = CheckpointCommit(existing.record_id, existing.sequence, digest)
            else:
                sequence = (session.scalar(select(func.max(ResearchCheckpointRow.sequence)).where(
                    ResearchCheckpointRow.run_id == run_id)) or 0) + 1
                record = ResearchCheckpointRow(record_id=uuid4(), owner_id=owner_id,
                    run_id=run_id, job_id=job.job_id, attempt=job.attempt,
                    sequence=sequence, fingerprint=self.codec.fingerprint,
                    checkpoint_id=UUID(value.checkpoint["id"]), content_hash=digest,
                    payload=raw, created_at=context.clock())
                session.add(record)
                session.flush()
                receipt = CheckpointCommit(record.record_id, sequence, digest)
        # Never return a successful ACK before the database context exits.
        return receipt

    def load_latest(self, *, session, owner_id: UUID, run_id: UUID):
        run = session.get(RunRow, run_id)
        if run is None or run.owner_id != owner_id:
            _reject()
        row = session.scalar(select(ResearchCheckpointRow).where(
            ResearchCheckpointRow.owner_id == owner_id,
            ResearchCheckpointRow.run_id == run_id).order_by(
                ResearchCheckpointRow.sequence.desc()).limit(1))
        if row is None:
            return None
        if (row.fingerprint != self.codec.fingerprint
                or hashlib.sha256(row.payload).hexdigest() != row.content_hash):
            _reject()  # Never fall back to an older apparently compatible row.
        try:
            value = self._decode(row.payload, run_id)
        except CheckpointCodecError:
            _reject()
        if UUID(value.checkpoint["id"]) != row.checkpoint_id:
            _reject()
        return value
