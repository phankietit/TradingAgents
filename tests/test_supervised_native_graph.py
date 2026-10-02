"""Original native LangGraph through spawn; synthetic models, no provider calls."""

from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from langchain_core.messages import AIMessage

from tests.test_analysis_engine import _instrument
from tests.test_risk_engine import NOW
from tests.test_snapshot_analysis import context
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph import trading_graph
from tradingagents.platform.analysis import AnalysisEngine, AnalysisRequest
from tradingagents.platform.analysis.observer import STAGES, ResearchObserver
from tradingagents.platform.analysis.snapshots import AnalysisSnapshot
from tradingagents.platform.analysis.supervision import SupervisedAnalysisEngine


class NativeFixtureEngine:
    def __init__(self, *, base_config=None):
        self.config = base_config

    def analyze(self, request):
        source_id = str(request.snapshot_context.by_analyst["market"][0].manifest.snapshot_id)
        options = []

        class Model:
            def invoke(self, prompt):
                return AIMessage(content="Synthetic analysis; coverage remains uncertain.")

            def with_structured_output(self, schema):
                claims = [{"claim": claim, "snapshot_ids": [source_id]}
                          for claim in ("Snapshot thesis", "Coverage risk", "New information")]
                values = {
                    "SentimentReport": {"overall_band": "Mixed", "overall_score": 5,
                        "confidence": "low", "narrative": "Synthetic limited source sentiment."},
                    "ResearchPlan": {"recommendation": "Hold", "rationale": "Snapshot evidence",
                        "strategic_actions": "Review"},
                    "TraderProposal": {"action": "Hold", "reasoning": "Research only"},
                    "PortfolioDecision": {"rating": "Hold", "executive_summary": "Research only",
                        "investment_thesis": "Snapshot thesis", "confidence": .5,
                        "risks": ["Coverage risk"], "invalidation_conditions": ["New information"],
                        "evidence_claims": claims},
                }
                if "quantity_bindings" in schema.model_fields:
                    payload = values["PortfolioDecision"]
                    payload.pop("evidence_claims")
                    payload.update(investment_thesis=[claims[0]], risks=[claims[1]],
                                   invalidation_conditions=[claims[2]])
                return SimpleNamespace(invoke=lambda prompt: schema.model_validate(values[schema.__name__]))

        def client(**kwargs):
            options.append(kwargs)
            return SimpleNamespace(get_llm=lambda: Model())

        def forbidden(*args, **kwargs):
            raise AssertionError("native snapshot graph accessed a legacy write/tool/memory path")

        with ExitStack() as patches:
            patches.enter_context(patch.object(trading_graph, "create_llm_client", client))
            patches.enter_context(patch.object(trading_graph, "TradingMemoryLog", forbidden))
            for name in ("_create_tool_nodes", "resolve_instrument_context", "_resolve_pending_entries",
                         "record_decision", "_log_state", "begin_checkpoint"):
                patches.enter_context(patch.object(trading_graph.TradingAgentsGraph, name, forbidden))
            result = AnalysisEngine(base_config=self.config).analyze(request)
        assert all(item["timeout"] == 600 and item["max_retries"] == 1 for item in options)
        return result


def test_all_fourteen_native_stages_survive_spawn_bridge_and_original_gates(tmp_path):
    instrument = _instrument()
    inputs = context(instrument)
    analysts = ("market", "social", "news", "fundamentals")
    original = inputs.by_analyst["market"][0]
    extras = {role: (AnalysisSnapshot(manifest=original.manifest.model_copy(update={
        "snapshot_id": uuid4(), "dataset": role}), payload=original.payload),)
        for role in analysts if role != "market"}
    inputs = inputs.model_copy(update={"by_analyst": {**inputs.by_analyst, **extras},
                                      "source_max_age_seconds": dict.fromkeys(analysts, 0)})
    captures, events = [], []
    observer = ResearchObserver(check_cancelled=lambda: None, emit=lambda *args: events.append(args),
        max_seconds=60, save_stage=lambda stage, outputs: captures.append((stage, outputs)) or uuid4())
    config = {**DEFAULT_CONFIG, "data_cache_dir": str(tmp_path / "cache"),
        "results_dir": str(tmp_path / "reports"), "max_debate_rounds": 1,
        "max_risk_discuss_rounds": 1, "output_language": "English"}
    result = SupervisedAnalysisEngine(base_config=config, engine_factory=NativeFixtureEngine).analyze(
        AnalysisRequest(instrument=instrument, analysis_date=NOW.date(), selected_analysts=analysts,
                        snapshot_context=inputs, execution_observer=observer))
    expected = ["Market Analyst", "Sentiment Analyst", "News Analyst", "Fundamentals Analyst",
        "Bull Researcher", "Bear Researcher", "Research Manager", "Trader", "Aggressive Analyst",
        "Conservative Analyst", "Neutral Analyst", "Portfolio Manager", "Financial validation",
        "Report presentation"]
    assert observer.completed == expected and set(expected) == STAGES
    assert [payload["stage"] for kind, payload in events if kind == "stage.completed"] == expected
    assert result.selected_analysts == analysts
    assert result.decision_payload.thesis == "Snapshot thesis"
    assert result.narrative_signal == "Hold"
    assert observer.receipt()["supervision_mode"] == "spawned_process"
    assert observer.receipt()["usage"]["status"] == "incomplete"  # Fake model, not provider usage proof.
    assert "messages" not in result.final_state
    assert all("messages" not in outputs for _, outputs in captures)
    assert list((tmp_path / "reports").iterdir()) == []
