"""SQLAlchemy persistence models for versioned platform contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, DateTime, ForeignKey, Index, MetaData, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

JSON_VALUE = JSON().with_variant(JSONB(), "postgresql")

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class InstrumentRow(Base):
    __tablename__ = "instruments"

    instrument_id: Mapped[UUID] = mapped_column(primary_key=True)
    schema_version: Mapped[str] = mapped_column(String(16), nullable=False)
    symbol: Mapped[str] = mapped_column(String(64), nullable=False)
    canonical_symbol: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    asset_class: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    tradability: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON_VALUE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class InstrumentAliasRow(Base):
    __tablename__ = "instrument_aliases"
    __table_args__ = (
        Index("ix_instrument_aliases_instrument", "instrument_id"),
        Index("ix_instrument_aliases_lookup", "normalized_alias"),
    )

    namespace: Mapped[str] = mapped_column(String(32), primary_key=True)
    normalized_alias: Mapped[str] = mapped_column(String(128), primary_key=True)
    instrument_id: Mapped[UUID] = mapped_column(
        ForeignKey("instruments.instrument_id"), nullable=False
    )
    schema_version: Mapped[str] = mapped_column(String(16), nullable=False)
    alias: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SnapshotRow(Base):
    __tablename__ = "snapshots"
    __table_args__ = (
        UniqueConstraint("instrument_id", "dataset", "content_hash"),
        Index("ix_snapshots_instrument_as_of", "instrument_id", "as_of"),
    )

    snapshot_id: Mapped[UUID] = mapped_column(primary_key=True)
    instrument_id: Mapped[UUID] = mapped_column(
        ForeignKey("instruments.instrument_id"), nullable=False
    )
    schema_version: Mapped[str] = mapped_column(String(16), nullable=False)
    dataset: Mapped[str] = mapped_column(String(128), nullable=False)
    vendor: Mapped[str] = mapped_column(String(64), nullable=False)
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(71), nullable=False)
    quality_status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON_VALUE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RunRow(Base):
    __tablename__ = "analysis_runs"
    __table_args__ = (Index("ix_runs_owner_created", "owner_id", "created_at"),)

    run_id: Mapped[UUID] = mapped_column(primary_key=True)
    owner_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    instrument_id: Mapped[UUID] = mapped_column(
        ForeignKey("instruments.instrument_id"), nullable=False
    )
    schema_version: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    analysis_as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON_VALUE, nullable=False)


class DecisionRow(Base):
    __tablename__ = "decisions"
    __table_args__ = (Index("ix_decisions_owner_as_of", "owner_id", "as_of"),)

    decision_id: Mapped[UUID] = mapped_column(primary_key=True)
    run_id: Mapped[UUID] = mapped_column(
        ForeignKey("analysis_runs.run_id"), nullable=False, unique=True
    )
    owner_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    instrument_id: Mapped[UUID] = mapped_column(
        ForeignKey("instruments.instrument_id"), nullable=False
    )
    schema_version: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    rating: Mapped[str] = mapped_column(String(32), nullable=False)
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON_VALUE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PortfolioSnapshotRow(Base):
    __tablename__ = "portfolio_snapshots"
    __table_args__ = (Index("ix_portfolios_owner_as_of", "owner_id", "as_of"),)

    portfolio_id: Mapped[UUID] = mapped_column(primary_key=True)
    owner_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    schema_version: Mapped[str] = mapped_column(String(16), nullable=False)
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(71), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON_VALUE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class LedgerTransactionRow(Base):
    __tablename__ = "ledger_transactions"
    __table_args__ = (
        Index("ix_ledger_transactions_owner_ledger_time", "owner_id", "ledger_id", "occurred_at"),
    )

    transaction_id: Mapped[UUID] = mapped_column(primary_key=True)
    ledger_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    owner_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    schema_version: Mapped[str] = mapped_column(String(16), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(32), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON_VALUE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PolicyRow(Base):
    __tablename__ = "policies"
    __table_args__ = (Index("ix_policies_owner_effective", "owner_id", "effective_at"),)

    policy_id: Mapped[UUID] = mapped_column(primary_key=True)
    policy_version: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    schema_version: Mapped[str] = mapped_column(String(16), nullable=False)
    asset_class: Mapped[str] = mapped_column(String(32), nullable=False)
    effective_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON_VALUE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ArtifactRow(Base):
    __tablename__ = "artifacts"
    __table_args__ = (
        Index("ix_artifacts_owner_created", "owner_id", "created_at"),
        Index("ix_artifacts_owner_run", "owner_id", "run_id"),
    )

    artifact_id: Mapped[UUID] = mapped_column(primary_key=True)
    owner_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    run_id: Mapped[UUID | None] = mapped_column(ForeignKey("analysis_runs.run_id"), nullable=True)
    instrument_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("instruments.instrument_id"), nullable=True
    )
    snapshot_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("snapshots.snapshot_id"), nullable=True
    )
    schema_version: Mapped[str] = mapped_column(String(16), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    media_type: Mapped[str] = mapped_column(String(128), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(71), nullable=False, index=True)
    byte_size: Mapped[int] = mapped_column(nullable=False)
    storage_key: Mapped[str] = mapped_column(String(160), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON_VALUE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class JobRow(Base):
    __tablename__ = "analysis_jobs"
    __table_args__ = (
        UniqueConstraint("owner_id", "idempotency_key"),
        UniqueConstraint("run_id"),
        Index("ix_jobs_claim", "status", "available_at", "created_at"),
        Index("ix_jobs_expired_lease", "status", "lease_expires_at"),
        Index("ix_jobs_owner_created", "owner_id", "created_at"),
    )

    job_id: Mapped[UUID] = mapped_column(primary_key=True)
    owner_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    run_id: Mapped[UUID] = mapped_column(ForeignKey("analysis_runs.run_id"), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(16), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON_VALUE, nullable=False)
    attempt: Mapped[int] = mapped_column(nullable=False)
    max_attempts: Mapped[int] = mapped_column(nullable=False)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    lease_owner: Mapped[str | None] = mapped_column(String(128), nullable=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    output_artifact_ids: Mapped[list[str]] = mapped_column(JSON_VALUE, nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(2048), nullable=True)


class OwnerRow(Base):
    __tablename__ = "owner_accounts"

    owner_id: Mapped[UUID] = mapped_column(primary_key=True)
    singleton_key: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(254), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class OwnerSessionRow(Base):
    __tablename__ = "owner_sessions"
    __table_args__ = (Index("ix_owner_sessions_owner_expiry", "owner_id", "expires_at"),)

    session_id: Mapped[UUID] = mapped_column(primary_key=True)
    owner_id: Mapped[UUID] = mapped_column(
        ForeignKey("owner_accounts.owner_id"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    csrf_token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RunEventRow(Base):
    __tablename__ = "run_events"
    __table_args__ = (
        UniqueConstraint("run_id", "sequence"),
        Index("ix_run_events_owner_run_sequence", "owner_id", "run_id", "sequence"),
    )

    event_id: Mapped[UUID] = mapped_column(primary_key=True)
    owner_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    run_id: Mapped[UUID] = mapped_column(ForeignKey("analysis_runs.run_id"), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(16), nullable=False)
    sequence: Mapped[int] = mapped_column(nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON_VALUE, nullable=False)
