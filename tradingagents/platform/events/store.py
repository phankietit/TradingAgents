"""Owner-scoped append-only event log with per-run ordering."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import JsonValue
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from tradingagents.contracts import RunEvent, RunEventType
from tradingagents.platform.persistence.models import RunEventRow, RunRow


class RunEventNotFound(LookupError):
    """The requested owner/run pair does not exist."""


class RunEventConflict(ValueError):
    """An event identifier was reused for different immutable content."""


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _event(row: RunEventRow) -> RunEvent:
    return RunEvent(
        event_id=row.event_id,
        owner_id=row.owner_id,
        run_id=row.run_id,
        schema_version=row.schema_version,
        sequence=row.sequence,
        event_type=RunEventType(row.event_type),
        occurred_at=_utc(row.occurred_at),
        payload=row.payload,
    )


class RunEventStore:
    def __init__(self, session: Session):
        self.session = session

    def append(
        self,
        *,
        owner_id: UUID,
        run_id: UUID,
        event_type: RunEventType,
        payload: dict[str, JsonValue] | None = None,
        occurred_at: datetime | None = None,
        event_id: UUID | None = None,
    ) -> RunEvent:
        event_payload = payload or {}
        if event_id is not None:
            existing = self.session.get(RunEventRow, event_id)
            if existing:
                existing_event = _event(existing)
                if (
                    existing_event.owner_id == owner_id
                    and existing_event.run_id == run_id
                    and existing_event.event_type is event_type
                    and existing_event.payload == event_payload
                    and (occurred_at is None or existing_event.occurred_at == _utc(occurred_at))
                ):
                    return existing_event
                raise RunEventConflict("event_id already has different content")
        run = self.session.scalar(
            select(RunRow)
            .where(RunRow.run_id == run_id, RunRow.owner_id == owner_id)
            .with_for_update()
        )
        if run is None:
            raise RunEventNotFound("run not found for owner")
        next_sequence = (
            self.session.scalar(
                select(func.coalesce(func.max(RunEventRow.sequence), 0)).where(
                    RunEventRow.run_id == run_id
                )
            )
            + 1
        )
        event = RunEvent(
            event_id=event_id or uuid4(),
            owner_id=owner_id,
            run_id=run_id,
            sequence=next_sequence,
            event_type=event_type,
            occurred_at=_utc(occurred_at or datetime.now(UTC)),
            payload=event_payload,
        )
        self.session.add(
            RunEventRow(
                event_id=event.event_id,
                owner_id=owner_id,
                run_id=run_id,
                schema_version=event.schema_version,
                sequence=event.sequence,
                event_type=event_type.value,
                occurred_at=event.occurred_at,
                payload=event.payload,
            )
        )
        self.session.flush()
        return event

    def list_after(
        self,
        owner_id: UUID,
        run_id: UUID,
        *,
        after_sequence: int = 0,
        limit: int = 100,
    ) -> tuple[RunEvent, ...]:
        if after_sequence < 0:
            raise ValueError("after_sequence cannot be negative")
        if not 1 <= limit <= 500:
            raise ValueError("limit must be between 1 and 500")
        run_exists = self.session.scalar(
            select(RunRow.run_id).where(RunRow.run_id == run_id, RunRow.owner_id == owner_id)
        )
        if run_exists is None:
            raise RunEventNotFound("run not found for owner")
        rows = self.session.scalars(
            select(RunEventRow)
            .where(
                RunEventRow.owner_id == owner_id,
                RunEventRow.run_id == run_id,
                RunEventRow.sequence > after_sequence,
            )
            .order_by(RunEventRow.sequence)
            .limit(limit)
        ).all()
        return tuple(_event(row) for row in rows)
