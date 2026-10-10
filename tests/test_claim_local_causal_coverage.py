"""Claim-local coverage, not general financial entailment or live model proof."""

import json
from types import SimpleNamespace
from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage

from tests.summary_fixtures import summary_response
from tests.test_financial_validation_stage import candidate
from tests.test_snapshot_market_facts import source
from tradingagents.agents.utils.financial_validation import create_financial_validation


def _review(claim, *, include_news, cite_news=False):
    prices = source()
    news = {"snapshot_id": str(uuid4()), "provenance": {"dataset": "news"},
            "data": {"headline": "Synthetic unrelated product announcement"}}
    raw = candidate(prices["snapshot_id"])
    citations = [prices["snapshot_id"]]
    if cite_news:
        citations.append(news["snapshot_id"])
    raw["investment_thesis"] += " " + claim
    raw["evidence_claims"][0] = {"claim": raw["investment_thesis"], "snapshot_ids": citations}
    before = json.dumps(raw, sort_keys=True)
    reports = {"market": json.dumps([prices])}
    if include_news:
        reports["news"] = json.dumps([news])
    calls = []

    class Model:
        def with_structured_output(self, schema):
            def invoke(prompt):
                calls.append(prompt)
                return schema.model_validate(summary_response(raw, [prices["snapshot_id"]]))
            return SimpleNamespace(invoke=invoke)

        def invoke(self, prompt):
            calls.append(prompt)
            return AIMessage(content=json.dumps(summary_response(raw, [prices["snapshot_id"]])))

    result = create_financial_validation(Model(), reports)({"structured_decision": raw})
    assert json.dumps(raw, sort_keys=True) == before
    assert result["rejected_structured_decision"] == raw
    assert 1 <= len(calls) <= 2  # Existing one structured call + one repair only.
    return result


@pytest.mark.parametrize("include_news", [False, True])
def test_price_cited_evidence_cannot_hide_factual_external_cause(include_news):
    result = _review("Tax-loss selling explains the latest decline.", include_news=include_news)
    assert result["structured_decision"] is None
    assert result["final_trade_decision"].startswith("UNVALIDATED RESEARCH")


@pytest.mark.parametrize("include_news", [False, True])
def test_price_cited_unverified_scenario_preserves_original_review(include_news):
    result = _review("Tax-loss selling could explain the decline; this is unverified.",
                     include_news=include_news)
    assert result["structured_decision"] is not None


def test_mixed_source_noncausal_observation_preserves_original_review():
    # Genuine nonprice coverage is not rejected merely because prices also exist.
    # This still does not certify general mixed-source semantic entailment.
    result = _review("The news snapshot adds a non-exhaustive headline sample.",
                     include_news=True, cite_news=True)
    assert result["structured_decision"] is not None
