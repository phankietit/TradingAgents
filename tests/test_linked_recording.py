"""Owner-readable terminal context and single-use dispatch, no provider call."""

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import replace
from datetime import timedelta
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import SQLAlchemyError

from tests.test_continuation_consent import history, prepared as prepared
from tests.test_linked_execution import setup
from tradingagents.contracts import ArtifactKind, SnapshotManifest
from tradingagents.platform.analysis.linked_execution import LinkedExecutionError
from tradingagents.platform.analysis.linked_publication import LinkedPublicationContext
from tradingagents.platform.analysis.linked_recording import (
    LinkedOriginalResearch,
    consume_linked_dispatch,
)
from tradingagents.platform.analysis.recording_context import (
    LinkedSnapshotRecordingInputs,
    SnapshotRecordingInputs,
    read_child_recording_inputs,
)
from tradingagents.platform.analysis.recovery_fingerprint import RecoveryFingerprintError
from tradingagents.platform.analysis.supervision import SupervisedAnalysisEngine
from tradingagents.platform.artifacts import ArtifactService, LocalArtifactStore
from tradingagents.platform.persistence import (
    PlatformRepository,
    downgrade_database,
    upgrade_database,
)
from tradingagents.platform.persistence.models import (
    ArtifactRow,
    ResearchExecutionDispatchRow,
    SnapshotRow,
)


@pytest.fixture
def linked(prepared, tmp_path):
    database, store, params, clock = setup(prepared)
    row = store.allocate(**params)
    lease = store.claim(execution_id=row.execution_id, worker_id="fixture")
    context = LinkedPublicationContext.prepare(store, lease, observer_clock=lambda: 0)
    blobs = LocalArtifactStore(tmp_path / "source-blobs")
    with database.session() as session:
        repository = PlatformRepository(session)
        run = repository.get_run(context.run_id, context.owner_id)
        artifacts = ArtifactService(blobs, repository)
        for role, ids in run.decision_inputs.snapshots_by_analyst.items():
            for identity in ids:
                raw = json.dumps({"close": 100, "source_note": "synthetic immutable fixture"}).encode()
                manifest = SnapshotManifest(snapshot_id=identity, instrument_id=run.instrument_id,
                    dataset="daily_prices" if role == "market" else role, vendor="fixture",
                    as_of=run.analysis_as_of, retrieved_at=run.analysis_as_of, source_end=run.analysis_as_of,
                    content_hash="sha256:" + hashlib.sha256(raw).hexdigest(), quality_status="OK")
                repository.add_snapshot(manifest)
                artifacts.create(owner_id=context.owner_id, kind=ArtifactKind.SNAPSHOT_PAYLOAD,
                    media_type="application/json", content=raw, snapshot_id=identity,
                    instrument_id=run.instrument_id, created_at=run.analysis_as_of)
    return database, store, params, clock, context, blobs


def engine(context, loaded, **changes):
    values = {"recording_inputs": loaded.recording_inputs, "restore_checkpoint": loaded.restore_checkpoint,
        "checkpoint_codec": context._store.consents.codec, "checkpoint_thread_id": str(context.run_id),
        "checkpoint_commit": context.commit_checkpoint, "linked_context": context}
    values.update(changes)
    return SupervisedAnalysisEngine(**values)


def consume(context, loaded):
    return consume_linked_dispatch(context=context, recording_inputs=loaded.recording_inputs,
        request=loaded.request, restore_checkpoint=loaded.restore_checkpoint)


def test_terminal_original_loader_preserves_every_field_and_has_no_authority_bytes(linked):
    database, _, params, _, context, blobs = linked
    before = history(database)
    loaded = LinkedOriginalResearch.load(context=context, artifact_store=blobs)
    value = loaded.recording_inputs.read()
    with database.session() as session:
        original = PlatformRepository(session).get_run(context.run_id, context.owner_id)
    assert value.run.model_dump() == original.model_dump() and value.run.completed_at is not None
    assert value.run.error_code == "RESEARCH_EXECUTION_FAILED"
    assert value.attempt == 2 and loaded.request.execution_observer is context.observer
    assert all(secret not in loaded.recording_inputs.raw.decode() for secret in (
        params["session_token"], params["csrf_token"], str(context._lease.token)))
    assert str(context.owner_id) not in repr(loaded) + repr(loaded.recording_inputs) + repr(value)
    with pytest.raises(RecoveryFingerprintError):
        SnapshotRecordingInputs(loaded.recording_inputs.raw).read()
    with pytest.raises(RecoveryFingerprintError):
        SnapshotRecordingInputs.create(owner_id=value.owner_id, run=value.run,
            expected_fingerprint=value.expected_fingerprint)
    assert history(database) == before


@pytest.mark.parametrize("mutation", ["owner", "missing", "changed_source", "snapshot_column", "nonce", "expired"])
def test_loader_refuses_missing_foreign_or_changed_inputs_without_history_edits(linked, mutation):
    database, _, _, clock, context, blobs = linked
    if mutation in {"owner", "missing"}:
        with database.session() as session:
            row = session.scalar(select(ArtifactRow).where(ArtifactRow.kind == ArtifactKind.SNAPSHOT_PAYLOAD.value))
            if mutation == "owner":
                row.owner_id = uuid4()
            else:
                session.delete(row)
    elif mutation == "changed_source":
        # Stored blob integrity fails; never replace it with current/live data.
        with database.session() as session:
            row = session.scalar(select(ArtifactRow).where(ArtifactRow.kind == ArtifactKind.SNAPSHOT_PAYLOAD.value))
            row.content_hash = "sha256:" + "c" * 64
    elif mutation == "nonce":
        context._lease = replace(context._lease, token=uuid4())
    elif mutation == "snapshot_column":
        with database.session() as session:
            session.scalar(select(SnapshotRow)).content_hash = "sha256:" + "c" * 64
    else:
        clock[0] = context._lease.expires_at
    before = history(database)
    with pytest.raises(LinkedExecutionError):
        LinkedOriginalResearch.load(context=context, artifact_store=blobs)
    assert history(database) == before


@pytest.mark.parametrize("mutation", ["context", "restore", "commit", "codec", "ordinary_context"])
def test_parent_requires_exact_linked_context_restore_and_fenced_callback(linked, mutation):
    _, _, _, _, context, blobs = linked
    loaded = LinkedOriginalResearch.load(context=context, artifact_store=blobs)
    values = {"context": {"linked_context": None}, "restore": {"restore_checkpoint": None},
        "commit": {"checkpoint_commit": lambda raw: None}, "codec": {"checkpoint_codec": None},
        "ordinary_context": {"recording_inputs": SnapshotRecordingInputs(loaded.recording_inputs.raw)}}
    with pytest.raises(ValueError, match="^invalid checkpoint bridge configuration$"):
        engine(context, loaded, **values[mutation])


@pytest.mark.parametrize("mutation", ["format", "run_hash", "job_hash", "bool_attempt", "raw_error", "extra"])
def test_mutated_wire_cannot_become_linked_parent_permission(linked, mutation):
    _, _, _, _, context, blobs = linked
    loaded = LinkedOriginalResearch.load(context=context, artifact_store=blobs)
    data = json.loads(loaded.recording_inputs.raw)
    if mutation == "format":
        data["format"] = "ordinary"
    elif mutation == "run_hash":
        data["source_run_hash"] = "b" * 64
    elif mutation == "job_hash":
        data["source_job_hash"] = "b" * 64
    elif mutation == "bool_attempt":
        data["attempt"] = True
    elif mutation == "raw_error":
        data["run"]["error_message"] = "PRIVATE_NEVER_ECHO"
    else:
        data["credentials"] = "PRIVATE_NEVER_ECHO"
    changed = replace(loaded, recording_inputs=LinkedSnapshotRecordingInputs(json.dumps(data).encode()))
    with pytest.raises(ValueError, match="^invalid checkpoint bridge configuration$"):
        engine(context, changed)


@pytest.mark.parametrize("prepared", [False,
    pytest.param("postgres_failed", marks=pytest.mark.integration)], indirect=True)
def test_dispatch_consumption_is_single_use_and_old_history_unchanged(linked):
    database, _, _, _, context, blobs = linked
    loaded = LinkedOriginalResearch.load(context=context, artifact_store=blobs)
    before = history(database)
    assert consume(context, loaded) is None
    with pytest.raises(LinkedExecutionError):
        consume(context, loaded)
    with database.session() as session:
        row = session.get(ResearchExecutionDispatchRow, context.execution_id)
        assert row.checkpoint_hash == loaded.recording_inputs.read().checkpoint_hash
        assert len(session.scalars(select(ResearchExecutionDispatchRow)).all()) == 1
    assert history(database) == before


@pytest.mark.parametrize("prepared", [False,
    pytest.param("postgres_failed", marks=pytest.mark.integration)], indirect=True)
def test_two_parent_dispatch_consumers_have_one_winner(linked):
    database, _, _, _, context, blobs = linked
    loaded = LinkedOriginalResearch.load(context=context, artifact_store=blobs)
    before = history(database)
    barrier = Barrier(2)

    def call(_):
        barrier.wait(timeout=5)
        try:
            consume(context, loaded)
            return True
        except LinkedExecutionError:
            return False

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(call, range(2))) == [False, True]
    with database.session() as session:
        assert len(session.scalars(select(ResearchExecutionDispatchRow)).all()) == 1
    assert history(database) == before


def test_sources_reloaded_again_before_dispatch_not_just_initial_load(linked):
    database, _, _, _, context, blobs = linked
    loaded = LinkedOriginalResearch.load(context=context, artifact_store=blobs)
    with database.session() as session:
        session.scalar(select(ArtifactRow)).owner_id = uuid4()
    with pytest.raises(LinkedExecutionError):
        consume(context, loaded)
    with database.session() as session:
        assert session.get(ResearchExecutionDispatchRow, context.execution_id) is None


@pytest.mark.parametrize("committed", [False, True])
def test_failed_or_lost_dispatch_ack_never_spawns_or_respawns(linked, monkeypatch, committed):
    database, _, _, _, context, blobs = linked
    loaded = LinkedOriginalResearch.load(context=context, artifact_store=blobs)
    supervised = engine(context, loaded)
    original = context.publication_session

    @contextmanager
    def uncertain(**options):
        consumed = False
        with original(**options) as session:
            yield session
            consumed = session.get(ResearchExecutionDispatchRow, context.execution_id) is not None
            if consumed and not committed:
                raise SQLAlchemyError("PRIVATE_NEVER_ECHO")
        if consumed and committed:
            raise SQLAlchemyError("PRIVATE_NEVER_ECHO")

    def forbidden(*args, **kwargs):
        raise AssertionError("uncertain dispatch constructed a process")

    monkeypatch.setattr("tradingagents.platform.analysis.supervision.get_context", forbidden)
    monkeypatch.setattr(context, "publication_session", uncertain)
    with pytest.raises((LinkedExecutionError, SQLAlchemyError)):
        supervised.analyze(loaded.request)
    monkeypatch.setattr(context, "publication_session", original)
    with database.session() as session:
        assert len(session.scalars(select(ResearchExecutionDispatchRow)).all()) == int(committed)
    if committed:
        with pytest.raises(LinkedExecutionError):
            supervised.analyze(loaded.request)
    assert context.observer.started_calls == 0


@pytest.mark.parametrize("mutation", ["request", "context", "restore", "callback", "expiry"])
def test_mutable_setup_rechecked_before_process_creation(linked, monkeypatch, mutation):
    database, _, _, clock, context, blobs = linked
    loaded = LinkedOriginalResearch.load(context=context, artifact_store=blobs)
    supervised = engine(context, loaded)
    request = loaded.request
    if mutation == "request":
        request = request.model_copy(update={"analysis_date": request.analysis_date + timedelta(days=1)})
    elif mutation == "context":
        supervised.linked_context = None
    elif mutation == "restore":
        supervised.restore_checkpoint = None
    elif mutation == "callback":
        supervised.checkpoint_commit = lambda raw: None
    else:
        clock[0] = context._lease.expires_at

    def forbidden(*args, **kwargs):
        raise AssertionError("invalid setup constructed a child")

    monkeypatch.setattr("tradingagents.platform.analysis.supervision.get_context", forbidden)
    with pytest.raises(ValueError):
        supervised.analyze(request)
    with database.session() as session:
        assert session.get(ResearchExecutionDispatchRow, context.execution_id) is None


def test_linked_child_transport_requires_explicit_restore_and_matching_execution(linked):
    _, _, _, _, context, blobs = linked
    loaded = LinkedOriginalResearch.load(context=context, artifact_store=blobs)
    for options, raw in (({"fingerprint": "a" * 64}, loaded.restore_checkpoint),
        ({"linked_execution_id": str(context.execution_id)}, None),
        ({"linked_execution_id": str(uuid4())}, loaded.restore_checkpoint)):
        with pytest.raises(RecoveryFingerprintError):
            read_child_recording_inputs(loaded.recording_inputs.raw, checkpoint_options=options,
                restore_checkpoint=raw).read()


def test_disposable_empty_dispatch_schema_roundtrip_preserves_evidence(linked):
    database, _, _, _, _, _ = linked
    before = history(database)
    url = database.engine.url.render_as_string(hide_password=False)
    downgrade_database(url, "0014_linked_publication")
    assert "research_execution_dispatches" not in inspect(database.engine).get_table_names()
    upgrade_database(url)
    assert "research_execution_dispatches" in inspect(database.engine).get_table_names()
    assert history(database) == before
