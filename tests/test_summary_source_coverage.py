"""Red summary-citation regression; not live semantic/model acceptance."""

import json
from types import SimpleNamespace
from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage

from tests.test_financial_validation_stage import candidate
from tests.test_snapshot_market_facts import source
from tradingagents.agents.utils.financial_validation import create_financial_validation


def _summary_review(summary, *, include_news):
    prices = source()
    raw = candidate(prices["snapshot_id"])
    raw["executive_summary"] = summary
    before = json.dumps(raw, sort_keys=True)
    reports = {"market": json.dumps([prices])}
    if include_news:
        news = {"snapshot_id": str(uuid4()), "provenance": {"dataset": "news"},
                "data": {"headline": "Synthetic unrelated product announcement"}}
        reports["news"] = json.dumps([news])
    calls = []

    class Model:
        def with_structured_output(self, schema):
            def invoke(prompt):
                calls.append(prompt)
                return schema.model_validate(raw)
            return SimpleNamespace(invoke=invoke)

        def invoke(self, prompt):
            calls.append(prompt)
            return AIMessage(content=json.dumps(raw))

    result = create_financial_validation(Model(), reports)({"structured_decision": raw})
    assert json.dumps(raw, sort_keys=True) == before
    assert result["rejected_structured_decision"] == raw
    assert 1 <= len(calls) <= 2
    return result


@pytest.mark.parametrize("include_news", [False, True])
def test_uncited_factual_cause_in_summary_is_withheld(include_news):
    result = _summary_review("Tax-loss selling explains the latest decline.",
                             include_news=include_news)
    assert result["structured_decision"] is None
    assert result["final_trade_decision"].startswith("UNVALIDATED RESEARCH")


@pytest.mark.parametrize("include_news", [False, True])
def test_unverified_conditional_summary_stays_research_not_fact(include_news):
    result = _summary_review("Tax-loss selling could explain the decline; this is unverified.",
                             include_news=include_news)
    assert result["structured_decision"] is not None
