from uuid import uuid4, uuid5

import pytest

from tests.test_decision_lifecycle import _approval
from tests.test_risk_engine import NOW
from tests.test_risk_provenance import setup_risk
from tradingagents.contracts import DecisionStatus, JobKind, JobStatus
from tradingagents.contracts.runs import DecisionRunInputs
from tradingagents.platform.analysis import AnalysisEngine
from tradingagents.platform.analysis.evidence_service import EvidenceGraphService
from tradingagents.platform.artifacts import ArtifactService
from tradingagents.platform.jobs import DurableJobQueue, JobWorker
from tradingagents.platform.jobs.analysis import AnalysisJobHandler
from tradingagents.platform.persistence import PlatformRepository


@pytest.mark.parametrize("case", ["valid", "fixture_graph", "invalid_fixture_graph", "missing_citation", "unknown_citation", "model_weight", "invalid_number", "cancel_after_publish"])
def test_snapshot_worker_evidence_risk_and_approval_pipeline(tmp_path, monkeypatch, case):
    database, store, seeded = setup_risk(tmp_path)
    with database.session() as session:
        repo = PlatformRepository(session, artifact_store=store)
        original_run = repo.get_run(seeded.run_id, seeded.owner_id)
        source = seeded.risk_snapshot_ids[0]
        policy_check = seeded.policy_checks[0]
        inputs = DecisionRunInputs(snapshots_by_analyst={"market": (source,)},
            source_max_age_seconds={"market": 86400},
            portfolio_snapshot_id=seeded.portfolio_snapshot_id, policy_id=policy_check.policy_id,
            policy_version=policy_check.policy_version, requested_target_weight=.3,
            risk_snapshot_ids=seeded.risk_snapshot_ids)
        run = original_run.model_copy(update={"run_id": uuid4(), "selected_analysts": ("market",),
            "snapshot_ids": inputs.snapshot_ids(), "decision_inputs": inputs})
        repo.save_run(run)
        DurableJobQueue(session).enqueue(owner_id=run.owner_id, run_id=run.run_id,
            idempotency_key=str(run.run_id), now=NOW, payload={
                "instrument_id": str(run.instrument_id), "analysis_as_of": NOW.isoformat(),
                "selected_analysts": ["market"], "config_hash": run.config_hash,
                "decision_inputs": inputs.model_dump(mode="json"),
            })

    class Graph:
        def __init__(self, **kwargs):
            assert str(source) in kwargs["snapshot_reports"]["market"]

        def propagate_snapshots(self, *args, **kwargs):
            assert kwargs["portfolio"] is not None
            assert len(kwargs["portfolio"].positions) == 2
            claims = [{"claim": text, "snapshot_ids": [str(source)]}
                      for text in ("Thesis", "Risk", "Invalidation")]
            if case == "missing_citation":
                claims.pop()
            elif case == "unknown_citation":
                claims[0]["snapshot_ids"] = [str(uuid4())]
            payload = {"rating": "Buy", "executive_summary": "Research", "investment_thesis": "Thesis",
                "confidence": .7, "risks": ["Risk"], "invalidation_conditions": ["Invalidation"],
                "evidence_claims": claims}
            if case == "model_weight":
                payload["target_weight"] = .99
            if case == "invalid_number":
                payload["observed_numbers"] = [{"snapshot_id": str(source), "fact_id": "invented", "value": 999, "decimal_places": 0}]
            return {"final_trade_decision": "Research", "structured_decision": payload}, "Buy"

    if case in {"fixture_graph", "invalid_fixture_graph"}:
        from scripts.web_fixture import InvalidSyntheticGraph, SyntheticSnapshotGraph
        graph_factory = InvalidSyntheticGraph if case == "invalid_fixture_graph" else SyntheticSnapshotGraph
        assert not hasattr(graph_factory, "propagate")  # No live-tool fallback.
    else:
        graph_factory = Graph
    handler = AnalysisJobHandler(database, store, engine=AnalysisEngine(graph_factory=graph_factory))
    if case == "cancel_after_publish":
        complete = DurableJobQueue.complete

        def cancel_before_complete(self, job_id, *args, **kwargs):
            self.request_cancel(job_id, run.owner_id, now=NOW)
            return complete(self, job_id, *args, **kwargs)

        monkeypatch.setattr(DurableJobQueue, "complete", cancel_before_complete)
    worker = JobWorker(database, worker_id="snapshot-worker", handlers={JobKind.ANALYSIS_RUN: handler}, clock=lambda: NOW)
    job = worker.run_once()
    assert job.status is (JobStatus.CANCELLED if case == "cancel_after_publish" else JobStatus.SUCCEEDED)
    with database.session() as session:
        repo = PlatformRepository(session, artifact_store=store)
        decision = repo.get_decision(uuid5(run.run_id, "decision-v1"), run.owner_id)
        if case == "cancel_after_publish":
            assert decision.status is DecisionStatus.READY_FOR_APPROVAL  # Immutable original research.
            with pytest.raises(ValueError, match="successfully completed"):
                repo.add_decision_event(_approval(decision))
            assert repo.list_decision_events(decision.decision_id, run.owner_id) == ()
        elif case in {"valid", "fixture_graph"}:
            assert decision.status is DecisionStatus.READY_FOR_APPROVAL
            assert decision.target_weight == .3  # Owner input, not model output.
            assert len(job.output_artifact_ids) == 2
            evidence = EvidenceGraphService(ArtifactService(store, repo)).read(job.output_artifact_ids[1], run.owner_id)
            if case == "valid":
                assert {claim.claim for claim in evidence.claims} == {"Thesis", "Risk", "Invalidation"}
            else:
                assert "SYNTHETIC LOCAL QA" in decision.thesis
                assert len(evidence.claims) == 3
            assert all(ref.snapshot_id == source for ref in evidence.evidence)
            repo.add_decision_event(_approval(decision))
        else:
            assert decision.status is DecisionStatus.REVIEW
            assert decision.target_weight is None
            if case == "invalid_number":
                import json

                service = ArtifactService(store, repo)
                _, content = service.read(job.output_artifact_ids[0], run.owner_id)
                report = json.loads(content)
                assert report["structured_narrative"] is None
                assert report["quantitative_references"][0]["fact_id"] == "invented"
                assert report["validation_issues"] == ["numeric_claim_not_supported"]
    database.dispose()
