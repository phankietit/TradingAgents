import json
from datetime import timedelta
from types import SimpleNamespace
from uuid import uuid4, uuid5

import pytest

from tests.test_durable_jobs import _database
from tests.test_risk_engine import NOW
from tests.test_risk_provenance import setup_risk
from tradingagents.contracts import ArtifactKind, JobKind, JobStatus
from tradingagents.contracts.runs import DecisionRunInputs
from tradingagents.platform.analysis import AnalysisEngine
from tradingagents.platform.analysis.observer import (
    STAGES,
    ResearchBudgetExceeded,
    ResearchObserver,
)
from tradingagents.platform.analysis.stage_records import (
    STAGE_PATHS,
    ResearchStageRecord,
    ResearchStageService,
    stage_sections,
)
from tradingagents.platform.artifacts import ArtifactService, LocalArtifactStore
from tradingagents.platform.events import RunEventStore
from tradingagents.platform.jobs import DurableJobQueue, JobWorker
from tradingagents.platform.jobs.analysis import AnalysisJobHandler
from tradingagents.platform.persistence import PlatformRepository


def test_projection_covers_every_original_role_without_retaining_arbitrary_state():
    assert set(STAGE_PATHS) == set(STAGES)
    outputs = {"market_report": "UNVALIDATED market research",
               "messages": ["private prompt", "model reasoning"],
               "target_weight": .99, "api_key": "sk-not-real"}
    assert stage_sections("Market Analyst", outputs) == {"market_report": "UNVALIDATED market research"}
    assert stage_sections("unknown", outputs) == {}
    assert stage_sections("Market Analyst", {"market_report": {"unknown": "not prose"}}) == {}


@pytest.mark.parametrize("stage", STAGE_PATHS)
def test_projection_preserves_exact_reader_text_for_each_role(stage):
    outputs = {}
    for label, path in STAGE_PATHS[stage].items():
        current = outputs
        for component in path[:-1]:
            current = current.setdefault(component, {})
        current[path[-1]] = "  Complete source-linked reader text: " + label
    expected = {label: "  Complete source-linked reader text: " + label for label in STAGE_PATHS[stage]}
    assert stage_sections(stage, outputs) == expected


def test_stage_fragments_are_immutable_owner_bound_and_never_approval_eligible(tmp_path):
    database, owner, run = _database(tmp_path)
    store = LocalArtifactStore(tmp_path / "artifacts")
    with database.session() as session:
        artifacts = ArtifactService(store, PlatformRepository(session, artifact_store=store))
        service = ResearchStageService(artifacts)
        manifest = service.persist(run, stage="Market Analyst", outputs={"market_report": "Research"},
            attempt=1, sequence=1, snapshot_attestation="UNVERIFIED")
        assert manifest.kind is ArtifactKind.RESEARCH_STAGE
        assert service.read(manifest.artifact_id, uuid4()) is None
        record = service.read(manifest.artifact_id, owner)
        assert record.research_quality == "unvalidated" and record.approval_eligible is False
        assert record.snapshot_ids == run.snapshot_ids and record.config_hash == run.config_hash
        raw = record.model_dump(mode="json")
        with pytest.raises(ValueError):
            ResearchStageRecord.model_validate({**raw, "approval_eligible": True})
        with pytest.raises(ValueError):
            ResearchStageRecord.model_validate({**raw, "sections": {"target_weight": "0.99"}})
        from tradingagents.agents.research_schemas import CanonicalSnapshotDecision

        with pytest.raises(ValueError):
            CanonicalSnapshotDecision.model_validate(raw)
        with pytest.raises(ValueError):
            service.persist(run, stage="Market Analyst", outputs={"market_report": "Changed"},
                attempt=1, sequence=1, snapshot_attestation="UNVERIFIED")


@pytest.mark.parametrize("field", ["run_id", "instrument_id", "config_hash", "snapshot_ids", "analysis_as_of", "prompt_version", "snapshot_attestation"])
def test_stage_reader_rejects_a_record_bound_to_another_context(tmp_path, field):
    database, owner, run = _database(tmp_path)
    store = LocalArtifactStore(tmp_path / "artifacts")
    with database.session() as session:
        artifacts = ArtifactService(store, PlatformRepository(session, artifact_store=store))
        manifest = ResearchStageService(artifacts).persist(run, stage="Market Analyst",
            outputs={"market_report": "Research"}, attempt=1, sequence=1, snapshot_attestation="UNVERIFIED")
        _, content = artifacts.read(manifest.artifact_id, owner)
        raw = json.loads(content)
        raw[field] = {"run_id": str(uuid4()), "instrument_id": str(uuid4()),
            "config_hash": "sha256:" + "f" * 64, "snapshot_ids": [str(uuid4())],
            "analysis_as_of": "2026-09-22T10:00:00Z", "prompt_version": "different",
            "snapshot_attestation": "PASS"}[field]
        fake = SimpleNamespace(read=lambda *_: (manifest, json.dumps(raw).encode()), repository=artifacts.repository)
        with pytest.raises(ValueError, match="context mismatch"):
            ResearchStageService(fake).read(manifest.artifact_id, owner)


def test_returned_stage_is_saved_before_deadline_failure_without_claiming_completion():
    clock = [0]
    captures, events = [], []
    observer = ResearchObserver(check_cancelled=lambda: None, emit=lambda *event: events.append(event),
        clock=lambda: clock[0], max_seconds=1,
        save_stage=lambda stage, outputs: captures.append((stage, outputs)) or uuid4())
    node = uuid4()
    observer.on_chain_start({}, {}, run_id=node, name="Market Analyst")
    clock[0] = 2
    with pytest.raises(ResearchBudgetExceeded):
        observer.on_chain_end({"market_report": "Research"}, run_id=node)
    assert len(captures) == 1
    assert observer.completed == []
    assert [kind for kind, _ in events] == ["stage.started"]


def test_cancelled_stage_cannot_publish_and_duplicate_end_cannot_republish():
    captures = []
    cancelled = [False]

    def check():
        if cancelled[0]:
            raise RuntimeError("cancelled")

    observer = ResearchObserver(check_cancelled=check, emit=lambda *_: None,
        save_stage=lambda *args: captures.append(args) or uuid4())
    node = uuid4()
    observer.on_chain_start({}, {}, run_id=node, name="Market Analyst")
    cancelled[0] = True
    with pytest.raises(RuntimeError, match="cancelled"):
        observer.on_chain_end({"market_report": "Research"}, run_id=node)
    assert captures == []
    cancelled[0] = False
    node = uuid4()
    observer.on_chain_start({}, {}, run_id=node, name="News Analyst")
    observer.on_chain_end({"news_report": "Research"}, run_id=node)
    observer.on_chain_end({"news_report": "Changed"}, run_id=node)
    assert len(captures) == 1


@pytest.mark.parametrize("case", ["failure", "engine_error", "deadline", "cancel", "cancel_after_stage", "stale_lease", "success"])
def test_real_worker_retains_private_stage_but_does_not_promote_failed_research(tmp_path, case):
    database, store, seeded = setup_risk(tmp_path)
    with database.session() as session:
        repo = PlatformRepository(session, artifact_store=store)
        original = repo.get_run(seeded.run_id, seeded.owner_id)
        source = seeded.risk_snapshot_ids[0]
        check = seeded.policy_checks[0]
        inputs = DecisionRunInputs(snapshots_by_analyst={"market": (source,)},
            source_max_age_seconds={"market": 86400}, portfolio_snapshot_id=seeded.portfolio_snapshot_id,
            policy_id=check.policy_id, policy_version=check.policy_version,
            requested_target_weight=.3, risk_snapshot_ids=seeded.risk_snapshot_ids)
        run = original.model_copy(update={"run_id": uuid4(), "selected_analysts": ("market",),
            "snapshot_ids": inputs.snapshot_ids(), "decision_inputs": inputs})
        repo.save_run(run)
        queued = DurableJobQueue(session).enqueue(owner_id=run.owner_id, run_id=run.run_id,
            idempotency_key=str(run.run_id), max_attempts=3 if case == "engine_error" else 1, now=NOW, payload={
                "instrument_id": str(run.instrument_id), "analysis_as_of": NOW.isoformat(),
                "selected_analysts": ["market"], "config_hash": run.config_hash,
                "decision_inputs": inputs.model_dump(mode="json")})

    class Graph:
        def __init__(self, **kwargs):
            self.observer = kwargs["execution_observer"]

        def propagate_snapshots(self, *args, **kwargs):
            node = uuid4()
            self.observer.on_chain_start({}, {}, run_id=node, name="Market Analyst")
            if case == "cancel":
                with database.session() as session:
                    DurableJobQueue(session).request_cancel(queued.job_id, run.owner_id, now=NOW)
            elif case == "stale_lease":
                JobWorker(database, worker_id="lease-recovery", handlers={},
                    clock=lambda: NOW + timedelta(minutes=6)).run_once()
            elif case == "deadline":
                self.observer.started -= self.observer.max_seconds + 1
            self.observer.on_chain_end({"market_report": "UNVALIDATED synthetic research",
                "messages": ["sk-not-real-private-prompt"], "structured_decision": {"target_weight": .99}}, run_id=node)
            if case == "cancel_after_stage":
                with database.session() as session:
                    DurableJobQueue(session).request_cancel(queued.job_id, run.owner_id, now=NOW)
                self.observer.on_chat_model_start({}, [], run_id=uuid4())
            if case == "failure":
                raise ResearchBudgetExceeded("synthetic time budget")
            if case == "engine_error":
                raise TimeoutError("synthetic vendor detail must not leak")
            payload = {"rating": "Hold", "executive_summary": "Research", "investment_thesis": "Thesis",
                "confidence": .5, "risks": ["Risk"], "invalidation_conditions": ["Invalidation"],
                "evidence_claims": [{"claim": text, "snapshot_ids": [str(source)]}
                    for text in ("Thesis", "Risk", "Invalidation")]}
            return {"final_trade_decision": "Research", "structured_decision": payload}, "Hold"

    handler = AnalysisJobHandler(database, store, engine=AnalysisEngine(graph_factory=Graph))
    job = JobWorker(database, worker_id="qa-stage-worker", clock=lambda: NOW,
        handlers={JobKind.ANALYSIS_RUN: handler}).run_once()
    assert job.status is {"failure": JobStatus.FAILED, "engine_error": JobStatus.FAILED, "deadline": JobStatus.FAILED,
                          "stale_lease": JobStatus.FAILED, "cancel": JobStatus.CANCELLED,
                          "cancel_after_stage": JobStatus.CANCELLED,
                          "success": JobStatus.SUCCEEDED}[case]
    if case == "engine_error":
        assert job.attempt == 1 and job.max_attempts == 3
        assert job.error_code == "RESEARCH_EXECUTION_FAILED"
        assert job.error_message == "ResearchExecutionFailed"
        assert JobWorker(database, worker_id="later-worker", clock=lambda: NOW + timedelta(hours=1),
            handlers={JobKind.ANALYSIS_RUN: handler}).run_once() is None
    with database.session() as session:
        repo = PlatformRepository(session, artifact_store=store)
        stages = [item for item in repo.list_run_artifacts(run.run_id, run.owner_id)
                  if item.kind is ArtifactKind.RESEARCH_STAGE]
        assert len(stages) == (0 if case in {"cancel", "stale_lease"} else 1)
        if stages:
            service = ResearchStageService(ArtifactService(store, repo))
            record = service.read(stages[0].artifact_id, run.owner_id)
            assert record.approval_eligible is False and record.snapshot_attestation == "PASS"
            assert record.sections == {"market_report": "UNVALIDATED synthetic research"}
            assert "sk-not-real" not in record.model_dump_json()
        events = RunEventStore(session).list_after(owner_id=run.owner_id, run_id=run.run_id)
        assert "sk-not-real" not in str([event.payload for event in events])
        if case == "deadline":
            assert job.error_code == "RESEARCH_BUDGET_EXHAUSTED"
            assert not any(event.event_type.value == "stage.completed" for event in events)
            assert any(event.event_type.value == "artifact.created" for event in events)
        decision = repo.get_decision(uuid5(run.run_id, "decision-v1"), run.owner_id)
        if case != "success":
            assert decision is None and job.output_artifact_ids == ()
        else:
            assert decision is not None and len(job.output_artifact_ids) == 2
