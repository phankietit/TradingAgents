import hashlib
import json
from datetime import timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage

from tests.test_analysis_engine import _instrument
from tests.test_risk_engine import NOW
from tradingagents.contracts import SnapshotManifest
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph import trading_graph
from tradingagents.platform.analysis import AnalysisEngine, AnalysisRequest
from tradingagents.platform.analysis.snapshots import AnalysisSnapshot, SnapshotAnalysisContext


def context(instrument):
    payload = json.dumps({"close": 100, "source_note": "fixture immutable price"})
    source = AnalysisSnapshot(manifest=SnapshotManifest(
        snapshot_id=uuid4(), instrument_id=instrument.instrument_id, dataset="daily_prices",
        vendor="fixture", as_of=NOW, retrieved_at=NOW, source_end=NOW,
        content_hash="sha256:" + hashlib.sha256(payload.encode()).hexdigest(), quality_status="OK",
    ), payload=payload)
    return SnapshotAnalysisContext(as_of=NOW, by_analyst={"market": (source,)}, source_max_age_seconds={"market": 0})


def test_real_graph_snapshot_path_has_no_live_tools_memory_or_legacy_writes(tmp_path, monkeypatch):
    calls = []

    class Model:
        def invoke(self, prompt):
            calls.append(prompt)
            return AIMessage(content="Fixture analysis of supplied snapshot; risk remains uncertain.")

        def with_structured_output(self, schema):
            values = {
                "ResearchPlan": {"recommendation": "Hold", "rationale": "Snapshot evidence", "strategic_actions": "Review"},
                "TraderProposal": {"action": "Hold", "reasoning": "Research only"},
                "PortfolioDecision": {"rating": "Hold", "executive_summary": "Research only",
                    "investment_thesis": "Snapshot thesis", "confidence": .5,
                    "risks": ["Coverage risk"], "invalidation_conditions": ["New information"]},
            }
            return SimpleNamespace(invoke=lambda prompt: schema.model_validate(values[schema.__name__]))

    model = Model()
    monkeypatch.setattr(trading_graph, "create_llm_client", lambda **kwargs: SimpleNamespace(get_llm=lambda: model))

    def forbidden(*args, **kwargs):
        pytest.fail("snapshot path accessed legacy tools/memory/writes")

    monkeypatch.setattr(trading_graph, "TradingMemoryLog", forbidden)
    for name in ("_create_tool_nodes", "resolve_instrument_context", "_resolve_pending_entries",
                 "record_decision", "_log_state", "begin_checkpoint"):
        monkeypatch.setattr(trading_graph.TradingAgentsGraph, name, forbidden)
    instrument = _instrument()
    inputs = context(instrument)
    config = {**DEFAULT_CONFIG, "data_cache_dir": str(tmp_path / "cache"),
              "results_dir": str(tmp_path / "reports"), "max_debate_rounds": 1,
              "max_risk_discuss_rounds": 1}
    result = AnalysisEngine(base_config=config).analyze(AnalysisRequest(
        instrument=instrument, analysis_date=NOW.date(), selected_analysts=("market",),
        snapshot_context=inputs))
    assert result.decision_payload.thesis == "Snapshot thesis"
    assert result.narrative_signal == "Hold"
    assert "fixture immutable price" in calls[0][1].content
    assert str(inputs.by_analyst["market"][0].manifest.snapshot_id) in calls[0][1].content
    assert list((tmp_path / "reports").iterdir()) == []


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


def test_snapshot_freshness_is_explicit_and_enforced():
    instrument = _instrument()
    inputs = context(instrument).model_copy(update={"as_of": NOW + timedelta(seconds=1)})
    with pytest.raises(ValueError, match="stale"):
        inputs.reports(instrument.instrument_id, ("market",))
    inputs = inputs.model_copy(update={"source_max_age_seconds": {}})
    with pytest.raises(ValueError, match="freshness"):
        inputs.reports(instrument.instrument_id, ("market",))
