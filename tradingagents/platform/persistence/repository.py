"""Owner-scoped repositories for platform contract persistence."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from tradingagents.contracts import (
    ArtifactManifest,
    AssetClass,
    DecisionCandidate,
    DecisionLifecycleEvent,
    DecisionStatus,
    InstrumentAliasContract,
    InstrumentContract,
    LedgerTransaction,
    PolicyContract,
    PortfolioSnapshot,
    RunManifest,
    RunStatus,
    SnapshotManifest,
    Tradability,
    normalize_instrument_alias,
)

from .models import (
    ArtifactRow,
    DecisionLifecycleEventRow,
    DecisionRow,
    InstrumentAliasRow,
    InstrumentRow,
    LedgerTransactionRow,
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


class AmbiguousInstrumentAlias(ValueError):
    """An unqualified alias refers to more than one canonical instrument."""


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
    def __init__(self, session: Session, *, artifact_store=None):
        self.session = session
        self.artifact_store = artifact_store

    def add_instrument(self, contract: InstrumentContract) -> InstrumentContract:
        existing = self.session.get(InstrumentRow, contract.instrument_id)
        if existing:
            if not _same_payload(existing, contract):
                raise ImmutableRecordConflict("instrument_id already has different content")
            self._ensure_primary_instrument_aliases(contract)
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
        self._ensure_primary_instrument_aliases(contract)
        return contract

    def _ensure_primary_instrument_aliases(self, contract: InstrumentContract) -> None:
        self.add_instrument_alias(
            InstrumentAliasContract.create(
                instrument_id=contract.instrument_id,
                namespace="canonical",
                alias=contract.canonical_symbol,
            )
        )
        if normalize_instrument_alias(contract.symbol) != normalize_instrument_alias(
            contract.canonical_symbol
        ):
            self.add_instrument_alias(
                InstrumentAliasContract.create(
                    instrument_id=contract.instrument_id,
                    namespace="symbol",
                    alias=contract.symbol,
                )
            )

    def add_instrument_alias(
        self, contract: InstrumentAliasContract
    ) -> InstrumentAliasContract:
        instrument = self.session.get(InstrumentRow, contract.instrument_id)
        if instrument is None:
            raise ValueError("instrument alias requires an existing instrument")
        if contract.namespace == "canonical" and contract.normalized_alias != normalize_instrument_alias(
            instrument.canonical_symbol
        ):
            raise ValueError("canonical alias must match the instrument canonical symbol")

        existing = self.session.get(
            InstrumentAliasRow,
            (contract.namespace, contract.normalized_alias),
        )
        if existing:
            if existing.instrument_id != contract.instrument_id:
                raise ImmutableRecordConflict(
                    "instrument alias already belongs to another instrument"
                )
            return InstrumentAliasContract(
                instrument_id=existing.instrument_id,
                namespace=existing.namespace,
                alias=existing.alias,
                normalized_alias=existing.normalized_alias,
                schema_version=existing.schema_version,
            )

        canonical_collision = self.session.scalar(
            select(InstrumentAliasRow).where(
                InstrumentAliasRow.namespace == "canonical",
                InstrumentAliasRow.normalized_alias == contract.normalized_alias,
                InstrumentAliasRow.instrument_id != contract.instrument_id,
            )
        )
        alias_collision = None
        if contract.namespace == "canonical":
            alias_collision = self.session.scalar(
                select(InstrumentAliasRow).where(
                    InstrumentAliasRow.normalized_alias == contract.normalized_alias,
                    InstrumentAliasRow.instrument_id != contract.instrument_id,
                )
            )
        if canonical_collision is not None or alias_collision is not None:
            raise ImmutableRecordConflict(
                "instrument alias conflicts with another canonical instrument"
            )

        self.session.add(
            InstrumentAliasRow(
                instrument_id=contract.instrument_id,
                namespace=contract.namespace,
                alias=contract.alias,
                normalized_alias=contract.normalized_alias,
                schema_version=contract.schema_version,
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

    def list_instrument_aliases(
        self, instrument_id: UUID
    ) -> tuple[InstrumentAliasContract, ...]:
        rows = self.session.scalars(
            select(InstrumentAliasRow)
            .where(InstrumentAliasRow.instrument_id == instrument_id)
            .order_by(InstrumentAliasRow.namespace, InstrumentAliasRow.normalized_alias)
        ).all()
        return tuple(
            InstrumentAliasContract(
                instrument_id=row.instrument_id,
                namespace=row.namespace,
                alias=row.alias,
                normalized_alias=row.normalized_alias,
                schema_version=row.schema_version,
            )
            for row in rows
        )

    def resolve_instrument(
        self,
        alias: str,
        *,
        namespace: str | None = None,
    ) -> InstrumentContract | None:
        normalized_alias = normalize_instrument_alias(alias)
        statement = select(InstrumentAliasRow.instrument_id).where(
            InstrumentAliasRow.normalized_alias == normalized_alias
        )
        if namespace is not None:
            statement = statement.where(InstrumentAliasRow.namespace == namespace)
        instrument_ids = set(self.session.scalars(statement).all())
        if not instrument_ids:
            return None
        if len(instrument_ids) > 1:
            raise AmbiguousInstrumentAlias(
                "instrument alias is ambiguous; provide an alias namespace"
            )
        return self.get_instrument(instrument_ids.pop())

    def list_instruments(
        self,
        *,
        asset_class: AssetClass | None = None,
        tradability: Tradability | None = None,
        venue: str | None = None,
        limit: int = 100,
    ) -> tuple[InstrumentContract, ...]:
        if not 1 <= limit <= 500:
            raise ValueError("limit must be between 1 and 500")
        statement = select(InstrumentRow)
        if asset_class is not None:
            statement = statement.where(InstrumentRow.asset_class == asset_class.value)
        if tradability is not None:
            statement = statement.where(InstrumentRow.tradability == tradability.value)
        if venue is not None:
            statement = statement.where(InstrumentRow.payload["venue"].as_string() == venue)
        rows = self.session.scalars(
            statement.order_by(InstrumentRow.canonical_symbol).limit(limit)
        ).all()
        return tuple(InstrumentContract.model_validate(row.payload) for row in rows)

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

    def latest_snapshot(
        self,
        *,
        instrument_id: UUID,
        dataset: str,
        as_of: datetime,
    ) -> SnapshotManifest | None:
        row = self.session.scalar(
            select(SnapshotRow)
            .where(
                SnapshotRow.instrument_id == instrument_id,
                SnapshotRow.dataset == dataset,
                SnapshotRow.as_of <= as_of,
            )
            .order_by(SnapshotRow.as_of.desc(), SnapshotRow.retrieved_at.desc())
            .limit(1)
        )
        return SnapshotManifest.model_validate(row.payload) if row else None

    def get_snapshot_artifact(
        self, snapshot_id: UUID, owner_id: UUID
    ) -> ArtifactManifest | None:
        row = self.session.scalar(
            select(ArtifactRow)
            .where(
                ArtifactRow.snapshot_id == snapshot_id,
                ArtifactRow.owner_id == owner_id,
                ArtifactRow.kind == "snapshot_payload",
            )
            .order_by(ArtifactRow.created_at)
            .limit(1)
        )
        return ArtifactManifest.model_validate(row.payload) if row else None

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

    def list_runs(self, owner_id: UUID, *, limit: int = 50) -> tuple[RunManifest, ...]:
        if not 1 <= limit <= 200:
            raise ValueError("limit must be between 1 and 200")
        rows = self.session.scalars(
            select(RunRow)
            .where(RunRow.owner_id == owner_id)
            .order_by(RunRow.created_at.desc(), RunRow.run_id.desc())
            .limit(limit)
        ).all()
        return tuple(RunManifest.model_validate(row.payload) for row in rows)

    def add_decision(self, contract: DecisionCandidate) -> DecisionCandidate:
        contract = DecisionCandidate.model_validate(contract.model_dump())
        run = self.get_run(contract.run_id, contract.owner_id)
        if run is None or run.instrument_id != contract.instrument_id or run.analysis_as_of != contract.as_of:
            raise ValueError("decision does not match its owner run")
        if contract.status is DecisionStatus.APPROVED:
            raise ValueError("approval must be recorded through lifecycle events")
        if contract.status is DecisionStatus.READY_FOR_APPROVAL:
            self._validate_decision_sources(contract)
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

    def add_decision_event(self, contract: DecisionLifecycleEvent) -> DecisionLifecycleEvent:
        from tradingagents.platform.decisions import DecisionLifecycle

        contract = DecisionLifecycleEvent.model_validate(contract.model_dump())
        row = self.session.scalar(select(DecisionRow).where(
            DecisionRow.decision_id == contract.decision_id,
            DecisionRow.owner_id == contract.owner_id,
        ).with_for_update())
        if row is None:
            raise ValueError("decision not found")
        existing = self.session.get(DecisionLifecycleEventRow, contract.event_id)
        if existing:
            if not _same_payload(existing, contract):
                raise ImmutableRecordConflict("decision event already has different content")
            return contract
        decision = DecisionCandidate.model_validate(row.payload)
        history = self.list_decision_events(contract.decision_id, contract.owner_id)
        if history and contract.occurred_at <= max(item.occurred_at for item in history):
            raise InvalidStateTransition("event must follow the previous event timestamp")
        new_status = DecisionLifecycle().apply(decision, (*history, contract))
        if contract.from_status.value != row.status:
            raise InvalidStateTransition("decision state changed")
        if contract.to_status in {DecisionStatus.READY_FOR_APPROVAL, DecisionStatus.APPROVED}:
            self._validate_decision_sources(decision)
        previous_updated_at = row.updated_at
        result = self.session.execute(update(DecisionRow).where(
            DecisionRow.decision_id == contract.decision_id,
            DecisionRow.owner_id == contract.owner_id,
            DecisionRow.status == contract.from_status.value,
            DecisionRow.updated_at == previous_updated_at,
        ).values(status=new_status.value, updated_at=datetime.now(UTC)))
        if result.rowcount != 1:
            raise InvalidStateTransition("concurrent decision transition")
        self.session.add(
            DecisionLifecycleEventRow(
                event_id=contract.event_id,
                decision_id=contract.decision_id,
                owner_id=contract.owner_id,
                schema_version=contract.schema_version,
                from_status=contract.from_status.value,
                to_status=contract.to_status.value,
                occurred_at=contract.occurred_at,
                payload=_payload(contract),
                created_at=datetime.now(UTC),
            )
        )
        self.session.flush()
        return contract

    def _validate_decision_sources(self, decision: DecisionCandidate) -> None:
        from tradingagents.contracts.decisions import require_decision_readiness

        require_decision_readiness(decision)
        run = self.get_run(decision.run_id, decision.owner_id)
        if run is None or run.instrument_id != decision.instrument_id:
            raise ValueError("decision owner run mismatch")
        for evidence in decision.evidence:
            source = self.get_snapshot(evidence.snapshot_id)
            if (
                source is None or source.snapshot_id not in run.snapshot_ids
                or source.instrument_id != decision.instrument_id
                or source.content_hash != evidence.content_hash
                or source.vendor != evidence.source_name
                or source.source_end != evidence.source_at
                or source.retrieved_at != evidence.observed_at
                or source.as_of > decision.as_of
                or source.quality_status.value != "OK"
            ):
                raise ValueError("decision evidence does not match persisted run source")
        check = decision.policy_checks[0]
        policy = self.get_policy(check.policy_id, check.policy_version, decision.owner_id)
        instrument = self.get_instrument(decision.instrument_id)
        if policy is None or policy.effective_at > decision.as_of or instrument is None or policy.asset_class != instrument.asset_class:
            raise ValueError("decision policy is not eligible for this owner instrument")
        self._validate_decision_risk(decision, policy, instrument)

    def _validate_decision_risk(self, decision, policy, instrument) -> None:
        from tradingagents.platform.risk import RiskEngine, RiskProposal

        portfolio = (
            self.get_portfolio_snapshot(decision.portfolio_snapshot_id, decision.owner_id)
            if decision.portfolio_snapshot_id is not None else None
        )
        if portfolio is None or portfolio.as_of != decision.as_of:
            raise ValueError("decision requires an owner portfolio snapshot at its as_of")
        classifications = {}
        for position in portfolio.positions:
            held = self.get_instrument(position.instrument_id)
            if held is None:
                raise ValueError("portfolio instrument classification is unavailable")
            classifications[position.instrument_id] = held.asset_class
        from tradingagents.platform.risk.provenance import replay_correlations

        correlations = replay_correlations(self, decision, portfolio, policy)
        assessment = RiskEngine().evaluate(
            portfolio=portfolio, policy=policy,
            proposal=RiskProposal(
                instrument_id=instrument.instrument_id, asset_class=instrument.asset_class,
                tradability=instrument.tradability, target_weight=decision.target_weight,
                data_quality=decision.data_quality, position_asset_classes=classifications,
                correlations=correlations,
            ),
        )
        current_weight = next((p.weight for p in portfolio.positions
                               if p.instrument_id == decision.instrument_id), 0.0)
        expected = {item.check_id: item for item in assessment.checks}
        supplied = {item.check_id: item for item in decision.policy_checks}
        if (not assessment.passed or expected != supplied
                or decision.current_weight != current_weight
                or decision.max_allowed_weight != assessment.max_allowed_weight):
            raise ValueError("decision risk assessment does not match persisted inputs")

    def list_decision_events(
        self, decision_id: UUID, owner_id: UUID
    ) -> tuple[DecisionLifecycleEvent, ...]:
        rows = self.session.scalars(
            select(DecisionLifecycleEventRow)
            .where(
                DecisionLifecycleEventRow.decision_id == decision_id,
                DecisionLifecycleEventRow.owner_id == owner_id,
            )
            .order_by(
                DecisionLifecycleEventRow.occurred_at,
                DecisionLifecycleEventRow.event_id,
            )
        ).all()
        return tuple(DecisionLifecycleEvent.model_validate(row.payload) for row in rows)

    def list_decisions(
        self, owner_id: UUID, *, limit: int = 50
    ) -> tuple[DecisionCandidate, ...]:
        if not 1 <= limit <= 200:
            raise ValueError("limit must be between 1 and 200")
        rows = self.session.scalars(
            select(DecisionRow)
            .where(DecisionRow.owner_id == owner_id)
            .order_by(DecisionRow.as_of.desc(), DecisionRow.decision_id.desc())
            .limit(limit)
        ).all()
        return tuple(DecisionCandidate.model_validate(row.payload) for row in rows)

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

    def add_ledger_transaction(self, contract: LedgerTransaction) -> LedgerTransaction:
        contract = LedgerTransaction.model_validate(contract.model_dump())
        existing = self.session.get(LedgerTransactionRow, contract.transaction_id)
        if existing:
            if not _same_payload(existing, contract):
                raise ImmutableRecordConflict("transaction_id already has different content")
            return contract
        self.session.add(
            LedgerTransactionRow(
                transaction_id=contract.transaction_id,
                ledger_id=contract.ledger_id,
                owner_id=contract.owner_id,
                schema_version=contract.schema_version,
                transaction_type=contract.transaction_type.value,
                occurred_at=contract.occurred_at,
                payload=_payload(contract),
                created_at=datetime.now(UTC),
            )
        )
        self.session.flush()
        return contract

    def list_ledger_transactions(
        self, ledger_id: UUID, owner_id: UUID
    ) -> tuple[LedgerTransaction, ...]:
        rows = self.session.scalars(
            select(LedgerTransactionRow)
            .where(
                LedgerTransactionRow.ledger_id == ledger_id,
                LedgerTransactionRow.owner_id == owner_id,
            )
            .order_by(LedgerTransactionRow.occurred_at, LedgerTransactionRow.transaction_id)
        ).all()
        return tuple(LedgerTransaction.model_validate(row.payload) for row in rows)

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
