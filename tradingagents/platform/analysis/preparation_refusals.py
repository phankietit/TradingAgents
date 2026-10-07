"""Control-only durable refusal and polling; no codec, lease or model grant."""

import re

from sqlalchemy import select, text

from tradingagents.platform.persistence.models import (
    ResearchExecutionRow,
    ResearchPreparationRefusalRow,
)

from .continuation import _db_utc, _digest
from .linked_execution import LinkedExecutionStore


def _payload(row):
    return {"format": "preparation-refusal-v1", "execution_id": str(row.execution_id),
        "observation_hash": row.observation_hash, "worker_id": row.worker_id,
        "refused_at": _db_utc(row.refused_at).isoformat(), "reason": "preparation_requires_review",
        "dispatch_authorized": False}


def validate_refusal(row, *, execution, now):
    if (row.execution_id != execution.execution_id or row.observation_hash != execution.observation_hash
            or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", row.worker_id) is None
            or _db_utc(row.refused_at) < _db_utc(execution.created_at)
            or _db_utc(row.refused_at) > now or row.payload_hash != _digest(_payload(row))):
        raise ValueError("preparation refusal requires review")


def record_preparation_refusal(*, database, execution_id, worker_id, clock):
    """Trusted worker notice only. A raced claim is never relabelled/refunded."""
    with database.session(lock_timeout_seconds=5.0) as session:
        if session.bind.dialect.name == "sqlite":
            session.execute(text("BEGIN IMMEDIATE"))
        now = clock()
        consent, observation = LinkedExecutionStore._control_source(session, execution_id, now, active=False)
        execution = LinkedExecutionStore._execution(session, consent, observation, now)
        if execution is None or execution.status != "reserved":
            return False
        row = session.get(ResearchPreparationRefusalRow, execution_id)
        if row is None:
            row = ResearchPreparationRefusalRow(execution_id=execution_id,
                observation_hash=execution.observation_hash, worker_id=worker_id, refused_at=now,
                payload_hash="")
            row.payload_hash = _digest(_payload(row))
            validate_refusal(row, execution=execution, now=now)
            session.add(row)
            session.flush()
        else:
            validate_refusal(row, execution=execution, now=now)
    return True


def next_reserved_execution(database):
    with database.session() as session:
        return session.scalar(select(ResearchExecutionRow.execution_id)
            .outerjoin(ResearchPreparationRefusalRow,
                ResearchPreparationRefusalRow.execution_id == ResearchExecutionRow.execution_id)
            .where(ResearchExecutionRow.status == "reserved", ResearchPreparationRefusalRow.execution_id.is_(None))
            .order_by(ResearchExecutionRow.created_at, ResearchExecutionRow.execution_id).limit(1))
