import json
from datetime import timedelta
from uuid import uuid4, uuid5

import pytest

from tests.test_durable_jobs import NOW, _database, _enqueue
from tradingagents.contracts import DecisionStatus, JobKind, JobStatus
from tradingagents.platform.analysis import AnalysisEngine
from tradingagents.platform.artifacts import ArtifactService, LocalArtifactStore
from tradingagents.platform.jobs import DurableJobQueue, JobWorker
from tradingagents.platform.jobs.analysis import AnalysisJobHandler
from tradingagents.platform.persistence import PlatformRepository


def setup_handler(tmp_path, callback=None, *, report_language=None, payload_language=None):
    database, owner, run = _database(tmp_path)
    if report_language is not None:
        run = run.model_copy(update={"run_id": uuid4(), "report_language": report_language})
        with database.session() as session:
            PlatformRepository(session).save_run(run)
    store = LocalArtifactStore(tmp_path / "artifacts")
    calls = []

    class Graph:
        def __init__(self, **kwargs):
            calls.append(kwargs)

        def propagate(self, *args, **kwargs):
            if callback:
                callback(database, owner)
            return {"final_trade_decision": "Buy narrative", "structured_decision": {
                "rating": "Buy", "executive_summary": "Summary", "investment_thesis": "Thesis",
                "confidence": .8, "risks": ["Risk"], "invalidation_conditions": ["Condition"],
            }}, "Buy"

    handler = AnalysisJobHandler(database, store, engine=AnalysisEngine(graph_factory=Graph))
    worker = JobWorker(database, worker_id="analysis-test", handlers={JobKind.ANALYSIS_RUN: handler},
                       retry_base=timedelta(0), clock=lambda: NOW)
    payload = {"instrument_id": str(run.instrument_id), "analysis_as_of": NOW.isoformat(),
               "selected_analysts": list(run.selected_analysts), "config_hash": run.config_hash}
    if report_language is not None:
        payload["report_language"] = payload_language or report_language
    job = _enqueue(database, owner, run, payload=payload)
    return database, owner, run, store, calls, worker, job


@pytest.mark.parametrize("language,expected", [("en", "English"), ("vi", "Vietnamese"), ("en-vi", "English and Vietnamese")])
def test_worker_uses_immutable_report_language(tmp_path, language, expected):
    database, owner, run, store, calls, worker, _ = setup_handler(tmp_path, report_language=language)
    try:
        result = worker.run_once()
        assert result.status is JobStatus.SUCCEEDED
        assert calls[0]["config"]["output_language"] == expected
        with database.session() as session:
            repo = PlatformRepository(session)
            _, content = ArtifactService(store, repo).read(result.output_artifact_ids[0], owner)
            assert json.loads(content)["report_language"] == language
            from tradingagents.platform.persistence import ImmutableRecordConflict
            with pytest.raises(ImmutableRecordConflict):
                repo.save_run(repo.get_run(run.run_id, owner).model_copy(update={"report_language": "vi" if language != "vi" else "en"}))
    finally:
        database.dispose()


def test_worker_rejects_tampered_language_before_model_call(tmp_path):
    database, _, _, _, calls, worker, _ = setup_handler(tmp_path, report_language="en-vi", payload_language="vi")
    try:
        assert worker.run_once().status is not JobStatus.SUCCEEDED
        assert calls == []
    finally:
        database.dispose()


def test_durable_handler_persists_research_without_fabricating_evidence(tmp_path):
    database, owner, run, store, calls, worker, _ = setup_handler(tmp_path)
    result = worker.run_once()
    assert result.status is JobStatus.SUCCEEDED
    assert len(result.output_artifact_ids) == 1
    assert calls[0]["config"]["quick_think_llm"] == run.quick_model
    with database.session() as session:
        repo = PlatformRepository(session)
        decision = repo.get_decision(uuid5(run.run_id, "decision-v1"), owner)
        assert decision.status is DecisionStatus.REVIEW
        assert decision.target_weight is None
        assert decision.evidence == ()
        artifact, content = ArtifactService(store, repo).read(result.output_artifact_ids[0], owner)
        assert artifact.run_id == run.run_id
        assert b"Buy narrative" in content
        assert b"UNVERIFIED" in content
    database.dispose()


def test_completion_retry_reuses_committed_result_without_second_model_call(tmp_path, monkeypatch):
    database, _, _, _, calls, worker, _ = setup_handler(tmp_path)
    complete = DurableJobQueue.complete
    attempts = []

    def transient_failure(self, *args, **kwargs):
        attempts.append(1)
        if len(attempts) == 1:
            raise RuntimeError("completion unavailable after output commit")
        return complete(self, *args, **kwargs)

    monkeypatch.setattr(DurableJobQueue, "complete", transient_failure)
    assert worker.run_once().status is JobStatus.RETRY_WAIT
    assert worker.run_once().status is JobStatus.SUCCEEDED
    assert len(calls) == 1
    database.dispose()


def test_finalization_retry_cannot_reenter_engine_if_saved_output_pair_becomes_unavailable(tmp_path, monkeypatch):
    database, _, _, _, calls, worker, _ = setup_handler(tmp_path)

    def completion_unavailable(*args, **kwargs):
        raise RuntimeError("synthetic completion unavailable")

    monkeypatch.setattr(DurableJobQueue, "complete", completion_unavailable)
    assert worker.run_once().status is JobStatus.RETRY_WAIT
    # Simulate an unavailable store without deleting any persisted evidence.
    monkeypatch.setattr(ArtifactService, "read", lambda *args, **kwargs: None)
    monkeypatch.setattr(PlatformRepository, "get_decision", lambda *args, **kwargs: None)
    failed = worker.run_once()
    assert failed.status is JobStatus.FAILED
    assert failed.error_code == "RESEARCH_EXECUTION_FAILED"
    assert len(calls) == 1
    database.dispose()


def test_cancellation_during_graph_does_not_publish_output(tmp_path):
    captured = {}

    def cancel(database, owner):
        with database.session() as session:
            DurableJobQueue(session).request_cancel(captured["job_id"], owner, now=NOW)

    database, owner, run, _, calls, worker, job = setup_handler(tmp_path, cancel)
    captured["job_id"] = job.job_id
    result = worker.run_once()
    assert result.status is JobStatus.CANCELLED
    assert result.output_artifact_ids == ()
    assert len(calls) == 1
    with database.session() as session:
        repo = PlatformRepository(session)
        assert repo.get_decision(uuid5(run.run_id, "decision-v1"), owner) is None
        assert repo.get_artifact(uuid5(run.run_id, "analysis-report-v1"), owner) is None
    database.dispose()
