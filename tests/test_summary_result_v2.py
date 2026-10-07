"""V2 graph-result to evidence boundary; original CLI and stored history untouched."""

import copy
from uuid import uuid4

import pytest

from tests.test_analysis_engine import _instrument
from tests.test_risk_engine import NOW
from tests.test_snapshot_analysis import context
from tradingagents.platform.analysis import AnalysisEngine, AnalysisRequest, EvidenceGraphBuilder


@pytest.mark.parametrize("mutation", ["valid", "same_text", "unknown", "missing", "version", "parity"])
def test_v2_result_keeps_summary_support_and_refuses_incomplete_or_unknown_sources(mutation):
    instrument = _instrument()
    inputs = context(instrument)
    manifest = inputs.by_analyst["market"][0].manifest
    sid = str(manifest.snapshot_id)
    raw = {"rating": "Hold", "confidence": .4, "investment_thesis": "Limited coverage.",
           "executive_summary": "The outlook remains uncertain.", "risks": ["Coverage gaps."],
           "invalidation_conditions": ["If new evidence changes the outlook."],
           "report_contract_version": "2.0", "summary_evidence": {
               "claim": "The outlook remains uncertain.", "snapshot_ids": [sid]},
           "evidence_claims": [{"claim": text, "snapshot_ids": [sid]} for text in (
               "Limited coverage.", "Coverage gaps.", "If new evidence changes the outlook.")]}
    if mutation == "same_text":
        raw["executive_summary"] = raw["summary_evidence"]["claim"] = raw["investment_thesis"]
    elif mutation == "unknown":
        raw["summary_evidence"]["snapshot_ids"] = [str(uuid4())]
    elif mutation == "missing":
        raw.pop("summary_evidence")
    elif mutation == "version":
        raw["report_contract_version"] = "3.0"
    elif mutation == "parity":
        raw["summary_evidence"]["claim"] = "An unrelated conclusion."
    before = copy.deepcopy(raw)

    class Graph:
        def __init__(self, **kwargs):
            pass

        def propagate_snapshots(self, *args, **kwargs):
            return {"structured_decision": raw}, "Hold"

    result = AnalysisEngine(graph_factory=Graph, base_config={"output_language": "English"}).analyze(
        AnalysisRequest(instrument=instrument, analysis_date=NOW.date(), selected_analysts=("market",),
                        snapshot_context=inputs))
    assert raw == before
    assert result.final_state["structured_decision"] == before
    if mutation in {"valid", "same_text"}:
        assert result.decision_payload is not None
        assert not result.validation_issues
        assert result.material_claims[raw["executive_summary"]] == (manifest.snapshot_id,)
        graph = EvidenceGraphBuilder().build(run_id=uuid4(), as_of=NOW, snapshots=[manifest],
                                            material_claims=result.material_claims)
        summary = next(claim for claim in graph.claims if claim.claim == raw["executive_summary"])
        references = {ref.evidence_id: ref.snapshot_id for ref in graph.evidence}
        assert [references[identity] for identity in summary.evidence_ids] == [manifest.snapshot_id]
    else:
        assert result.decision_payload is None
        assert result.validation_issues
        assert result.material_claims == {}
        if mutation == "unknown":
            assert result.validation_issues == ("unknown_snapshot_reference",)
