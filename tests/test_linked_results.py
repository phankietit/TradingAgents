"""Private linked writer mechanics; synthetic stop is not native/live proof."""

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import timedelta
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import SQLAlchemyError

from tests.test_continuation_consent import history, prepared as prepared
from tests.test_linked_execution import setup
from tests.test_linked_publication import assert_old_history_unchanged, raw_checkpoint
from tests.test_linked_recording import engine
from tradingagents.contracts import ArtifactKind, SnapshotManifest
from tradingagents.platform.analysis import AnalysisResult
from tradingagents.platform.analysis.linked_execution import LinkedExecutionError
from tradingagents.platform.analysis.linked_publication import LinkedPublicationContext
from tradingagents.platform.analysis.linked_recording import (
    LinkedOriginalResearch,
    consume_linked_dispatch,
)
from tradingagents.platform.analysis.linked_results import (
    LinkedResultPublisher,
    read_linked_completion,
)
from tradingagents.platform.analysis.stage_records import ResearchStageService
from tradingagents.platform.artifacts import ArtifactService, LocalArtifactStore
from tradingagents.platform.persistence import (
    PlatformRepository,
    downgrade_database,
    upgrade_database,
)
from tradingagents.platform.persistence.models import (
    ArtifactRow,
    DecisionRow,
    ResearchExecutionArtifactRow,
    ResearchExecutionCompletionRow,
)


def publisher_setup(prepared, tmp_path, *, store_override=None):
    database, executions, params, clock = setup(prepared)
    row = executions.allocate(**params)
    lease = executions.claim(execution_id=row.execution_id, worker_id="writer-fixture")
    blobs = store_override or LocalArtifactStore(tmp_path / "linked-blobs")
    publisher = LinkedResultPublisher(blobs)
    context = LinkedPublicationContext.prepare(executions, lease, observer_clock=lambda: (
        clock[0] - lease.started_at).total_seconds(), save_stage=publisher.save_stage)
    with database.session() as session:
        repository = PlatformRepository(session)
        run = repository.get_run(context.run_id, context.owner_id)
        artifacts = ArtifactService(blobs, repository)
        for role, ids in run.decision_inputs.snapshots_by_analyst.items():
            for identity in ids:
                if repository.get_snapshot(identity) is not None:
                    continue
                raw = json.dumps({"close": 100, "source_note": "SYNTHETIC WRITER FIXTURE"}).encode()
                manifest = SnapshotManifest(snapshot_id=identity, instrument_id=run.instrument_id,
                    dataset="daily_prices" if role == "market" else role, vendor="fixture",
                    as_of=run.analysis_as_of, retrieved_at=run.analysis_as_of, source_end=run.analysis_as_of,
                    content_hash="sha256:" + hashlib.sha256(raw).hexdigest(), quality_status="OK")
                repository.add_snapshot(manifest)
                artifacts.create(owner_id=context.owner_id, kind=ArtifactKind.SNAPSHOT_PAYLOAD,
                    media_type="application/json", content=raw, snapshot_id=identity,
                    instrument_id=run.instrument_id, created_at=run.analysis_as_of)
    loaded = LinkedOriginalResearch.load(context=context, artifact_store=blobs)
    publisher.bind(context, loaded)
    supervised = engine(context, loaded)
    result = AnalysisResult(instrument=loaded.request.instrument, analysis_date=loaded.request.analysis_date,
        selected_analysts=loaded.request.selected_analysts, profile_name="large_cap_equity",
        reference_only=False, final_state={"final_trade_decision": "SYNTHETIC LOCAL WRITER RESEARCH"},
        narrative_signal="Review", validation_issues=("structured_output_missing",))
    return database, executions, params, clock, publisher, context, loaded, supervised, result


@pytest.fixture
def published(prepared, tmp_path):
    return publisher_setup(prepared, tmp_path)


def stopped(published):
    _, executions, _, _, _, context, loaded, supervised, result = published
    consume_linked_dispatch(context=context, recording_inputs=loaded.recording_inputs,
        request=loaded.request, restore_checkpoint=loaded.restore_checkpoint)
    _, raw = raw_checkpoint(context, executions)
    context.commit_checkpoint(raw)
    # Unit-only fabricated supervisor fields/hook, not real process attestation.
    # Actual clean exit/reaping is tested by the native fixture matrix.
    context.observer._record_supervised_stop()
    supervised._linked_return_result = result
    supervised._linked_clean_exit = True


@pytest.mark.parametrize("prepared", [False,
    pytest.param("postgres_failed", marks=pytest.mark.integration)], indirect=True)
def test_atomic_original_report_candidate_receipt_and_history(published):
    database, _, _, _, publisher, context, loaded, supervised, result = published
    stopped(published)
    before = history(database)
    output = publisher.publish_completed(supervised, result, loaded.request)
    with database.session() as session:
        repository = PlatformRepository(session)
        receipt = session.get(ResearchExecutionCompletionRow, context.execution_id)
        assert output == (receipt.report_artifact_id,)  # Missing schema stays REVIEW.
        candidate = repository.get_decision(receipt.decision_id, context.owner_id)
        assert candidate.status.value == candidate.rating.value.lower() == "review"
        assert candidate.target_weight is None and candidate.requires_human_approval is True
        assert repository.get_run(context.run_id, context.owner_id).status.value == "failed"
        report = json.loads(ArtifactService(publisher.artifact_store, repository).read(output[0], context.owner_id)[1])
        assert report["linked_execution"]["original_run_unchanged"] is True
        assert report["validation_issues"] == ["structured_output_missing"]
        assert report["canonical_research"] is None and report["execution"]["usage"]["cost"] is None
        assert ArtifactService(publisher.artifact_store, repository).read(output[0], uuid4()) is None
        assert session.get(ResearchExecutionArtifactRow, output[0]).execution_id == context.execution_id
        read = read_linked_completion(session=session, artifact_store=publisher.artifact_store,
            owner_id=context.owner_id, execution_id=context.execution_id)
        assert read.report_artifact_id == output[0] and str(context.owner_id) not in repr(read)
    assert history(database) == before
    with pytest.raises(LinkedExecutionError):
        publisher.publish_completed(supervised, result, loaded.request)


def test_stage_reader_only_fields_actor_and_immutable_history(published):
    database, _, _, _, publisher, context, loaded, _, _ = published
    consume_linked_dispatch(context=context, recording_inputs=loaded.recording_inputs,
        request=loaded.request, restore_checkpoint=loaded.restore_checkpoint)
    before = history(database)
    identity = publisher.save_stage("Market Analyst", {"market_report": "Reader-owned research",
        "messages": ["PRIVATE_NEVER_ECHO"], "reasoning": "PRIVATE_NEVER_ECHO", "target_weight": .99})
    with database.session() as session:
        artifacts = ArtifactService(publisher.artifact_store, PlatformRepository(session))
        record = ResearchStageService(artifacts).read(identity, context.owner_id)
        assert record.sections == {"market_report": "Reader-owned research"}
        assert record.attempt == 2 and record.approval_eligible is False
        assert b"PRIVATE_NEVER_ECHO" not in artifacts.read(identity, context.owner_id)[1]
        assert session.get(ResearchExecutionArtifactRow, identity).execution_id == context.execution_id
    assert_old_history_unchanged(database, before)


def test_stage_cannot_write_before_dispatch_or_after_stop(published):
    database, _, _, _, publisher, _, _, _, _ = published
    before = history(database)
    with pytest.raises(LinkedExecutionError):
        publisher.save_stage("Market Analyst", {"market_report": "not dispatched"})
    assert history(database) == before
    stopped(published)
    with pytest.raises(LinkedExecutionError):
        publisher.save_stage("Market Analyst", {"market_report": "already stopped"})


@pytest.mark.parametrize("prepared", [False,
    pytest.param("postgres_failed", marks=pytest.mark.integration)], indirect=True)
def test_two_result_publishers_have_one_atomic_winner(published):
    database, _, _, _, publisher, context, loaded, supervised, result = published
    stopped(published)
    barrier = Barrier(2)

    def call(_):
        barrier.wait(timeout=5)
        try:
            publisher.publish_completed(supervised, result, loaded.request)
            return True
        except LinkedExecutionError:
            return False

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(call, range(2))) == [False, True]
    with database.session() as session:
        assert len(session.scalars(select(ResearchExecutionCompletionRow)).all()) == 1
        assert len(session.scalars(select(DecisionRow)).all()) == 1
        assert read_linked_completion(session=session, artifact_store=publisher.artifact_store,
            owner_id=context.owner_id, execution_id=context.execution_id) is not None


def test_expiry_during_final_flush_rolls_back_all_output_metadata(published, monkeypatch):
    from sqlalchemy.orm import Session

    database, _, _, clock, publisher, context, loaded, supervised, result = published
    stopped(published)
    flush = Session.flush

    def expire(session, *args, **kwargs):
        completing = any(type(row) is ResearchExecutionCompletionRow for row in session.new)
        returned = flush(session, *args, **kwargs)
        if completing:
            clock[0] = context._lease.expires_at
        return returned

    monkeypatch.setattr(Session, "flush", expire)
    with pytest.raises(LinkedExecutionError):
        publisher.publish_completed(supervised, result, loaded.request)
    with database.session() as session:
        assert session.get(ResearchExecutionCompletionRow, context.execution_id) is None
        assert session.scalar(select(DecisionRow)) is None
        assert session.scalar(select(ArtifactRow).where(ArtifactRow.kind == ArtifactKind.ANALYSIS_REPORT.value)) is None


@pytest.mark.parametrize("mutation", ["not_stopped", "unclean_exit", "result", "request", "expired", "cancel", "source_owner", "missing_actor", "missing_dispatch"])
def test_no_completion_from_uncertain_wrong_or_changed_context(published, mutation):
    database, executions, params, clock, publisher, context, loaded, supervised, result = published
    if mutation != "not_stopped":
        stopped(published)
    if mutation == "unclean_exit":
        supervised._linked_clean_exit = False
    elif mutation == "result":
        result = result.model_copy(update={"narrative_signal": "arbitrary replacement"})
    elif mutation == "request":
        loaded = type(loaded)(loaded.recording_inputs,
            loaded.request.model_copy(update={"analysis_date": loaded.request.analysis_date + timedelta(days=1)}), loaded.restore_checkpoint)
    elif mutation == "expired":
        clock[0] = context._lease.expires_at
    elif mutation == "cancel":
        executions.request_cancel(**params)
    elif mutation == "source_owner":
        with database.session() as session:
            session.scalar(select(ArtifactRow)).owner_id = uuid4()
    elif mutation in {"missing_actor", "missing_dispatch"}:
        from tradingagents.platform.persistence.models import (
            ResearchCheckpointExecutionRow,
            ResearchExecutionDispatchRow,
        )

        with database.session() as session:
            model = ResearchCheckpointExecutionRow if mutation == "missing_actor" else ResearchExecutionDispatchRow
            session.delete(session.scalar(select(model)))
    before = history(database)
    with pytest.raises(LinkedExecutionError):
        publisher.publish_completed(supervised, result, loaded.request)
    with database.session() as session:
        assert session.get(ResearchExecutionCompletionRow, context.execution_id) is None
        assert session.scalar(select(DecisionRow)) is None
        assert session.scalar(select(ArtifactRow).where(ArtifactRow.kind == ArtifactKind.ANALYSIS_REPORT.value)) is None
    assert history(database) == before


@pytest.mark.parametrize("committed", [False, True])
def test_finalization_fault_does_not_grant_reentry_or_partial_metadata(published, monkeypatch, committed):
    database, _, _, _, publisher, context, loaded, supervised, result = published
    stopped(published)
    original = context.publication_session

    @contextmanager
    def uncertain(**options):
        with original(**options) as session:
            yield session
            if not committed:
                raise SQLAlchemyError("PRIVATE_NEVER_ECHO")
        raise SQLAlchemyError("PRIVATE_NEVER_ECHO")

    monkeypatch.setattr(context, "publication_session", uncertain)
    with pytest.raises(LinkedExecutionError):
        publisher.publish_completed(supervised, result, loaded.request)
    monkeypatch.setattr(context, "publication_session", original)
    with database.session() as session:
        assert (session.get(ResearchExecutionCompletionRow, context.execution_id) is not None) is committed
        assert (session.scalar(select(DecisionRow)) is not None) is committed
        assert (session.scalar(select(ResearchExecutionArtifactRow)) is not None) is committed
    with pytest.raises(ValueError):
        supervised.analyze(loaded.request)
    if committed:
        with database.session() as session:
            assert read_linked_completion(session=session, artifact_store=publisher.artifact_store,
                owner_id=context.owner_id, execution_id=context.execution_id) is not None
        with pytest.raises(LinkedExecutionError):
            publisher.publish_completed(supervised, result, loaded.request)


@pytest.mark.parametrize("mutation", ["owner", "report_hash", "decision_hash", "report_column", "decision_payload", "actor", "stop", "checkpoint_fingerprint", "event_actor", "completed_at"])
def test_completion_reader_rejects_foreign_or_corrupt_receipts(published, mutation):
    database, _, _, _, publisher, context, loaded, supervised, result = published
    stopped(published)
    publisher.publish_completed(supervised, result, loaded.request)
    owner = context.owner_id
    with database.session() as session:
        receipt = session.get(ResearchExecutionCompletionRow, context.execution_id)
        if mutation == "owner":
            owner = uuid4()
        elif mutation == "report_hash":
            receipt.report_hash = "sha256:" + "c" * 64
        elif mutation == "decision_hash":
            receipt.decision_hash = "c" * 64
        elif mutation == "report_column":
            session.get(ArtifactRow, receipt.report_artifact_id).content_hash = "sha256:" + "c" * 64
        elif mutation == "decision_payload":
            row = session.get(DecisionRow, receipt.decision_id)
            row.payload = {**row.payload, "thesis": "corrupted candidate"}
        elif mutation == "actor":
            session.delete(session.get(ResearchExecutionArtifactRow, receipt.report_artifact_id))
        elif mutation == "stop":
            from tradingagents.platform.persistence.models import RunEventRow

            event = session.scalars(select(RunEventRow).order_by(RunEventRow.sequence.desc())).first()
            event.payload = {key: value for key, value in event.payload.items() if key != "execution_stopped"}
        elif mutation == "checkpoint_fingerprint":
            from tradingagents.platform.persistence.models import ResearchCheckpointRow

            session.get(ResearchCheckpointRow, receipt.checkpoint_record_id).fingerprint = "b" * 64
        elif mutation == "event_actor":
            from tradingagents.platform.persistence.models import ResearchExecutionEventRow

            session.delete(session.scalars(select(ResearchExecutionEventRow).order_by(ResearchExecutionEventRow.event_id)).first())
        elif mutation == "completed_at":
            receipt.completed_at = context._lease.deadline_at
    with database.session() as session, pytest.raises(LinkedExecutionError):
        read_linked_completion(session=session, artifact_store=publisher.artifact_store,
            owner_id=owner, execution_id=context.execution_id)


def test_expired_lease_does_not_hide_verified_archived_output(published):
    database, executions, params, clock, publisher, context, loaded, supervised, result = published
    stopped(published)
    publisher.publish_completed(supervised, result, loaded.request)
    with pytest.raises(LinkedExecutionError):
        context.heartbeat()
    with pytest.raises(LinkedExecutionError):
        executions.request_cancel(**params)
    with pytest.raises(LinkedExecutionError):
        context.commit_checkpoint(loaded.restore_checkpoint)
    clock[0] = context._lease.deadline_at + timedelta(days=1)
    assert executions.mark_expired_for_review(execution_id=context.execution_id).status == "leased"
    with database.session() as session:
        assert read_linked_completion(session=session, artifact_store=publisher.artifact_store,
            owner_id=context.owner_id, execution_id=context.execution_id) is not None


def test_existing_real_portfolio_policy_risk_pipeline_is_not_cut(tmp_path, monkeypatch):
    from tests.test_continuation_consent import _prepared
    from tests.test_recovery_fingerprint import inputs
    from tests.test_risk_provenance import setup_risk
    from tradingagents.platform.analysis.decisions import StructuredDecisionNarrative

    database, blobs, seeded = setup_risk(tmp_path)
    with database.session() as session:
        repository = PlatformRepository(session)
        instrument = repository.get_instrument(seeded.instrument_id)
        source = seeded.risk_snapshot_ids[0]
    args = inputs()
    run = args["run"].model_copy(update={"owner_id": seeded.owner_id, "instrument_id": seeded.instrument_id,
        "selected_analysts": ("market",), "snapshot_ids": seeded.risk_snapshot_ids,
        "decision_inputs": {"snapshots_by_analyst": {"market": (source,)},
            "source_max_age_seconds": {"market": 86400}, "portfolio_snapshot_id": seeded.portfolio_snapshot_id,
            "policy_id": seeded.policy_checks[0].policy_id, "policy_version": seeded.policy_checks[0].policy_version,
            "requested_target_weight": .3, "risk_snapshot_ids": seeded.risk_snapshot_ids}})
    args.update(owner_id=seeded.owner_id, run=type(run).model_validate(run.model_dump()),
        request=args["request"].model_copy(update={"instrument": instrument}))
    monkeypatch.setattr("tests.test_continuation_consent.inputs", lambda: args)
    url = database.engine.url.render_as_string(hide_password=False)
    database.dispose()
    fixture = _prepared(url, cancelled=False)
    try:
        prepared = next(fixture)
        values = publisher_setup(prepared, tmp_path, store_override=blobs)
        database, _, _, _, publisher, context, loaded, supervised, result = values
        narrative = StructuredDecisionNarrative(rating="Buy", confidence=.7, thesis="Thesis",
            risks=("Risk",), invalidation_conditions=("Invalidation",))
        result = result.model_copy(update={"decision_payload": narrative, "material_claims": dict.fromkeys(("Thesis", "Risk", "Invalidation"), (source,)), "validation_issues": ()})
        values = (*values[:-1], result)
        stopped(values)
        publisher.publish_completed(supervised, result, loaded.request)
        with database.session() as session:
            read = read_linked_completion(session=session, artifact_store=blobs,
                owner_id=context.owner_id, execution_id=context.execution_id)
            candidate = PlatformRepository(session, artifact_store=blobs).get_decision(read.decision_id, context.owner_id)
            assert candidate.status.value == "ready_for_approval" and candidate.target_weight == .3
            assert candidate.current_weight == .2 and candidate.policy_checks == seeded.policy_checks
            assert len(candidate.evidence) == 3 and candidate.requires_human_approval is True
            # Existing root-success authority is deliberately NOT bypassed here.
            # Integrating verified linked completion with approval is a later gate.
            from tests.test_decision_lifecycle import _approval

            with pytest.raises(ValueError, match="successfully completed"):
                PlatformRepository(session, artifact_store=blobs).add_decision_event(_approval(candidate))
    finally:
        fixture.close()


def test_disposable_empty_completion_migration_preserves_history(published):
    database, _, _, _, _, _, _, _, _ = published
    before = history(database)
    url = database.engine.url.render_as_string(hide_password=False)
    downgrade_database(url, "0015_linked_dispatch")
    assert "research_execution_completions" not in inspect(database.engine).get_table_names()
    upgrade_database(url)
    assert "research_execution_completions" in inspect(database.engine).get_table_names()
    assert history(database) == before
