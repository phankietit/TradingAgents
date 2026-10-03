"""Reload immutable terminal original inputs under linked parent authority.

Default routes stay disabled. This is not a model call, final result, human
approval or a portable bearer grant. Private original history is never edited.
"""

import hashlib
import re
from dataclasses import dataclass

from sqlalchemy import select

from tradingagents.contracts import ArtifactKind
from tradingagents.platform.artifacts import ArtifactIntegrityError, ArtifactService
from tradingagents.platform.jobs.decision_pipeline import load_run_portfolio
from tradingagents.platform.persistence import PlatformRepository
from tradingagents.platform.persistence.models import (
    ArtifactRow,
    DecisionRow,
    ResearchCheckpointRow,
    ResearchExecutionDispatchRow,
    SnapshotRow,
)

from .allowance import validate_retained_observer
from .checkpoint_store import PrivateCheckpointStore
from .continuation import _canonical, _db_utc, _digest
from .engine import AnalysisRequest
from .linked_execution import _reject
from .linked_publication import LinkedPublicationContext
from .recording_context import LinkedSnapshotRecordingInputs
from .snapshots import AnalysisSnapshot, load_snapshot_context


@dataclass(frozen=True, repr=False)
class _SourceBinding:
    recording_hash: str
    request_hash: str
    checkpoint_hash: str
    sources_hash: str
    artifact_store: object


def _artifact_columns(session, artifact):
    row = session.get(ArtifactRow, artifact.artifact_id)
    if (row is None or any(getattr(row, key) != getattr(artifact, key) for key in (
            "owner_id", "run_id", "instrument_id", "snapshot_id", "content_hash",
            "byte_size", "storage_key", "media_type")) or row.kind != artifact.kind.value
            or _db_utc(row.created_at) != artifact.created_at):
        _reject()


def _snapshot_columns(session, manifest):
    row = session.get(SnapshotRow, manifest.snapshot_id)
    if (row is None or any(getattr(row, key) != getattr(manifest, key) for key in (
            "instrument_id", "schema_version", "dataset", "vendor", "content_hash"))
            or row.quality_status != manifest.quality_status.value
            or _db_utc(row.as_of) != manifest.as_of or _db_utc(row.retrieved_at) != manifest.retrieved_at):
        _reject()


def _owned_sources(session, context, artifact_store, run):
    repository = PlatformRepository(session)
    artifacts = ArtifactService(artifact_store, repository)
    try:
        for identities in run.decision_inputs.snapshots_by_analyst.values():
            for identity in identities:
                artifact = repository.get_snapshot_artifact(identity, context.owner_id)
                manifest = repository.get_snapshot(identity)
                if artifact is None or manifest is None:
                    _reject()
                _artifact_columns(session, artifact)
                _snapshot_columns(session, manifest)
        return load_snapshot_context(artifacts, run, run.decision_inputs.snapshots_by_analyst)
    except (ArtifactIntegrityError, OSError, UnicodeError):
        _reject()


def _source(context, session):
    context._observer()
    consent, observation, _ = context._store._source(session, context.execution_id, context.clock())
    run = PlatformRepository(session).get_run(context.run_id, context.owner_id)
    # Final output appearing after consent is not permission to replay models.
    if (run is None or session.scalar(select(DecisionRow.decision_id).where(
            DecisionRow.run_id == context.run_id).limit(1)) is not None
            or session.scalar(select(ArtifactRow.artifact_id).where(ArtifactRow.run_id == context.run_id,
                ArtifactRow.kind == ArtifactKind.ANALYSIS_REPORT.value).limit(1)) is not None
            or (run.error_message is not None and re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,127}", run.error_message) is None)):
        _reject()  # Never clear original error text to make it transferable.
    checkpoint = session.scalar(select(ResearchCheckpointRow).where(
        ResearchCheckpointRow.run_id == context.run_id).order_by(ResearchCheckpointRow.sequence.desc()).limit(1))
    if (checkpoint is None or checkpoint.record_id != consent.checkpoint_record_id
            or checkpoint.owner_id != context.owner_id or checkpoint.job_id != context.job_id
            or checkpoint.attempt != observation["source_attempt"]
            or checkpoint.content_hash != observation["checkpoint_content_hash"]
            or checkpoint.fingerprint != context._store.consents.codec.fingerprint):
        _reject()
    PrivateCheckpointStore(codec=context._store.consents.codec).load_latest(
        session=session, owner_id=context.owner_id, run_id=context.run_id)
    return consent, observation, run, checkpoint


@dataclass(frozen=True, repr=False)
class LinkedOriginalResearch:
    recording_inputs: LinkedSnapshotRecordingInputs
    request: AnalysisRequest
    restore_checkpoint: bytes

    @classmethod
    def load(cls, *, context, artifact_store):
        if type(context) is not LinkedPublicationContext:
            _reject()
        try:
            with context.publication_session() as session:
                consent, observation, run, checkpoint = _source(context, session)
                repository = PlatformRepository(session)
                artifacts = ArtifactService(artifact_store, repository)
                declared = run.decision_inputs
                sources = _owned_sources(session, context, artifact_store, run)
                instrument = repository.get_instrument(run.instrument_id)
                if instrument is None:
                    _reject()
                book = policy = None
                if declared.portfolio_snapshot_id is not None:
                    book = repository.get_portfolio_snapshot(declared.portfolio_snapshot_id, run.owner_id)
                    policy = repository.get_policy(declared.policy_id, declared.policy_version, run.owner_id)
                    if book is None or policy is None:
                        _reject()
                risk = []
                for identity in declared.risk_snapshot_ids:
                    manifest = repository.get_snapshot(identity)
                    artifact = repository.get_snapshot_artifact(identity, run.owner_id)
                    if (manifest is None or artifact is None or artifact.content_hash != manifest.content_hash
                            or artifact.instrument_id != manifest.instrument_id):
                        _reject()
                    _artifact_columns(session, artifact)
                    _snapshot_columns(session, manifest)
                    loaded = artifacts.read(artifact.artifact_id, run.owner_id)
                    if loaded is None:
                        _reject()
                    risk.append(AnalysisSnapshot(manifest=manifest, payload=loaded[1].decode("utf-8")))
                overrides = {"llm_provider": run.llm_provider, "quick_think_llm": run.quick_model,
                    "deep_think_llm": run.deep_model}
                if run.report_language is not None:
                    overrides["output_language"] = {"en": "English", "vi": "Vietnamese",
                        "en-vi": "English and Vietnamese"}[run.report_language]
                request = AnalysisRequest(instrument=instrument, analysis_date=run.analysis_as_of.date(),
                    selected_analysts=run.selected_analysts, snapshot_context=sources,
                    portfolio=load_run_portfolio(repository, run), config_overrides=overrides,
                    execution_observer=context.observer)
                recording = LinkedSnapshotRecordingInputs.create(format="linked-snapshot-recording-v1",
                    owner_id=run.owner_id, run=run, expected_fingerprint=checkpoint.fingerprint,
                    portfolio_snapshot=book, policy=policy, risk_snapshots=tuple(risk),
                    execution_id=context.execution_id, source_job_id=context.job_id,
                    source_job_hash=observation["source_job_hash"], source_run_hash=observation["source_run_hash"],
                    observation_hash=consent.observation_hash, attempt=context._lease.reservation.attempt,
                    checkpoint_record_id=checkpoint.record_id, checkpoint_hash=checkpoint.content_hash)
                recording.validate_request(request)
                result = cls(recording, request, checkpoint.payload)
                binding = _SourceBinding(hashlib.sha256(recording.raw).hexdigest(),
                    _digest(request.model_dump(mode="json")), checkpoint.content_hash,
                    _digest(sources.model_dump(mode="json")), artifact_store)
            context._linked_source_binding = binding
            return result
        except (ValueError, TypeError, AttributeError, KeyError, OSError, UnicodeError, ArtifactIntegrityError):
            _reject()


def validate_linked_recording(*, context, recording_inputs, request=None, restore_checkpoint):
    """Parent-only source reload; no lifecycle projection or fresh observer."""
    if type(context) is not LinkedPublicationContext or type(recording_inputs) is not LinkedSnapshotRecordingInputs:
        _reject()
    with context.publication_session() as session:
        return _validate(session, context, recording_inputs, request, restore_checkpoint)


def _validate(session, context, recording_inputs, request, restore_checkpoint):
    binding = getattr(context, "_linked_source_binding", None)
    if (type(binding) is not _SourceBinding or hashlib.sha256(recording_inputs.raw).hexdigest() != binding.recording_hash
            or request is not None and _digest(request.model_dump(mode="json")) != binding.request_hash):
        _reject()
    value = recording_inputs.read() if request is None else recording_inputs.validate_request(request)
    consent, observation, run, checkpoint = _source(context, session)
    validate_retained_observer(observer=context.observer, run=run)
    if (request is not None and request.execution_observer is not context.observer
            or type(restore_checkpoint) is not bytes or restore_checkpoint != checkpoint.payload
            or hashlib.sha256(restore_checkpoint).hexdigest() != value.checkpoint_hash
            or binding.checkpoint_hash != value.checkpoint_hash
            or _canonical(value.run.model_dump(mode="json")) != _canonical(run.model_dump(mode="json"))
            or (value.execution_id, value.source_job_id, value.source_job_hash, value.source_run_hash,
                value.observation_hash, value.attempt, value.checkpoint_record_id, value.checkpoint_hash,
                value.expected_fingerprint) != (context.execution_id, context.job_id,
                    observation["source_job_hash"], observation["source_run_hash"], consent.observation_hash,
                    context._lease.reservation.attempt, checkpoint.record_id, checkpoint.content_hash, checkpoint.fingerprint)):
        _reject()
    # Explicit book/policy bytes must still match owner-readable immutable rows.
    repository = PlatformRepository(session)
    declared = run.decision_inputs
    sources = _owned_sources(session, context, binding.artifact_store, run)
    if _digest(sources.model_dump(mode="json")) != binding.sources_hash:
        _reject()
    for source in value.risk_snapshots:
        manifest = repository.get_snapshot(source.manifest.snapshot_id)
        artifact = repository.get_snapshot_artifact(source.manifest.snapshot_id, context.owner_id)
        if manifest is None or artifact is None:
            _reject()
        _snapshot_columns(session, manifest)
        _artifact_columns(session, artifact)
        try:
            loaded = ArtifactService(binding.artifact_store, repository).read(artifact.artifact_id, context.owner_id)
            if loaded is None or _digest(AnalysisSnapshot(manifest=manifest, payload=loaded[1].decode()).model_dump(mode="json")) != _digest(source.model_dump(mode="json")):
                _reject()
        except (ArtifactIntegrityError, OSError, UnicodeError):
            _reject()
    if declared.portfolio_snapshot_id is not None:
        book = repository.get_portfolio_snapshot(declared.portfolio_snapshot_id, context.owner_id)
        policy = repository.get_policy(declared.policy_id, declared.policy_version, context.owner_id)
        if (book is None or policy is None or _digest(book.model_dump(mode="json")) != _digest(value.portfolio_snapshot.model_dump(mode="json"))
                or _digest(policy.model_dump(mode="json")) != _digest(value.policy.model_dump(mode="json"))):
            _reject()
    return value


def consume_linked_dispatch(*, context, recording_inputs, request, restore_checkpoint):
    """Single-use durable boundary before Process construction/start, ACK last.

    A lost committed ACK leaves uncertainty; neither same nor new parent may
    respawn it. This records consumption, not a successful child/provider call.
    """
    if (type(context) is not LinkedPublicationContext or type(recording_inputs) is not LinkedSnapshotRecordingInputs
            or type(request) is not AnalysisRequest):
        _reject()
    with context.publication_session() as session:
        value = _validate(session, context, recording_inputs, request, restore_checkpoint)
        if session.get(ResearchExecutionDispatchRow, context.execution_id) is not None:
            _reject()
        session.add(ResearchExecutionDispatchRow(execution_id=context.execution_id,
            checkpoint_record_id=value.checkpoint_record_id, checkpoint_hash=value.checkpoint_hash,
            created_at=context.clock()))
        session.flush()
