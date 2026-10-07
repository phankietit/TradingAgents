import hashlib
import json
from datetime import timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage

from tests.summary_fixtures import summary_response
from tests.test_analysis_engine import _instrument
from tests.test_risk_engine import NOW
from tradingagents.contracts import SnapshotManifest
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph import trading_graph
from tradingagents.platform.analysis import AnalysisEngine, AnalysisRequest
from tradingagents.platform.analysis.observer import ResearchObserver
from tradingagents.platform.analysis.snapshots import AnalysisSnapshot, SnapshotAnalysisContext
from tradingagents.platform.analysis.stage_records import stage_sections


def context(instrument):
    payload = json.dumps({"close": 100, "source_note": "fixture immutable price"})
    source = AnalysisSnapshot(manifest=SnapshotManifest(
        snapshot_id=uuid4(), instrument_id=instrument.instrument_id, dataset="daily_prices",
        vendor="fixture", as_of=NOW, retrieved_at=NOW, source_end=NOW,
        content_hash="sha256:" + hashlib.sha256(payload.encode()).hexdigest(), quality_status="OK",
    ), payload=payload)
    return SnapshotAnalysisContext(as_of=NOW, by_analyst={"market": (source,)}, source_max_age_seconds={"market": 0})


@pytest.mark.parametrize("role", ["news", "social", "fundamentals"])
def test_price_snapshot_cannot_masquerade_as_other_analyst_evidence(role):
    instrument = _instrument()
    original = context(instrument)
    mismatched = SnapshotAnalysisContext(as_of=NOW, by_analyst={role: original.by_analyst["market"]},
        source_max_age_seconds={role: 0})
    with pytest.raises(ValueError, match="dataset is not supported"):
        mismatched.reports(instrument.instrument_id, (role,))


@pytest.mark.parametrize("all_roles", [False, True])
@pytest.mark.parametrize("capture_stages", [False, True])
def test_real_graph_snapshot_path_has_no_live_tools_memory_or_legacy_writes(tmp_path, monkeypatch, all_roles, capture_stages):
    calls = []
    structured_prompts = []

    class Model:
        def invoke(self, prompt):
            calls.append(prompt)
            return AIMessage(content="Fixture analysis of supplied snapshot; risk remains uncertain.")

        def with_structured_output(self, schema):
            values = {
                "SentimentReport": {"overall_band": "Mixed", "overall_score": 5, "confidence": "low",
                                    "narrative": "Fixture source sentiment; limited sample, not a market conclusion."},
                "ResearchPlan": {"recommendation": "Hold", "rationale": "Snapshot evidence", "strategic_actions": "Review"},
                "TraderProposal": {"action": "Hold", "reasoning": "Research only"},
                "PortfolioDecision": {"rating": "Hold", "executive_summary": "Research only",
                    "investment_thesis": "Snapshot thesis", "confidence": .5,
                        "risks": ["Coverage risk"], "invalidation_conditions": ["New information"],
                        "evidence_claims": [{"claim": claim, "snapshot_ids": [str(inputs.by_analyst["market"][0].manifest.snapshot_id)]}
                            for claim in ("Snapshot thesis", "Coverage risk", "New information")]},
            }
            if "quantity_bindings" in schema.model_fields:
                payload = values["PortfolioDecision"]
                claims = payload.pop("evidence_claims")
                payload["investment_thesis"] = [claims[0]]
                payload["risks"] = [claims[1]]
                payload["invalidation_conditions"] = [claims[2]]
            if "report_contract_version" in schema.model_fields:
                values["PortfolioDecision"] = summary_response(values["PortfolioDecision"],
                    [str(inputs.by_analyst["market"][0].manifest.snapshot_id)])
            return SimpleNamespace(invoke=lambda prompt: (structured_prompts.append(prompt)
                or schema.model_validate(values[schema.__name__])))

    model = Model()
    client_options = []

    def client(**kwargs):
        client_options.append(kwargs)
        return SimpleNamespace(get_llm=lambda: model)

    monkeypatch.setattr(trading_graph, "create_llm_client", client)

    def forbidden(*args, **kwargs):
        pytest.fail("snapshot path accessed legacy tools/memory/writes")

    monkeypatch.setattr(trading_graph, "TradingMemoryLog", forbidden)
    for name in ("_create_tool_nodes", "resolve_instrument_context", "_resolve_pending_entries",
                 "record_decision", "_log_state", "begin_checkpoint"):
        monkeypatch.setattr(trading_graph.TradingAgentsGraph, name, forbidden)
    instrument = _instrument()
    inputs = context(instrument)
    analysts = ("market", "social", "news", "fundamentals") if all_roles else ("market",)
    if all_roles:
        original = inputs.by_analyst["market"][0]
        extras = {role: (AnalysisSnapshot(manifest=original.manifest.model_copy(update={
            "snapshot_id": uuid4(), "dataset": role}), payload=original.payload),)
            for role in analysts if role != "market"}
        inputs = inputs.model_copy(update={"by_analyst": {**inputs.by_analyst, **extras},
                                          "source_max_age_seconds": dict.fromkeys(analysts, 0)})
    events = []
    captures = []

    def capture(stage, outputs):
        sections = stage_sections(stage, outputs)
        if sections:
            captures.append((stage, sections))
            return uuid4()
        return None

    observer = ResearchObserver(check_cancelled=lambda: None, emit=lambda kind, payload: events.append((kind, payload)),
        save_stage=capture if capture_stages else None)
    config = {**DEFAULT_CONFIG, "data_cache_dir": str(tmp_path / "cache"),
              "results_dir": str(tmp_path / "reports"), "max_debate_rounds": 1,
              "max_risk_discuss_rounds": 1, "output_language": "English"}
    result = AnalysisEngine(base_config=config).analyze(AnalysisRequest(
        instrument=instrument, analysis_date=NOW.date(), selected_analysts=analysts,
        snapshot_context=inputs, execution_observer=observer))
    assert result.decision_payload.thesis == "Snapshot thesis"
    assert result.narrative_signal == "Hold"
    assert "EDITORIAL CONTRACT" in structured_prompts[-2]
    assert "diễn biến giá" in structured_prompts[-2]
    assert "in structured references only" in structured_prompts[-2]
    assert "percentage denominator" in structured_prompts[-1]
    assert all(options["timeout"] == 600 for options in client_options)
    assert all(options["max_retries"] == 1 for options in client_options)
    assert "fixture immutable price" in calls[0][1].content
    assert str(inputs.by_analyst["market"][0].manifest.snapshot_id) in calls[0][1].content
    assert list((tmp_path / "reports").iterdir()) == []
    completed = [payload["stage"] for kind, payload in events if kind == "stage.completed"]
    expected_analysts = ["Market Analyst", "Sentiment Analyst", "News Analyst", "Fundamentals Analyst"] if all_roles else ["Market Analyst"]
    assert completed == [*expected_analysts, "Bull Researcher", "Bear Researcher", "Research Manager", "Trader",
                         "Aggressive Analyst", "Conservative Analyst", "Neutral Analyst", "Portfolio Manager", "Financial validation", "Report presentation"]
    if capture_stages:
        assert [stage for stage, _ in captures] == completed[:-1]  # English-only presentation has no translated fragment.
        assert all("research_artifact_id" in payload for kind, payload in events
                   if kind == "stage.completed" and payload["stage"] != "Report presentation")
        assert all("messages" not in sections for _, sections in captures)
    else:
        assert all(set(payload) == {"stage"} for _, payload in events)
    assert observer.receipt()["usage"]["status"] == "incomplete"  # fake model has no provider usage


@pytest.mark.parametrize("mutation", ["hash", "future", "owner_instrument", "roles", "missing_source_end"])
def test_snapshot_input_rejects_invalid_provenance(mutation):
    instrument = _instrument()
    inputs = context(instrument)
    source = inputs.by_analyst["market"][0]
    if mutation == "hash":
        source = source.model_copy(update={"payload": "{}"})
    elif mutation == "future":
        source = source.model_copy(update={"manifest": source.manifest.model_copy(
            update={"retrieved_at": NOW + timedelta(days=1)})})
    elif mutation == "owner_instrument":
        source = source.model_copy(update={"manifest": source.manifest.model_copy(
            update={"instrument_id": uuid4()})})
    elif mutation == "missing_source_end":
        source = source.model_copy(update={"manifest": source.manifest.model_copy(update={"source_end": None})})
    inputs = inputs.model_copy(update={"by_analyst": {"news" if mutation == "roles" else "market": (source,)}})
    with pytest.raises(ValueError):
        inputs.reports(instrument.instrument_id, ("market",))


@pytest.mark.parametrize("phase,blocked", [("repair", True), ("structured", False)])
def test_failed_upstream_schema_repair_cannot_be_hidden_by_valid_final_report(phase, blocked):
    instrument = _instrument()
    inputs = context(instrument)
    sid = str(inputs.by_analyst["market"][0].manifest.snapshot_id)
    class Graph:
        def __init__(self, **kwargs):
            pass
        def propagate_snapshots(self, *args, **kwargs):
            return {"structured_decision": {"rating":"Hold", "confidence":.5,
                "executive_summary":"Limited research", "investment_thesis":"Thesis",
                "report_contract_version":"2.0", "summary_evidence":{"claim":"Limited research", "snapshot_ids":[sid]},
                "risks":["Risk"], "invalidation_conditions":["Conditional change"],
                "evidence_claims":[{"claim":text,"snapshot_ids":[sid]} for text in ("Thesis","Risk","Conditional change")]},
                "structured_diagnostics":[{"agent":"Research Manager","phase":phase,"error_type":"ValueError"}]}, "Hold"
    result = AnalysisEngine(graph_factory=Graph, base_config={"output_language":"English"}).analyze(
        AnalysisRequest(instrument=instrument, analysis_date=NOW.date(), selected_analysts=("market",), snapshot_context=inputs))
    assert (result.decision_payload is None) is blocked
    assert ("upstream_structured_output_invalid" in result.validation_issues) is blocked


def test_snapshot_freshness_is_explicit_and_enforced():
    instrument = _instrument()
    inputs = context(instrument).model_copy(update={"as_of": NOW + timedelta(seconds=1)})
    with pytest.raises(ValueError, match="stale"):
        inputs.reports(instrument.instrument_id, ("market",))
    inputs = inputs.model_copy(update={"source_max_age_seconds": {}})
    with pytest.raises(ValueError, match="freshness"):
        inputs.reports(instrument.instrument_id, ("market",))
