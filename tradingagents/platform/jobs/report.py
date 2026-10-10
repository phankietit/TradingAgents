"""Shared existing report projection; no models, lifecycle or policy authority."""

import json
from uuid import uuid5

from tradingagents.platform.analysis.market_facts import SnapshotMarketFacts
from tradingagents.platform.analysis.profiles import resolve_analysis_profile


def build_run_report(run, result, *, instrument, snapshot_context, observer):
    # Preserve the ordinary handler's projection and disclosures exactly.
    from .analysis import publication_warning

    raw = result.decision_payload.model_dump(mode="json") if result.decision_payload else {}
    market_sources = [SnapshotMarketFacts(source)
        for source in json.loads(snapshot_context.reports(run.instrument_id, run.selected_analysts).get("market", "[]"))
        if source["provenance"]["dataset"] == "ohlcv.daily"] if snapshot_context else []
    return {
        "run_id": str(run.run_id), "decision_id": str(uuid5(run.run_id, "decision-v1")),
        "profile": result.profile_name, "reference_only": result.reference_only,
        "selected_analysts": result.selected_analysts,
        "narrative": publication_warning(snapshot_context)
            + result.final_state.get("final_trade_decision", result.narrative_signal),
        "structured_narrative": raw or None,
        "snapshot_attestation": "PASS" if snapshot_context is not None else "UNVERIFIED",
        "report_language": run.report_language,
        "publication_warning": publication_warning(snapshot_context),
        "structured_diagnostics": result.final_state.get("structured_diagnostics", []),
        "execution": observer.receipt(),
        "source_quality": "verified" if snapshot_context is not None else "unverified",
        "research_quality": "structured" if raw else "unvalidated",
        "validation_issues": list(result.validation_issues),
        "quantitative_references": [item.model_dump(mode="json") for item in result.quantitative_references],
        "localized_report": (result.final_state.get("structured_decision") or {}).get("localized_report"),
        "rejected_structured_decision": result.final_state.get("rejected_structured_decision"),
        "structured_draft": result.final_state.get("structured_draft"),
        "canonical_research": result.final_state.get("structured_decision"),
        "coverage": {"selected": list(run.selected_analysts),
                     "expected": list(resolve_analysis_profile(instrument).allowed_analysts),
                     "missing": [role for role in resolve_analysis_profile(instrument).allowed_analysts if role not in run.selected_analysts],
                     "all_profile_roles_present": set(run.selected_analysts) == set(resolve_analysis_profile(instrument).allowed_analysts)},
        "market_facts": [source.summary() for source in market_sources],
        "market_history": [source.chart() for source in market_sources],
        "research_sections": {key: result.final_state[key] for key in (
            "market_report", "sentiment_report", "news_report", "fundamentals_report",
            "investment_plan", "trader_investment_plan")
            if isinstance(result.final_state.get(key), str)},
        "debate_sections": {key: result.final_state.get(key, {}).get("history", "")
            for key in ("investment_debate_state", "risk_debate_state")},
    }
