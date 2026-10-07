"""Actual bounded financial node with explicit V2 input; no paid SDK calls."""

import copy
import json
from types import SimpleNamespace
from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage

from tests.test_summary_provenance_v2 import _draft
from tradingagents.agents.utils.financial_validation import create_financial_validation
from tradingagents.agents.utils.report_compiler import compile_report_v2
from tradingagents.platform.analysis.market_facts import SnapshotMarketFacts


@pytest.mark.parametrize("draft_input", [False, True])
@pytest.mark.parametrize("mutation", ["valid", "downgrade", "factual_cause", "conditional"])
def test_v2_bounded_review_preserves_summary_sources_and_rejects_downgrade(draft_input, mutation):
    draft, prices = _draft()
    if mutation in {"factual_cause", "conditional"}:
        text = "Tax-loss selling explains the latest decline." if mutation == "factual_cause" else (
            "Tax-loss selling could explain the decline; this is unverified.")
        draft["executive_summary"] = draft["summary_evidence"]["claim"] = text
    raw = draft if draft_input else compile_report_v2(
        draft, {prices["snapshot_id"]: SnapshotMarketFacts(prices)}).model_dump(mode="json")
    before = copy.deepcopy(raw)
    response = copy.deepcopy(raw)
    if mutation == "downgrade":
        response.pop("report_contract_version")
        response.pop("summary_evidence")
    calls = []

    class Model:
        def with_structured_output(self, schema):
            def invoke(prompt):
                calls.append(prompt)
                assert "COMPLETE executive_summary exactly" in prompt
                assert "unrelated available sources" in prompt
                return schema.model_validate(response)
            return SimpleNamespace(invoke=invoke)

        def invoke(self, prompt):
            calls.append(prompt)
            return AIMessage(content=json.dumps(response))

    news = {"snapshot_id": str(uuid4()), "provenance": {"dataset": "news"},
            "data": {"headline": "Synthetic unrelated product announcement"}}
    reports = {"market": json.dumps([prices]), "news": json.dumps([news])}
    result = create_financial_validation(Model(), reports)({
        "structured_draft" if draft_input else "structured_decision": raw})
    assert raw == before
    assert result["rejected_structured_decision"] == before
    if mutation in {"downgrade", "factual_cause"}:
        assert len(calls) == 2  # Original structured attempt + one repair only.
        assert result["structured_decision"] is None
        assert result["final_trade_decision"].startswith("UNVALIDATED RESEARCH")
    else:
        assert len(calls) == 1
        accepted = result["structured_decision"]
        assert accepted["report_contract_version"] == "2.0"
        assert accepted["summary_evidence"]["claim"] == accepted["executive_summary"]
        assert accepted["summary_evidence"]["snapshot_ids"] == before["summary_evidence"]["snapshot_ids"]
        assert prices["snapshot_id"] not in result["final_trade_decision"]
