"""Parent-only linked reader/output publication; default routes stay disabled.

Uses the ordinary report/evidence/risk pipeline. Completion is a separate
receipt, not permission to rewrite terminal history or approve a decision.
"""

import hashlib
import json
from dataclasses import asdict, dataclass
from uuid import UUID, uuid5

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from tradingagents.contracts import ArtifactKind, RunEventType
from tradingagents.platform.artifacts import ArtifactService
from tradingagents.platform.jobs import DurableJobQueue
from tradingagents.platform.jobs.decision_pipeline import build_run_decision
from tradingagents.platform.jobs.report import build_run_report
from tradingagents.platform.persistence import PlatformRepository
from tradingagents.platform.persistence.models import (
    ArtifactRow,
    DecisionRow,
    ResearchCheckpointExecutionRow,
    ResearchCheckpointRow,
    ResearchContinuationRow,
    ResearchExecutionArtifactRow,
    ResearchExecutionCompletionRow,
    ResearchExecutionDispatchRow,
    ResearchExecutionEventRow,
    ResearchExecutionRow,
    RunEventRow,
)

from .accounting import load_accounting_evidence
from .checkpoint_store import PrivateCheckpointStore
from .continuation import _canonical, _db_utc, _digest
from .engine import AnalysisResult
from .linked_execution import _reject
from .linked_publication import LinkedPublicationContext
from .linked_recording import (
    LinkedOriginalResearch,
    _artifact_columns,
    _owned_sources,
    _snapshot_columns,
    _SourceBinding,
    validate_linked_recording,
)
from .observer import STAGES
from .snapshots import AnalysisSnapshot
from .stage_records import ResearchStageService


class LinkedResultPublisher:
    """Exact bound callback, never a browser/model-selectable result sink."""

    def __init__(self, artifact_store):
        self.artifact_store = artifact_store
        self.context = None
        self.original = None

    def __repr__(self):
        return object.__repr__(self)

    def bind(self, context, original):
        binding = getattr(context, "_linked_source_binding", None)
        if (type(self) is not LinkedResultPublisher or type(context) is not LinkedPublicationContext or type(original) is not LinkedOriginalResearch
                or self.context is not None or getattr(context, "_result_publisher", None) is not None
                or getattr(context.observer.save_stage, "__self__", None) is not self
                or getattr(context.observer.save_stage, "__func__", None) is not LinkedResultPublisher.save_stage
                or type(binding) is not _SourceBinding or binding.artifact_store is not self.artifact_store):
            _reject()
        validate_linked_recording(context=context, recording_inputs=original.recording_inputs,
            request=original.request, restore_checkpoint=original.restore_checkpoint)
        self.context, self.original = context, original
        context._result_publisher = self

    def _bound(self):
        context = self.context
        binding = getattr(context, "_linked_source_binding", None)
        if (type(context) is not LinkedPublicationContext or type(self.original) is not LinkedOriginalResearch
                or getattr(context, "_result_publisher", None) is not self
                or getattr(context.observer.save_stage, "__self__", None) is not self
                or getattr(context.observer.save_stage, "__func__", None) is not LinkedResultPublisher.save_stage
                or type(binding) is not _SourceBinding or binding.artifact_store is not self.artifact_store
                or hashlib.sha256(self.original.recording_inputs.raw).hexdigest() != context._linked_source_binding.recording_hash
                or _digest(self.original.request.model_dump(mode="json")) != context._linked_source_binding.request_hash):
            _reject()
        context._observer()
        return context

    def _original_sources(self, session, context):
        _, observation, _ = context._store._source(session, context.execution_id, context.clock())
        value = self.original.recording_inputs.read()
        repository = PlatformRepository(session)
        run = repository.get_run(context.run_id, context.owner_id)
        if (run is None or _canonical(run.model_dump(mode="json")) != _canonical(value.run.model_dump(mode="json"))
                or value.source_run_hash != observation["source_run_hash"]
                or value.source_job_hash != observation["source_job_hash"]):
            _reject()
        sources = _owned_sources(session, context, self.artifact_store, run)
        if _digest(sources.model_dump(mode="json")) != context._linked_source_binding.sources_hash:
            _reject()
        if value.portfolio_snapshot is not None:
            book = repository.get_portfolio_snapshot(value.portfolio_snapshot.portfolio_id, context.owner_id)
            policy = repository.get_policy(value.policy.policy_id, value.policy.policy_version, context.owner_id)
            if (book is None or policy is None or book.model_dump(mode="json") != value.portfolio_snapshot.model_dump(mode="json")
                    or policy.model_dump(mode="json") != value.policy.model_dump(mode="json")):
                _reject()
        artifacts = ArtifactService(self.artifact_store, repository)
        for source in value.risk_snapshots:
            manifest = repository.get_snapshot(source.manifest.snapshot_id)
            artifact = repository.get_snapshot_artifact(source.manifest.snapshot_id, context.owner_id)
            if manifest is None or artifact is None:
                _reject()
            _snapshot_columns(session, manifest)
            _artifact_columns(session, artifact)
            loaded = artifacts.read(artifact.artifact_id, context.owner_id)
            if loaded is None or AnalysisSnapshot(manifest=manifest, payload=loaded[1].decode()).model_dump() != source.model_dump():
                _reject()
        return run, sources

    def save_stage(self, stage, outputs):
        try:
            return self._save_stage(stage, outputs)
        except (ValueError, TypeError, KeyError, AttributeError, OSError, UnicodeError, SQLAlchemyError):
            _reject()

    def _save_stage(self, stage, outputs):
        context = self._bound()
        if context.observer._execution_stopped or type(stage) is not str or stage not in STAGES:
            _reject()
        with context.publication_session() as session:
            run, _ = self._original_sources(session, context)
            if session.get(ResearchExecutionDispatchRow, context.execution_id) is None:
                _reject()
            sequence = session.scalar(select(func.count()).select_from(ResearchExecutionArtifactRow).join(
                ArtifactRow, ArtifactRow.artifact_id == ResearchExecutionArtifactRow.artifact_id).where(
                ResearchExecutionArtifactRow.execution_id == context.execution_id,
                ArtifactRow.kind == ArtifactKind.RESEARCH_STAGE.value)) + 1
            manifest = ResearchStageService(ArtifactService(self.artifact_store, PlatformRepository(session))).persist(
                run, stage=stage, outputs=outputs, attempt=context._lease.reservation.attempt,
                sequence=sequence, snapshot_attestation="PASS")
            if manifest is not None:
                session.add(ResearchExecutionArtifactRow(artifact_id=manifest.artifact_id, execution_id=context.execution_id))
                context._append(session, RunEventType.ARTIFACT_CREATED, {
                    "artifact_id": str(manifest.artifact_id), "kind": manifest.kind.value,
                    "stage": stage, "research_quality": "unvalidated"}, context.clock())
                identity = manifest.artifact_id
            else:
                identity = None
        return identity  # ACK after actor/event/artifact commit, no raw text in event.

    def publish_completed(self, supervisor, result, request):
        try:
            return self._publish_completed(supervisor, result, request)
        except (ValueError, TypeError, KeyError, AttributeError, OSError, UnicodeError, SQLAlchemyError):
            _reject()

    def _publish_completed(self, supervisor, result, request):
        from .supervision import RESULT_FIELDS, SupervisedAnalysisEngine

        context = self._bound()
        if (type(supervisor) is not SupervisedAnalysisEngine or supervisor.linked_context is not context
                or supervisor._linked_return_result is not result or supervisor._linked_clean_exit is not True
                or type(result) is not AnalysisResult or not context.observer._execution_stopped
                or request.execution_observer is not context.observer
                or _digest(request.model_dump(mode="json")) != context._linked_source_binding.request_hash
                or set(result.final_state) - RESULT_FIELDS or result.instrument != request.instrument
                or result.analysis_date != request.analysis_date
                or result.selected_analysts != request.selected_analysts):
            _reject()
        with context.publication_session() as session:
            run, sources = self._original_sources(session, context)
            dispatch = session.get(ResearchExecutionDispatchRow, context.execution_id)
            checkpoint = session.scalar(select(ResearchCheckpointRow).where(
                ResearchCheckpointRow.run_id == context.run_id).order_by(ResearchCheckpointRow.sequence.desc()).limit(1))
            actor = session.get(ResearchCheckpointExecutionRow, checkpoint.record_id) if checkpoint else None
            if (dispatch is None or dispatch.checkpoint_record_id != self.original.recording_inputs.read().checkpoint_record_id
                    or dispatch.checkpoint_hash != self.original.recording_inputs.read().checkpoint_hash
                    or checkpoint is None or actor is None or actor.execution_id != context.execution_id
                    or checkpoint.attempt != context._lease.reservation.attempt
                    or session.get(ResearchExecutionCompletionRow, context.execution_id) is not None
                    or session.scalar(select(DecisionRow.decision_id).where(DecisionRow.run_id == run.run_id)) is not None
                    or session.scalar(select(ArtifactRow.artifact_id).where(ArtifactRow.run_id == run.run_id,
                        ArtifactRow.kind == ArtifactKind.ANALYSIS_REPORT.value)) is not None):
                _reject()
            PrivateCheckpointStore(codec=context._store.consents.codec).load_latest(
                session=session, owner_id=context.owner_id, run_id=context.run_id)
            accounting = load_accounting_evidence(session=session, owner_id=context.owner_id, run_id=context.run_id)
            if (accounting.evidence_status != "PASS" or accounting.elapsed_upper_bound is None
                    or accounting.attempts[-1] != context._lease.reservation.attempt
                    or accounting.started_calls > accounting.original_model_calls
                    or accounting.elapsed_upper_bound > accounting.original_wall_seconds
                    or context.observer.started_calls != context.observer.usage["model_calls"]
                    or context.observer.usage["failed_calls"] != 0):
                _reject()
            repository = PlatformRepository(session, artifact_store=self.artifact_store)
            artifacts = ArtifactService(self.artifact_store, repository)
            report = build_run_report(run, result, instrument=request.instrument,
                snapshot_context=sources, observer=context.observer)
            candidate, evidence = build_run_decision(artifacts, run, result)
            report["evidence_artifact_id"] = str(evidence.artifact_id) if evidence else None
            report["linked_execution"] = {"execution_id": str(context.execution_id),
                "attempt": context._lease.reservation.attempt, "source_job_id": str(context.job_id),
                "source_run_hash": self.original.recording_inputs.read().source_run_hash,
                "original_run_status": run.status.value, "original_run_unchanged": True,
                "accounting": asdict(accounting), "checkpoint_hash": checkpoint.content_hash,
                "result_hash": _digest(result.model_dump(mode="json"))}
            # JSON UUIDs only for the internal cumulative accounting metadata.
            report["linked_execution"]["accounting"].update(owner_id=str(context.owner_id), run_id=str(context.run_id))
            report_id = uuid5(run.run_id, "analysis-report-v1")
            manifest = artifacts.create(artifact_id=report_id, owner_id=context.owner_id, run_id=context.run_id,
                instrument_id=run.instrument_id, kind=ArtifactKind.ANALYSIS_REPORT, media_type="application/json",
                created_at=context.clock(), content=json.dumps(report, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())
            repository.add_decision(candidate)
            for identity in (report_id, *((evidence.artifact_id,) if evidence else ())):
                session.add(ResearchExecutionArtifactRow(artifact_id=identity, execution_id=context.execution_id))
            session.flush()
            session.add(ResearchExecutionCompletionRow(execution_id=context.execution_id,
                checkpoint_record_id=checkpoint.record_id, checkpoint_hash=checkpoint.content_hash,
                report_artifact_id=manifest.artifact_id, evidence_artifact_id=evidence.artifact_id if evidence else None,
                decision_id=candidate.decision_id, result_hash=_digest(result.model_dump(mode="json")),
                accounting_hash=_digest(asdict(accounting)), report_hash=manifest.content_hash,
                decision_hash=_digest(candidate.model_dump(mode="json")),
                evidence_hash=evidence.content_hash if evidence else None, completed_at=context.clock()))
            session.flush()
            output = (report_id, *((evidence.artifact_id,) if evidence else ()))
        return output  # Only after final context fence and commit; ACK loss is not replay.


@dataclass(frozen=True, repr=False)
class LinkedCompletionReceipt:
    """Read-only verified output identities, not execution or approval authority."""

    execution_id: UUID
    run_id: UUID
    report_artifact_id: UUID
    evidence_artifact_id: UUID | None
    decision_id: UUID


def read_linked_completion(*, session, artifact_store, owner_id, execution_id):
    """Owner-scoped read after uncertain ACK; never starts/retries a model.

    No live lease is required to read old evidence. API callers must separately
    authenticate owner_id; these private arguments are not bearer permissions.
    """
    try:
        if type(owner_id) is not UUID or type(execution_id) is not UUID:
            _reject()
        receipt = session.get(ResearchExecutionCompletionRow, execution_id)
        execution = session.get(ResearchExecutionRow, execution_id)
        consent = session.get(ResearchContinuationRow, execution_id)
        if receipt is None:
            return None
        if (execution is None or consent is None or execution.owner_id != owner_id or consent.owner_id != owner_id
                or execution.source_run_id != consent.source_run_id or execution.source_job_id != consent.source_job_id
                or execution.observation_hash != consent.observation_hash or _digest(consent.payload) != consent.observation_hash):
            _reject()
        repository = PlatformRepository(session)
        run = repository.get_run(execution.source_run_id, owner_id)
        job = DurableJobQueue(session).get(execution.source_job_id, owner_id)
        if (run is None or job is None or job.run_id != run.run_id
                or _digest(run.model_dump(mode="json")) != consent.payload["observation"]["source_run_hash"]
                or _digest(job.model_dump(mode="json")) != consent.payload["observation"]["source_job_hash"]):
            _reject()
        from .checkpoint_store import _provenance
        from .linked_publication import validate_entry

        validate_entry(session, execution)
        dispatch = session.get(ResearchExecutionDispatchRow, execution_id)
        checkpoint = session.get(ResearchCheckpointRow, receipt.checkpoint_record_id)
        original = session.get(ResearchCheckpointRow, consent.checkpoint_record_id)
        actor = session.get(ResearchCheckpointExecutionRow, receipt.checkpoint_record_id)
        if (dispatch is None or dispatch.checkpoint_record_id != consent.checkpoint_record_id
                or dispatch.checkpoint_hash != consent.payload["observation"]["checkpoint_content_hash"]
                or original is None or original.owner_id != owner_id or original.run_id != run.run_id
                or original.job_id != execution.source_job_id or original.attempt != execution.attempt - 1
                or original.content_hash != dispatch.checkpoint_hash
                or hashlib.sha256(original.payload).hexdigest() != original.content_hash
                or checkpoint is None or actor is None or actor.execution_id != execution_id
                or checkpoint.fingerprint != original.fingerprint
                or checkpoint.owner_id != owner_id or checkpoint.run_id != run.run_id or checkpoint.job_id != execution.source_job_id
                or checkpoint.attempt != execution.attempt or checkpoint.content_hash != receipt.checkpoint_hash
                or hashlib.sha256(checkpoint.payload).hexdigest() != receipt.checkpoint_hash
                or execution.started_at is None or not _db_utc(execution.started_at) <= _db_utc(receipt.completed_at) < _db_utc(execution.lease_expires_at)
                or _db_utc(receipt.completed_at) >= _db_utc(execution.deadline_at)):
            _reject()
        _provenance(session, checkpoint)
        artifacts = ArtifactService(artifact_store, repository)
        stored = artifacts.read(receipt.report_artifact_id, owner_id)
        candidate = repository.get_decision(receipt.decision_id, owner_id)
        if stored is None or candidate is None:
            _reject()
        manifest, raw = stored
        _artifact_columns(session, manifest)
        report = json.loads(raw)
        binding = report["linked_execution"]
        if (manifest.run_id != run.run_id or manifest.instrument_id != run.instrument_id
                or manifest.kind is not ArtifactKind.ANALYSIS_REPORT or manifest.content_hash != receipt.report_hash
                or report["run_id"] != str(run.run_id) or report["decision_id"] != str(receipt.decision_id)
                or binding["execution_id"] != str(execution_id) or type(binding["attempt"]) is not int
                or binding["attempt"] != execution.attempt or binding["checkpoint_hash"] != receipt.checkpoint_hash
                or binding["result_hash"] != receipt.result_hash or binding["source_job_id"] != str(execution.source_job_id)
                or binding["source_run_hash"] != consent.payload["observation"]["source_run_hash"]
                or binding["original_run_status"] != run.status.value or binding["original_run_unchanged"] is not True
                or candidate.run_id != run.run_id or candidate.instrument_id != run.instrument_id
                or _digest(candidate.model_dump(mode="json")) != receipt.decision_hash):
            _reject()
        decision_row = session.get(DecisionRow, receipt.decision_id)
        if (decision_row.owner_id, decision_row.run_id, decision_row.instrument_id, decision_row.rating) != (
                owner_id, run.run_id, run.instrument_id, candidate.rating.value):
            _reject()
        accounting = load_accounting_evidence(session=session, owner_id=owner_id, run_id=run.run_id)
        if (_digest(asdict(accounting)) != receipt.accounting_hash or accounting.elapsed_upper_bound is None
                or _canonical(asdict(accounting)) != _canonical(binding["accounting"])):
            _reject()
        for event in session.scalars(select(RunEventRow).where(RunEventRow.owner_id == owner_id,
                RunEventRow.run_id == run.run_id, RunEventRow.sequence <= accounting.high_water_sequence)):
            if event.payload.get("attempt") == execution.attempt:
                link = session.get(ResearchExecutionEventRow, event.event_id)
                if link is None or link.execution_id != execution_id:
                    _reject()
        for identity in (receipt.report_artifact_id, *((receipt.evidence_artifact_id,) if receipt.evidence_artifact_id else ())):
            link = session.get(ResearchExecutionArtifactRow, identity)
            if link is None or link.execution_id != execution_id:
                _reject()
        if receipt.evidence_artifact_id is not None:
            from .evidence_service import EvidenceGraphService

            stored_evidence = artifacts.read(receipt.evidence_artifact_id, owner_id)
            if stored_evidence is None:
                _reject()
            _artifact_columns(session, stored_evidence[0])
            graph = EvidenceGraphService(artifacts).read(receipt.evidence_artifact_id, owner_id)
            if (stored_evidence[0].content_hash != receipt.evidence_hash or graph.evidence != candidate.evidence
                    or report["evidence_artifact_id"] != str(receipt.evidence_artifact_id)):
                _reject()
        elif receipt.evidence_hash is not None or candidate.evidence or report["evidence_artifact_id"] is not None:
            _reject()
        return LinkedCompletionReceipt(execution_id, run.run_id, manifest.artifact_id,
            receipt.evidence_artifact_id, candidate.decision_id)
    except (ValueError, TypeError, KeyError, AttributeError, OSError, UnicodeError, SQLAlchemyError):
        _reject()
