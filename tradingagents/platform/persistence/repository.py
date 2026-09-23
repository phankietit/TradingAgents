"""Owner-scoped repositories for platform contract persistence."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from tradingagents.contracts import (
    ArtifactManifest,
    DecisionCandidate,
    InstrumentContract,
    PolicyContract,
    PortfolioSnapshot,
    RunManifest,
    RunStatus,
    SnapshotManifest,
)

from .models import (
    ArtifactRow,
    DecisionRow,
    InstrumentRow,
    PolicyRow,
    PortfolioSnapshotRow,
    RunRow,
    SnapshotRow,
)

ContractT = TypeVar("ContractT", bound=BaseModel)


class ImmutableRecordConflict(ValueError):
    """A caller attempted to replace an immutable contract identifier."""


class InvalidStateTransition(ValueError):
    """A mutable lifecycle aggregate attempted an invalid transition."""


RUN_TRANSITIONS = {
    RunStatus.QUEUED: {RunStatus.RUNNING, RunStatus.CANCELLED, RunStatus.FAILED},
    RunStatus.RUNNING: {RunStatus.SUCCEEDED, RunStatus.FAILED, RunStatus.CANCELLED},
    RunStatus.SUCCEEDED: set(),
    RunStatus.FAILED: set(),
    RunStatus.CANCELLED: set(),
}


def _payload(contract: BaseModel) -> dict:
    return contract.model_dump(mode="json")


def _same_payload(row, contract: BaseModel) -> bool:
    return row.payload == _payload(contract)


class PlatformRepository:
    def __init__(self, session: Session):
        self.session = session

    def add_instrument(self, contract: InstrumentContract) -> InstrumentContract:
        existing = self.session.get(InstrumentRow, contract.instrument_id)
        if existing:
            if not _same_payload(existing, contract):
                raise ImmutableRecordConflict("instrument_id already has different content")
            return contract
        self.session.add(
            InstrumentRow(
                instrument_id=contract.instrument_id,
                schema_version=contract.schema_version,
                symbol=contract.symbol,
                canonical_symbol=contract.canonical_symbol,
                asset_class=contract.asset_class.value,
                tradability=contract.tradability.value,
                payload=_payload(contract),
                created_at=datetime.now(UTC),
            )
        )
        self.session.flush()
        return contract

    def add_artifact(self, contract: ArtifactManifest) -> ArtifactManifest:
        existing = self.session.get(ArtifactRow, contract.artifact_id)
        if existing:
            if not _same_payload(existing, contract):
                raise ImmutableRecordConflict("artifact_id already has different content")
            return contract
        self.session.add(
            ArtifactRow(
                artifact_id=contract.artifact_id,
                owner_id=contract.owner_id,
                run_id=contract.run_id,
                instrument_id=contract.instrument_id,
                snapshot_id=contract.snapshot_id,
                schema_version=contract.schema_version,
                kind=contract.kind.value,
                media_type=contract.media_type,
                content_hash=contract.content_hash,
                byte_size=contract.byte_size,
                storage_key=contract.storage_key,
                payload=_payload(contract),
                created_at=contract.created_at,
            )
        )
        self.session.flush()
        return contract

    def get_artifact(self, artifact_id: UUID, owner_id: UUID) -> ArtifactManifest | None:
        row = self.session.scalar(
            select(ArtifactRow).where(
                ArtifactRow.artifact_id == artifact_id,
                ArtifactRow.owner_id == owner_id,
            )
        )
        return ArtifactManifest.model_validate(row.payload) if row else None

    def get_instrument(self, instrument_id: UUID) -> InstrumentContract | None:
        row = self.session.get(InstrumentRow, instrument_id)
        return InstrumentContract.model_validate(row.payload) if row else None

    def add_snapshot(self, contract: SnapshotManifest) -> SnapshotManifest:
        existing = self.session.get(SnapshotRow, contract.snapshot_id)
        if existing:
            if not _same_payload(existing, contract):
                raise ImmutableRecordConflict("snapshot_id already has different content")
            return contract
        self.session.add(
            SnapshotRow(
                snapshot_id=contract.snapshot_id,
                instrument_id=contract.instrument_id,
                schema_version=contract.schema_version,
                dataset=contract.dataset,
                vendor=contract.vendor,
                as_of=contract.as_of,
                retrieved_at=contract.retrieved_at,
                content_hash=contract.content_hash,
                quality_status=contract.quality_status.value,
                payload=_payload(contract),
                created_at=datetime.now(UTC),
            )
        )
        self.session.flush()
        return contract

    def get_snapshot(self, snapshot_id: UUID) -> SnapshotManifest | None:
        row = self.session.get(SnapshotRow, snapshot_id)
        return SnapshotManifest.model_validate(row.payload) if row else None

    def save_run(self, contract: RunManifest) -> RunManifest:
        row = self.session.get(RunRow, contract.run_id)
        now = datetime.now(UTC)
        if row:
            previous = RunManifest.model_validate(row.payload)
            if (
                previous.owner_id != contract.owner_id
                or previous.instrument_id != contract.instrument_id
            ):
                raise ImmutableRecordConflict("run owner and instrument are immutable")
            if previous.status == contract.status:
                if previous != contract:
                    raise ImmutableRecordConflict("a saved run state cannot be rewritten")
                return contract
            if (
                previous.status != contract.status
                and contract.status not in RUN_TRANSITIONS[previous.status]
            ):
                raise InvalidStateTransition(
                    f"run cannot transition from {previous.status.value} to {contract.status.value}"
                )
            row.status = contract.status.value
            row.payload = _payload(contract)
            row.updated_at = now
        else:
            row = RunRow(
                run_id=contract.run_id,
                owner_id=contract.owner_id,
                instrument_id=contract.instrument_id,
                schema_version=contract.schema_version,
                status=contract.status.value,
                analysis_as_of=contract.analysis_as_of,
                created_at=contract.created_at,
                updated_at=now,
                payload=_payload(contract),
            )
            self.session.add(row)
        self.session.flush()
        return contract

    def get_run(self, run_id: UUID, owner_id: UUID) -> RunManifest | None:
        row = self.session.scalar(
            select(RunRow).where(RunRow.run_id == run_id, RunRow.owner_id == owner_id)
        )
        return RunManifest.model_validate(row.payload) if row else None

    def add_decision(self, contract: DecisionCandidate) -> DecisionCandidate:
        existing = self.session.get(DecisionRow, contract.decision_id)
        if existing:
            if not _same_payload(existing, contract):
                raise ImmutableRecordConflict("decision_id already has different content")
            return contract
        now = datetime.now(UTC)
        self.session.add(
            DecisionRow(
                decision_id=contract.decision_id,
                run_id=contract.run_id,
                owner_id=contract.owner_id,
                instrument_id=contract.instrument_id,
                schema_version=contract.schema_version,
                status=contract.status.value,
                rating=contract.rating.value,
                as_of=contract.as_of,
                payload=_payload(contract),
                created_at=now,
                updated_at=now,
            )
        )
        self.session.flush()
        return contract

    def get_decision(self, decision_id: UUID, owner_id: UUID) -> DecisionCandidate | None:
        row = self.session.scalar(
            select(DecisionRow).where(
                DecisionRow.decision_id == decision_id,
                DecisionRow.owner_id == owner_id,
            )
        )
        return DecisionCandidate.model_validate(row.payload) if row else None

    def add_portfolio_snapshot(self, contract: PortfolioSnapshot) -> PortfolioSnapshot:
        existing = self.session.get(PortfolioSnapshotRow, contract.portfolio_id)
        if existing:
            if not _same_payload(existing, contract):
                raise ImmutableRecordConflict("portfolio_id already has different content")
            return contract
        self.session.add(
            PortfolioSnapshotRow(
                portfolio_id=contract.portfolio_id,
                owner_id=contract.owner_id,
                schema_version=contract.schema_version,
                as_of=contract.as_of,
                content_hash=contract.content_hash,
                payload=_payload(contract),
                created_at=datetime.now(UTC),
            )
        )
        self.session.flush()
        return contract

    def get_portfolio_snapshot(
        self, portfolio_id: UUID, owner_id: UUID
    ) -> PortfolioSnapshot | None:
        row = self.session.scalar(
            select(PortfolioSnapshotRow).where(
                PortfolioSnapshotRow.portfolio_id == portfolio_id,
                PortfolioSnapshotRow.owner_id == owner_id,
            )
        )
        return PortfolioSnapshot.model_validate(row.payload) if row else None

    def add_policy(self, contract: PolicyContract) -> PolicyContract:
        key = (contract.policy_id, contract.policy_version)
        existing = self.session.get(PolicyRow, key)
        if existing:
            if not _same_payload(existing, contract):
                raise ImmutableRecordConflict("policy version already has different content")
            return contract
        self.session.add(
            PolicyRow(
                policy_id=contract.policy_id,
                policy_version=contract.policy_version,
                owner_id=contract.owner_id,
                schema_version=contract.schema_version,
                asset_class=contract.asset_class.value,
                effective_at=contract.effective_at,
                payload=_payload(contract),
                created_at=datetime.now(UTC),
            )
        )
        self.session.flush()
        return contract

    def get_policy(
        self, policy_id: UUID, policy_version: str, owner_id: UUID
    ) -> PolicyContract | None:
        row = self.session.scalar(
            select(PolicyRow).where(
                PolicyRow.policy_id == policy_id,
                PolicyRow.policy_version == policy_version,
                PolicyRow.owner_id == owner_id,
            )
        )
        return PolicyContract.model_validate(row.payload) if row else None
