"""Actual graph + owner storage, synthetic SDK/data; not live financial/MT QA."""

import json
from datetime import timedelta
from types import SimpleNamespace

import pytest
from langchain_core.messages import AIMessage

from tests.summary_fixtures import summary_response
from tests.test_platform_fred import NOW
from tests.test_platform_sec import collect as collect_sec, document, fact
from tests.test_platform_social import collect as collect_social
from tests.test_price_preparation import AAPL, metadata, price_frame
from tests.test_snapshot_macro_facts import macro_draft, macro_source
from tradingagents.dataflows.platform_news import collect_yahoo_news
from tradingagents.dataflows.platform_prices import normalize_yahoo
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph import trading_graph
from tradingagents.platform.analysis import AnalysisEngine, AnalysisRequest
from tradingagents.platform.analysis.observer import ResearchObserver
from tradingagents.platform.analysis.snapshots import load_snapshot_context
from tradingagents.platform.artifacts import ArtifactService, LocalArtifactStore
from tradingagents.platform.auth import OwnerAuth
from tradingagents.platform.jobs.analysis import publication_warning
from tradingagents.platform.market_data import TimeSeriesSnapshotService
from tradingagents.platform.market_data.macro import MacroSnapshotService
from tradingagents.platform.market_data.news import NewsSnapshotService
from tradingagents.platform.market_data.sec_facts import SecSnapshotService
from tradingagents.platform.market_data.social import SocialSnapshotService
from tradingagents.platform.persistence import Database, PlatformRepository, upgrade_database


@pytest.mark.parametrize("language", ["English", "Vietnamese", "English and Vietnamese"])
@pytest.mark.parametrize("invalid_binding", [False, True])
@pytest.mark.parametrize("with_headlines", [False, True])
def test_real_graph_keeps_all_roles_rounds_validation_and_bilingual_macro_semantics(tmp_path, monkeypatch, language, invalid_binding, with_headlines):
    url = f"sqlite:///{tmp_path / 'macro-graph.db'}"
    upgrade_database(url)
    database = Database(url)
    store = LocalArtifactStore(tmp_path / "artifacts")
    macro = macro_source()
    raw, _ = macro_draft(macro)
    raw = summary_response(raw, [macro["snapshot_id"]])
    if invalid_binding:
        raw["quantity_bindings"][0]["fact_id"] = raw["quantity_bindings"][0]["fact_id"].replace("DGS10", "CPIAUCSL")
    source_ids = {}
    with database.session() as session:
        owner = OwnerAuth(session).bootstrap_owner("macro-graph@example.com", "synthetic-qa-password").owner_id
        repository = PlatformRepository(session)
        repository.add_instrument(AAPL)
        artifacts = ArtifactService(store, repository)
        # Real normalization with original five-year XNAS session requirements.
        prices = normalize_yahoo(AAPL, price_frame(AAPL, NOW), metadata(AAPL), now=NOW)
        assert len(prices.bars) > 1200
        source_ids["market"] = (TimeSeriesSnapshotService(repository, artifacts).persist(
            owner_id=owner, series=prices, vendor="fixture", retrieved_at=NOW).snapshot_id,)
        from tradingagents.dataflows.platform_fred import MacroCollection
        source_ids["news"] = (MacroSnapshotService(repository, artifacts).persist(owner_id=owner,
            collection=MacroCollection.model_validate(macro["data"]),
            snapshot_id=macro["provenance"]["snapshot_id"]).snapshot_id,)
        if with_headlines:
            news = collect_yahoo_news(AAPL, clock=lambda: NOW, fetch=lambda *_: [{"content": {
                "title": "Synthetic headline distinct from FRED",
                "summary": "Synthetic non-exhaustive source, not macro coverage.",
                "provider": {"displayName": "Fixture publisher"},
                "canonicalUrl": {"url": "https://example.com/news/macro-fixture"},
                "pubDate": (NOW - timedelta(hours=2)).isoformat()}}])
            source_ids["news"] += (NewsSnapshotService(repository, artifacts).persist(
                owner_id=owner, collection=news).snapshot_id,)
        sec = collect_sec(document([fact(100_000_000, "2025-11-01")]), now=NOW)
        source_ids["fundamentals"] = (SecSnapshotService(repository, artifacts).persist(
            owner_id=owner, collection=sec).snapshot_id,)
        # Actual structured parsing/storage over explicit synthetic original-feed bytes.
        source_ids["social"] = tuple(SocialSnapshotService(repository, artifacts).persist(
            owner_id=owner, collection=collect_social(vendor=vendor)).snapshot_id
            for vendor in ("stocktwits", "reddit"))
    analysts = ("market", "social", "news", "fundamentals")
    run = SimpleNamespace(owner_id=owner, instrument_id=AAPL.instrument_id,
        snapshot_ids=tuple(sid for ids in source_ids.values() for sid in ids),
        analysis_as_of=NOW, selected_analysts=analysts,
        decision_inputs=SimpleNamespace(source_max_age_seconds={"market": 86400, "news": 86400,
            "social": 86400, "fundamentals": 365 * 86400}))
    with database.session() as session:
        inputs = load_snapshot_context(ArtifactService(store, PlatformRepository(session)), run, source_ids)
    warnings = publication_warning(inputs)
    assert "MACRO COVERAGE" in warnings
    assert ("HEADLINE COVERAGE" not in warnings) is with_headlines
    assert ("NEWS COVERAGE" in warnings) is with_headlines
    calls, structured, events = [], [], []

    class Model:
        def bind_tools(self, tools):
            return self
        def invoke(self, messages):
            calls.append(messages)
            if isinstance(messages, str):
                # Failed financial review's sole bounded JSON repair.
                return AIMessage(content=json.dumps(raw))
            return AIMessage(content="Synthetic evidence review; opposing case and coverage remain uncertain.")
        def with_structured_output(self, schema):
            def invoke(prompt):
                structured.append((schema.__name__, prompt))
                if schema.__name__ == "ReportTranslation":
                    rows = json.loads(prompt.split("<translation_blocks>\n")[1].split("\n</translation_blocks>")[0])
                    return schema(blocks=[{"block_id": row["block_id"], "vi": row["en"]} for row in rows])
                if schema.__name__ == "SentimentReport":
                    return schema(overall_band="Mixed", overall_score=5, confidence="low",
                        narrative="Synthetic fixture sentiment; not exhaustive social coverage.")
                if schema.__name__ == "ResearchPlan":
                    return schema(recommendation="Hold", rationale="Conditional research only.", strategic_actions="Review evidence.")
                if schema.__name__ == "TraderProposal":
                    return schema(action="Hold", reasoning="Conditional research, no sizing.")
                assert schema.__name__ == "PortfolioDecision"
                return schema.model_validate(raw)
            return SimpleNamespace(invoke=invoke)

    model = Model()
    monkeypatch.setattr(trading_graph, "create_llm_client", lambda **kwargs: SimpleNamespace(get_llm=lambda: model))

    def forbidden(*_, **kwargs):
        pytest.fail("Snapshot graph accessed live vendor, legacy memory or a legacy write")

    monkeypatch.setattr(trading_graph, "TradingMemoryLog", forbidden)
    for name in ("_create_tool_nodes", "resolve_instrument_context", "_resolve_pending_entries",
            "record_decision", "_log_state", "begin_checkpoint"):
        monkeypatch.setattr(trading_graph.TradingAgentsGraph, name, forbidden)
    import requests
    monkeypatch.setattr(requests.sessions.Session, "request", forbidden)
    observer = ResearchObserver(check_cancelled=lambda: None,
        emit=lambda kind, payload: events.append((kind, payload)))
    try:
        result = AnalysisEngine(base_config={**DEFAULT_CONFIG, "data_cache_dir": str(tmp_path / "cache"),
            "results_dir": str(tmp_path / "reports"), "max_debate_rounds": 2,
            "max_risk_discuss_rounds": 2, "output_language": language}).analyze(AnalysisRequest(
                instrument=AAPL, analysis_date=NOW.date(), selected_analysts=analysts,
                snapshot_context=inputs, execution_observer=observer))
        stages = [payload["stage"] for kind, payload in events if kind == "stage.completed"]
        assert stages == ["Market Analyst", "Sentiment Analyst", "News Analyst", "Fundamentals Analyst",
            "Bull Researcher", "Bear Researcher", "Bull Researcher", "Bear Researcher", "Research Manager", "Trader",
            "Aggressive Analyst", "Conservative Analyst", "Neutral Analyst",
            "Aggressive Analyst", "Conservative Analyst", "Neutral Analyst", "Portfolio Manager",
            "Financial validation", "Report presentation"]
        assert any("full_history_tool" in str(messages) and "get_snapshot_macro" in str(messages) for messages in calls)
        sentiment_prompt = str(dict(structured)["SentimentReport"])
        assert "Synthetic full retail opinion" in sentiment_prompt and "Complete discussion body" in sentiment_prompt
        assert "sample_count.unlabeled" in sentiment_prompt and "unlabeled is not Neutral" in sentiment_prompt
        assert all(str(sid) in sentiment_prompt for sid in source_ids["social"])
        if with_headlines:
            assert any("Synthetic headline distinct from FRED" in str(messages)
                and str(source_ids["news"][0]) in str(messages)
                and str(source_ids["news"][1]) in str(messages) for messages in calls)
        assert (result.decision_payload is None) is invalid_binding
        if invalid_binding:
            assert result.validation_issues and result.final_state["structured_decision"] is None
        else:
            assert result.quantitative_references[0].value == 10
            assert 'native unit "Percent"' in result.decision_payload.thesis
            assert "percentage-point" in dict(structured).get("PortfolioDecision", "") or "native" in dict(structured)["PortfolioDecision"]
            localized = result.final_state["structured_decision"].get("localized_report")
            if language != "English":
                assert "Chuỗi FRED" in localized["vi"] and "10.00" in localized["vi"]
            else:
                assert localized is None
        assert list((tmp_path / "reports").iterdir()) == []
    finally:
        database.dispose()
