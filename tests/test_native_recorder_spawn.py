"""Exact production child/engine/recorder/native graph with synthetic SDK responses."""

import asyncio
import json
import os
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import select

from tests.test_durable_jobs import _database, _enqueue
from tests.test_risk_engine import NOW
from tests.test_snapshot_analysis import context
from tests.test_supervised_native_graph import NativeFixtureEngine
from tradingagents.contracts import ArtifactKind, RunEventType
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.platform.analysis import AnalysisEngine, AnalysisRequest
from tradingagents.platform.analysis.accounting import load_accounting_evidence
from tradingagents.platform.analysis.allowance import (
    build_retained_observer,
    load_remaining_allowance,
)
from tradingagents.platform.analysis.checkpoint_codec import SnapshotCheckpointCodec
from tradingagents.platform.analysis.checkpoint_store import (
    CheckpointDatabaseError,
    PrivateCheckpointStore,
)
from tradingagents.platform.analysis.client_binding import build_initialized_graph_fingerprint
from tradingagents.platform.analysis.continuation import ContinuationConsentStore
from tradingagents.platform.analysis.linked_execution import LinkedExecutionStore
from tradingagents.platform.analysis.linked_publication import LinkedPublicationContext
from tradingagents.platform.analysis.linked_recording import LinkedOriginalResearch
from tradingagents.platform.analysis.observer import (
    STAGES,
    ResearchBudgetExceeded,
    ResearchExecutionFailed,
    ResearchObserver,
)
from tradingagents.platform.analysis.recording import SnapshotRecorder
from tradingagents.platform.analysis.recording_context import (
    SnapshotRecordingInputs,
    read_child_recording_inputs,
)
from tradingagents.platform.analysis.snapshots import AnalysisSnapshot
from tradingagents.platform.analysis.supervision import (
    RESULT_FIELDS,
    SupervisedAnalysisEngine,
    _child as original_child,
)
from tradingagents.platform.artifacts import ArtifactService, LocalArtifactStore
from tradingagents.platform.auth import OwnerAuth
from tradingagents.platform.events import RunEventStore
from tradingagents.platform.jobs import DurableJobQueue, JobWorker
from tradingagents.platform.jobs.worker import JobExecutionContext
from tradingagents.platform.persistence import PlatformRepository
from tradingagents.platform.persistence.models import (
    ResearchCheckpointExecutionRow,
    ResearchCheckpointRow,
    ResearchExecutionDispatchRow,
)


def fixture_child(connection, base_config, request_data, engine_factory, checkpoint_options, recording_data,
                  *, invalid=False, callbacks=False, restore_checkpoint=None):
    """Only install synthetic SDK responses; do not replace engine or graph hooks."""
    assert engine_factory is AnalysisEngine
    os.environ["OPENAI_API_KEY"] = "synthetic-NEVER_ECHO"
    inputs = read_child_recording_inputs(recording_data, checkpoint_options=checkpoint_options,
        restore_checkpoint=restore_checkpoint).read()
    request = AnalysisRequest.model_validate(request_data)
    fixture = NativeFixtureEngine(base_config={**base_config, "_fixture_invalid_translation": invalid,
                                              "_fixture_callbacks": callbacks})
    # Test-owned synthetic prompts only, outside Git. Prefix survives a real
    # supervisor termination; unknown SDK cleanup must not be called closed.
    fixture.trace_sink = lambda trace: Path(base_config["results_dir"] + ".fixture-trace.json").write_text(
        json.dumps({"pid": os.getpid(), "trace": trace, "closed_clients": None}), encoding="utf-8")
    # Enable reviewed actual SDK construction in the reusable fixture. This
    # sentinel is never used by production child, which builds its own recorder.
    fixture.snapshot_recorder = SnapshotRecorder(owner_id=inputs.owner_id, run=inputs.run,
        expected_fingerprint=inputs.expected_fingerprint, commit=lambda raw: None)

    def forbidden(*args, **kwargs):
        raise AssertionError("native-spawn fixture attempted network/provider invocation")

    with patch.object(httpx.Client, "send", forbidden), patch.object(httpx.AsyncClient, "send", forbidden):
        fixture.analyze(request, fixture_execution=lambda config: original_child(
            connection, config, request_data, engine_factory, checkpoint_options, recording_data, restore_checkpoint))
    assert len(fixture.initialized_clients) == 2
    assert all(llm.root_client.is_closed() and llm.root_async_client.is_closed()
               for llm in fixture.initialized_clients)
    Path(base_config["results_dir"] + ".fixture-trace.json").write_text(json.dumps({
        "pid": os.getpid(), "trace": fixture.model_trace, "closed_clients": 2}), encoding="utf-8")


def invalid_fixture_child(connection, base_config, request_data, engine_factory, checkpoint_options, recording_data):
    fixture_child(connection, base_config, request_data, engine_factory, checkpoint_options, recording_data,
                  invalid=True)


def callback_fixture_child(connection, base_config, request_data, engine_factory, checkpoint_options, recording_data):
    fixture_child(connection, base_config, request_data, engine_factory, checkpoint_options, recording_data,
                  callbacks=True)


def invalid_callback_fixture_child(connection, base_config, request_data, engine_factory, checkpoint_options, recording_data):
    fixture_child(connection, base_config, request_data, engine_factory, checkpoint_options, recording_data,
                  callbacks=True, invalid=True)


def restored_callback_fixture_child(connection, base_config, request_data, engine_factory,
                                    checkpoint_options, recording_data, restore_checkpoint):
    fixture_child(connection, base_config, request_data, engine_factory, checkpoint_options, recording_data,
                  callbacks=True, restore_checkpoint=restore_checkpoint,
                  invalid=base_config["_fixture_restore_invalid"])


@pytest.mark.parametrize("language,invalid", [("English", False), ("Vietnamese", False),
    ("English and Vietnamese", False), ("English and Vietnamese", True)])
@pytest.mark.parametrize("callbacks", [False, True, "exhausted", "stopped", "linked_stopped"])
def test_exact_engine_native_spawn_recorder_with_parent_persistence(tmp_path, monkeypatch, language, invalid, callbacks):
    def forbidden(*args, **kwargs):
        raise AssertionError("parent fixture attempted provider/network invocation")

    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-NEVER_ECHO")
    monkeypatch.setattr(httpx.Client, "send", forbidden)
    monkeypatch.setattr(httpx.AsyncClient, "send", forbidden)
    exhausted = callbacks == "exhausted"
    linked_attempt = callbacks == "linked_stopped"
    stopped_attempt = callbacks in {"stopped", "linked_stopped"}
    child = ({False: fixture_child, True: invalid_fixture_child} if not callbacks else
             {False: callback_fixture_child, True: invalid_callback_fixture_child})[invalid and not exhausted]
    monkeypatch.setattr("tradingagents.platform.analysis.supervision._child", child)
    database, owner, original = _database(tmp_path / "db")
    graph = None
    try:
        with database.session() as session:
            instrument = PlatformRepository(session).get_instrument(original.instrument_id)
        analysts = ("market", "social", "news", "fundamentals")
        sources = context(instrument)
        first = sources.by_analyst["market"][0]
        extras = {role: (AnalysisSnapshot(manifest=first.manifest.model_copy(update={
            "snapshot_id": uuid4(), "dataset": role}), payload=first.payload),)
            for role in analysts if role != "market"}
        sources = sources.model_copy(update={"by_analyst": {**sources.by_analyst, **extras},
            "source_max_age_seconds": dict.fromkeys(analysts, 0)})
        run = original.model_copy(update={"run_id": uuid4(), "analysis_as_of": NOW, "selected_analysts": analysts,
            "report_language": {"English": "en", "Vietnamese": "vi", "English and Vietnamese": "en-vi"}[language],
            "snapshot_ids": tuple(source.manifest.snapshot_id for group in sources.by_analyst.values() for source in group),
            "decision_inputs": {"snapshots_by_analyst": {role: tuple(source.manifest.snapshot_id for source in group)
                for role, group in sources.by_analyst.items()}, "source_max_age_seconds": dict.fromkeys(analysts, 0)}})
        run = type(original).model_validate(run.model_dump())
        if exhausted:
            run = type(original).model_validate(run.model_copy(update={
                "execution_limits": {"wall_seconds": 1800, "model_calls": 1}}).model_dump())
        with database.session() as session:
            PlatformRepository(session).save_run(run)
        artifact_store = LocalArtifactStore(tmp_path / "owned-blobs")
        if linked_attempt:
            with database.session() as session:
                OwnerAuth(session).bootstrap_owner("native-linked@example.test", "synthetic fixture password",
                    owner_id=owner, now=NOW)
                repository = PlatformRepository(session)
                artifacts = ArtifactService(artifact_store, repository)
                for group in sources.by_analyst.values():
                    for source in group:
                        repository.add_snapshot(source.manifest)
                        artifacts.create(owner_id=owner, kind=ArtifactKind.SNAPSHOT_PAYLOAD,
                            media_type="application/json", content=source.payload.encode(),
                            instrument_id=instrument.instrument_id, snapshot_id=source.manifest.snapshot_id,
                            created_at=NOW, expected_hash=source.manifest.content_hash)
            _enqueue(database, owner, run, payload={"instrument_id": str(run.instrument_id),
                "analysis_as_of": run.analysis_as_of.isoformat(), "selected_analysts": list(analysts),
                "config_hash": run.config_hash, "decision_inputs": run.decision_inputs.model_dump(mode="json"),
                "report_language": run.report_language})
        else:
            _enqueue(database, owner, run)
        with database.session() as session:
            job = DurableJobQueue(session).claim("fixture", lease_for=timedelta(minutes=5), now=NOW)
            if linked_attempt:
                JobWorker(database, worker_id="fixture", handlers={})._record_job_state(session, job, NOW)
        job_context = JobExecutionContext(database, job.job_id, "fixture", timedelta(minutes=5), lambda: NOW)
        events = []
        event_attempt = job.attempt
        def emit(kind, payload):
            with job_context.publication_session() as session:
                RunEventStore(session).append(owner_id=owner, run_id=run.run_id,
                    event_type=RunEventType(kind), occurred_at=NOW, payload={**payload, "attempt": event_attempt})
            events.append((kind, payload))

        observer = ResearchObserver(check_cancelled=job_context.raise_if_cancelled,
            emit=emit, max_calls=1 if exhausted else 128)
        started = observer.started
        request = AnalysisRequest(instrument=instrument, analysis_date=NOW.date(), selected_analysts=analysts,
            snapshot_context=sources, execution_observer=observer)
        config = {**DEFAULT_CONFIG, "llm_provider": "openai", "quick_think_llm": "quick", "deep_think_llm": "deep",
            "backend_url": "https://example.test/v1", "data_cache_dir": str(tmp_path / "cache"),
            "results_dir": str(tmp_path / "results"), "output_language": language,
            "max_debate_rounds": 2, "max_risk_discuss_rounds": 2}
        graph = TradingAgentsGraph(config=config, selected_analysts=analysts,
            snapshot_reports=sources.reports(instrument.instrument_id, analysts))
        fingerprint = build_initialized_graph_fingerprint(graph=graph, owner_id=owner, run=run,
            request=request, base_config=config)
        codec = SnapshotCheckpointCodec(fingerprint=fingerprint, nodes=graph.workflow.nodes)
        store = PrivateCheckpointStore(codec=codec)
        commit_pids = []
        ack_lost = False

        def commit(raw):
            nonlocal ack_lost
            commit_pids.append(os.getpid())
            receipt = store.commit(context=job_context, owner_id=owner, run_id=run.run_id, raw=raw)
            if (stopped_attempt and not ack_lost and any(channel == "market_report" and value
                    for _, channel, value in codec.decode(raw).pending_writes)):
                ack_lost = True
                raise CheckpointDatabaseError("fixture committed but acknowledgement lost")
            return receipt

        recording = SnapshotRecordingInputs.create(owner_id=owner, run=run, expected_fingerprint=fingerprint)
        with job_context.publication_session() as session:
            RunEventStore(session).append(owner_id=owner, run_id=run.run_id,
                event_type=RunEventType.RESEARCH_EXECUTION_STARTED, occurred_at=NOW,
                payload={"attempt": job.attempt})
        supervised = SupervisedAnalysisEngine(base_config=config, recording_inputs=recording,
            checkpoint_codec=codec, checkpoint_thread_id=str(run.run_id),
            checkpoint_commit=commit)
        if stopped_attempt:
            with pytest.raises(ResearchExecutionFailed, match="^checkpoint commit requires review$"):
                supervised.analyze(request)
            assert ack_lost
            prefix = json.loads(Path(config["results_dir"] + ".fixture-trace.json").read_text())
            assert prefix["closed_clients"] is None  # Killed SDK cleanup is unknown.
            assert prefix["pid"] != os.getpid()
            with pytest.raises(ProcessLookupError):
                os.kill(prefix["pid"], 0)
            assert observer.started_calls == len(prefix["trace"]) == 1
            assert observer.receipt()["usage"]["total_tokens"] == 15
            with database.session() as session:
                rows = session.scalars(select(ResearchCheckpointRow).order_by(ResearchCheckpointRow.sequence)).all()
                saved = store.load_latest(session=session, owner_id=owner, run_id=run.run_id)
                assert saved.pending_writes and any(channel == "market_report" for _, channel, _ in saved.pending_writes)
                raw = rows[-1].payload
                prior_rows = [(row.record_id, row.content_hash, row.payload) for row in rows]
                evidence = load_accounting_evidence(session=session, owner_id=owner, run_id=run.run_id)
                assert evidence.started_calls == 1 and evidence.elapsed_upper_bound is not None
                if not linked_attempt:
                    retained = build_retained_observer(session=session, owner_id=owner, run_id=run.run_id,
                        expected_accounting=evidence, check_cancelled=job_context.raise_if_cancelled, emit=emit)
            baseline = NativeFixtureEngine(base_config={**config, "_fixture_invalid_translation": invalid,
                                                       "_fixture_callbacks": True})
            baseline.snapshot_recorder = SnapshotRecorder(owner_id=owner, run=run,
                expected_fingerprint=fingerprint, commit=lambda raw: None)
            baseline_request = request.model_copy(update={"execution_observer": ResearchObserver(
                check_cancelled=lambda: None, emit=lambda *args: None)})
            expected = baseline.analyze(baseline_request, fixture_execution=lambda options:
                AnalysisEngine(base_config=options).analyze(baseline_request))
            if linked_attempt:
                from tests.test_continuation_consent import history

                later = NOW + timedelta(seconds=60)
                with database.session() as session:
                    terminal = DurableJobQueue(session).fail(job.job_id, "fixture", retryable=False,
                        error_code="RESEARCH_EXECUTION_FAILED", error_message="ResearchExecutionFailed", now=later)
                    JobWorker(database, worker_id="fixture", handlers={})._record_job_state(session, terminal, later)
                    auth = OwnerAuth(session).login("native-linked@example.test", "synthetic fixture password", now=later)
                before_linked = history(database)
                consents = ContinuationConsentStore(database, codec=codec, clock=lambda: later)
                with database.session() as session:
                    observation = consents.observe(session=session, owner_id=owner, run_id=run.run_id)
                consent = consents.record(session_token=auth.token, csrf_token=auth.csrf_token,
                    expected_observation=observation, idempotency_key=uuid4(), confirm_continue=True)
                executions = LinkedExecutionStore(consents)
                executions.allocate(execution_id=consent.execution_id, session_token=auth.token, csrf_token=auth.csrf_token)
                lease = executions.claim(execution_id=consent.execution_id, worker_id="linked-native")
                from tradingagents.platform.analysis.linked_results import LinkedResultPublisher

                publisher = LinkedResultPublisher(artifact_store)
                linked_context = LinkedPublicationContext.prepare(executions, lease, save_stage=publisher.save_stage)
                loaded = LinkedOriginalResearch.load(context=linked_context, artifact_store=artifact_store)
                publisher.bind(linked_context, loaded)
                terminal_run = loaded.recording_inputs.read().run
                assert terminal_run.completed_at == later and terminal_run.error_code == "RESEARCH_EXECUTION_FAILED"
                original_terminal = next(row["payload"] for row in before_linked["analysis_runs"]
                    if row["run_id"] == run.run_id)
                assert terminal_run.model_dump(mode="json") == original_terminal
                retained = linked_context.observer
                recovered_request = loaded.request
                recovered_recording = loaded.recording_inputs
                recovered_commit = linked_context.commit_checkpoint
            else:
                event_attempt = 2
                with job_context.publication_session() as session:
                    RunEventStore(session).append(owner_id=owner, run_id=run.run_id,
                        event_type=RunEventType.RESEARCH_EXECUTION_STARTED, occurred_at=NOW, payload={"attempt": 2})
                recovered_request = request.model_copy(update={"execution_observer": retained})
                recovered_recording, recovered_commit = recording, commit
            monkeypatch.setattr("tradingagents.platform.analysis.supervision._child", restored_callback_fixture_child)
            recovery = SupervisedAnalysisEngine(base_config={**config, "_fixture_restore_invalid": invalid},
                recording_inputs=recovered_recording, checkpoint_codec=codec, checkpoint_thread_id=str(run.run_id),
                checkpoint_commit=recovered_commit, restore_checkpoint=raw,
                **({"linked_context": linked_context} if linked_attempt else {}))
            result = recovery.analyze(recovered_request)
            suffix = json.loads(Path(config["results_dir"] + ".fixture-trace.json").read_text())
            assert suffix["pid"] != prefix["pid"] and suffix["closed_clients"] == 2
            with pytest.raises(ProcessLookupError):
                os.kill(suffix["pid"], 0)
            assert prefix["trace"] + suffix["trace"] == json.loads(json.dumps(baseline.model_trace))
            expected_data = expected.model_dump()
            expected_data["final_state"] = {key: value for key, value in expected_data["final_state"].items()
                                            if key in RESULT_FIELDS}
            for key in ("investment_debate_state", "risk_debate_state"):
                expected_data["final_state"][key] = {"history": expected_data["final_state"][key].get("history", "")}
            assert result.model_dump() == expected_data
            assert retained._retained_started_calls == 1 and retained.max_calls == 128
            assert retained._retained_elapsed_seconds == evidence.elapsed_upper_bound
            with database.session() as session:
                after = session.scalars(select(ResearchCheckpointRow).order_by(ResearchCheckpointRow.sequence)).all()
                assert [(row.record_id, row.content_hash, row.payload) for row in after[:len(rows)]] == prior_rows
                aggregate = load_accounting_evidence(session=session, owner_id=owner, run_id=run.run_id)
                assert aggregate.attempts == (1, 2)
                assert aggregate.started_calls == len(baseline.model_trace)
                assert aggregate.reported_total_tokens == len(baseline.model_trace) * 15
                assert aggregate.elapsed_upper_bound >= evidence.elapsed_upper_bound
                assert PlatformRepository(session).get_run(original.run_id, owner).decision_inputs is None
                if linked_attempt:
                    from tradingagents.platform.persistence.models import (
                        ResearchExecutionCompletionRow,
                    )

                    completion = session.get(ResearchExecutionCompletionRow, linked_context.execution_id)
                    assert completion is not None and completion.checkpoint_record_id == after[-1].record_id
                    artifacts = ArtifactService(artifact_store, PlatformRepository(session))
                    report = json.loads(artifacts.read(completion.report_artifact_id, owner)[1])
                    assert report["linked_execution"]["original_run_status"] == "failed"
                    assert report["linked_execution"]["accounting"]["reported_total_tokens"] == aggregate.reported_total_tokens
                    assert report["validation_issues"] == list(result.validation_issues)
                    candidate = PlatformRepository(session).get_decision(completion.decision_id, owner)
                    assert candidate.requires_human_approval is True and candidate.status.value == "review"
                    assert report["canonical_research"] == result.final_state.get("structured_decision")
                    from tradingagents.platform.analysis.linked_results import (
                        read_linked_completion,
                    )

                    assert read_linked_completion(session=session, artifact_store=artifact_store,
                        owner_id=owner, execution_id=linked_context.execution_id).decision_id == candidate.decision_id
                    assert session.get(ResearchExecutionDispatchRow, linked_context.execution_id) is not None
                    linked_rows = session.scalars(select(ResearchCheckpointExecutionRow)).all()
                    assert linked_rows and all(row.execution_id == linked_context.execution_id for row in linked_rows)
                    assert all(row.attempt == 2 for row in after[len(rows):])
            if linked_attempt:
                from tests.test_linked_publication import assert_old_history_unchanged

                assert_old_history_unchanged(database, before_linked)
                with pytest.raises(ValueError, match="^invalid checkpoint bridge configuration$"):
                    recovery.analyze(recovered_request)
            assert list((tmp_path / "results").iterdir()) == []
            assert set(commit_pids) == {os.getpid()}
            return
        if exhausted:
            with pytest.raises(ResearchBudgetExceeded, match="research model-call budget exhausted"):
                supervised.analyze(request)
            usage = observer.receipt()["usage"]
            assert observer.started == started and observer.max_calls == 1
            assert observer.started_calls == usage["model_calls"] == usage["calls_with_usage"] == 1
            assert usage["input_tokens"] == 10 and usage["output_tokens"] == 5 and usage["total_tokens"] == 15
            assert usage["failed_calls"] == 0 and usage["cost"] is None
            assert [data["usage"]["total_tokens"] for kind, data in events if kind == "model.usage"] == [0, 15, 15]
            assert observer.completed == ["Market Analyst"]
            assert commit_pids and set(commit_pids) == {os.getpid()}
            with database.session() as session:
                rows = session.scalars(select(ResearchCheckpointRow)).all()
                assert rows and all(row.owner_id == owner and row.run_id == run.run_id for row in rows)
                for row in rows:
                    codec.decode(row.payload)
                usage_events = [event for event in RunEventStore(session).list_after(owner, run.run_id, limit=500)
                                if event.event_type is RunEventType.MODEL_USAGE]
                assert len(usage_events) == 3
                assert usage_events[-1].payload["execution_stopped"] is True
                assert usage_events[0].payload["usage"]["started_model_calls"] == 1
                assert usage_events[0].payload["usage"]["model_calls"] == 0
                assert usage_events[0].payload["usage"]["status"] == "incomplete"
                assert usage_events[1].payload["usage"] == usage
                assert all(event.payload["attempt"] == job.attempt for event in usage_events)
                evidence = load_accounting_evidence(session=session, owner_id=owner, run_id=run.run_id)
                assert evidence.evidence_status == "PASS" and evidence.started_calls == 1
                assert evidence.reported_total_tokens == 15 and evidence.exact_elapsed_known is False
                assert evidence.elapsed_upper_bound is not None
                allowance = load_remaining_allowance(session=session, owner_id=owner, run_id=run.run_id)
                assert allowance.assessment_status == "BLOCKED" and allowance.remaining_model_calls == 0
                assert PlatformRepository(session).get_run(original.run_id, owner).decision_inputs is None
            return
        result = supervised.analyze(request)
        trace = json.loads(Path(config["results_dir"] + ".fixture-trace.json").read_text())
        assert trace["pid"] != os.getpid() and trace["closed_clients"] == 2
        with pytest.raises(ProcessLookupError):
            os.kill(trace["pid"], 0)  # Parent supervision reaped the completed child.
        assert commit_pids and set(commit_pids) == {os.getpid()}
        baseline = NativeFixtureEngine(base_config={**config, "_fixture_invalid_translation": invalid,
                                                   "_fixture_callbacks": callbacks})
        baseline_observer = ResearchObserver(check_cancelled=lambda: None, emit=lambda *args: None)
        baseline_request = request.model_copy(update={"execution_observer": baseline_observer})
        if callbacks:
            # Construct actual SDKs but run baseline without a saver/recorder.
            baseline.snapshot_recorder = SnapshotRecorder(owner_id=owner, run=run,
                expected_fingerprint=fingerprint, commit=lambda raw: None)
            expected = baseline.analyze(baseline_request, fixture_execution=lambda options:
                AnalysisEngine(base_config=options).analyze(baseline_request))
        else:
            expected = baseline.analyze(baseline_request)
        assert trace["trace"] == json.loads(json.dumps(baseline.model_trace))
        actual_data, expected_data = result.model_dump(), expected.model_dump()
        expected_data["final_state"] = {key: value for key, value in expected_data["final_state"].items()
                                        if key in RESULT_FIELDS}
        # Supervisor intentionally publishes only debate history, not internal counters.
        for key in ("investment_debate_state", "risk_debate_state"):
            expected_data["final_state"][key] = {"history": expected_data["final_state"][key].get("history", "")}
        assert actual_data == expected_data
        assert observer.completed == baseline_observer.completed
        assert set(observer.completed) == STAGES
        assert observer.completed.count("Bull Researcher") == 2
        assert observer.completed.count("Aggressive Analyst") == 2
        assert observer.started == started
        assert observer.max_seconds == 1800 and observer.max_calls == 128
        assert observer.receipt()["supervision_mode"] == "spawned_process"
        usage = observer.receipt()["usage"]
        if callbacks:
            calls = len(trace["trace"])
            assert calls > 14
            assert observer.started_calls == calls == baseline_observer.started_calls
            assert usage == baseline_observer.receipt()["usage"]
            assert usage["model_calls"] == usage["calls_with_usage"] == calls
            assert usage["input_tokens"] == 10 * calls and usage["output_tokens"] == 5 * calls
            assert usage["total_tokens"] == 15 * calls and usage["status"] == "reported"
            assert usage["cost"] is None and usage["provider_request_attempts"] is None
        else:
            assert usage["status"] == "incomplete"  # Synthetic invoke bypasses callbacks.
        if invalid:
            assert result.decision_payload is None
            assert "report_translation_unavailable" in result.validation_issues
        else:
            assert result.decision_payload.thesis == "Snapshot thesis"
        with database.session() as session:
            rows = session.scalars(select(ResearchCheckpointRow).order_by(ResearchCheckpointRow.sequence)).all()
            assert len(rows) > 17
            assert [row.sequence for row in rows] == list(range(1, len(rows) + 1))
            assert all(row.owner_id == owner and row.run_id == run.run_id and row.fingerprint == fingerprint for row in rows)
            assert all(b"synthetic-NEVER_ECHO" not in row.payload and b"PRIVATE_NATIVE_REASONING" not in row.payload for row in rows)
            for row in rows:
                assert codec.decode(row.payload).checkpoint["channel_values"].get("messages", []) == []
            assert store.load_latest(session=session, owner_id=owner, run_id=run.run_id) is not None
            if callbacks:
                usage_events = [event for event in RunEventStore(session).list_after(owner, run.run_id, limit=500)
                                if event.event_type is RunEventType.MODEL_USAGE]
                assert len(usage_events) == 2 * calls + 1
                assert usage_events[-1].payload["execution_stopped"] is True
                assert usage_events[-1].payload["usage"] == usage
                assert all(event.payload["execution_limits"] == {"wall_seconds": 1800, "model_calls": 128}
                           and event.payload["elapsed_seconds"] >= 0
                           and event.payload["attempt"] == job.attempt for event in usage_events)
                evidence = load_accounting_evidence(session=session, owner_id=owner, run_id=run.run_id)
                assert evidence.evidence_status == "PASS" and evidence.started_calls == calls
                assert evidence.reported_total_tokens == 15 * calls and evidence.unreported_started_calls == 0
                assert evidence.exact_elapsed_known is False
                assert evidence.elapsed_upper_bound is not None
                allowance = load_remaining_allowance(session=session, owner_id=owner, run_id=run.run_id)
                assert allowance.assessment_status == "PASS" and allowance.remaining_model_calls == 128 - calls
                assert 0 < allowance.remaining_wall_seconds <= 1800
            assert PlatformRepository(session).get_run(original.run_id, owner).decision_inputs is None
        if callbacks is True:
            # Synthetic mechanism proof: branch from an intermediate completed
            # run tuple into an actual new child, retaining ALL first-attempt
            # costs (even work after the chosen tuple). Not recovery consent.
            raw = [row.payload for row in rows if (
                codec.decode(row.payload).checkpoint["channel_values"].get("market_report")
                and not codec.decode(row.payload).checkpoint["channel_values"].get("news_report"))][-1]
            prior_rows = [(row.record_id, row.content_hash, row.payload) for row in rows]
            with database.session() as session:
                retained = build_retained_observer(session=session, owner_id=owner, run_id=run.run_id,
                    expected_accounting=evidence, check_cancelled=job_context.raise_if_cancelled, emit=emit)
            event_attempt = 2
            with job_context.publication_session() as session:
                RunEventStore(session).append(owner_id=owner, run_id=run.run_id,
                    event_type=RunEventType.RESEARCH_EXECUTION_STARTED, occurred_at=NOW, payload={"attempt": 2})
            monkeypatch.setattr("tradingagents.platform.analysis.supervision._child", restored_callback_fixture_child)
            restored_supervisor = SupervisedAnalysisEngine(base_config={**config, "_fixture_restore_invalid": invalid},
                recording_inputs=recording, checkpoint_codec=codec, checkpoint_thread_id=str(run.run_id),
                checkpoint_commit=commit, restore_checkpoint=raw)
            # Fixture-only option is removed by fixture bootstrap before the
            # original production child fingerprint guard initializes clients.
            restored_result = restored_supervisor.analyze(request.model_copy(update={"execution_observer": retained}))
            restored_trace = json.loads(Path(config["results_dir"] + ".fixture-trace.json").read_text())
            assert restored_trace["pid"] != trace["pid"] and restored_trace["pid"] != os.getpid()
            with pytest.raises(ProcessLookupError):
                os.kill(restored_trace["pid"], 0)
            assert restored_trace["closed_clients"] == 2
            assert 0 < len(restored_trace["trace"]) < len(trace["trace"])
            assert restored_trace["trace"] == trace["trace"][-len(restored_trace["trace"]):]
            assert restored_result.model_dump() == actual_data
            assert retained.max_calls == 128 and retained._retained_started_calls == calls
            assert retained._retained_elapsed_seconds == evidence.elapsed_upper_bound
            with database.session() as session:
                after = session.scalars(select(ResearchCheckpointRow).order_by(ResearchCheckpointRow.sequence)).all()
                assert [(row.record_id, row.content_hash, row.payload) for row in after[:len(rows)]] == prior_rows
                aggregate = load_accounting_evidence(session=session, owner_id=owner, run_id=run.run_id)
                assert aggregate.attempts == (1, 2)
                assert aggregate.started_calls == calls + len(restored_trace["trace"])
                assert aggregate.reported_total_tokens == aggregate.started_calls * 15
                assert aggregate.elapsed_upper_bound is not None
                assert aggregate.elapsed_upper_bound >= evidence.elapsed_upper_bound
        assert list((tmp_path / "results").iterdir()) == []
    finally:
        if graph is not None:
            for llm in (graph.quick_thinking_llm, graph.deep_thinking_llm):
                llm.root_client.close()
                asyncio.run(llm.root_async_client.close())
        database.dispose()
