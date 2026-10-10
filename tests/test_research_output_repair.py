import json
from types import SimpleNamespace

import pytest
from langchain_core.messages import AIMessage

from tradingagents.agents.research_schemas import SnapshotPortfolioDecision, SnapshotTraderProposal
from tradingagents.agents.schemas import render_pm_decision
from tradingagents.agents.utils.structured import invoke_structured_or_freetext


def valid():
    return {"rating": "Hold", "investment_thesis": "Limited snapshot evidence", "executive_summary": "Research only",
            "confidence": .4, "risks": ["Coverage uncertainty"], "invalidation_conditions": ["If the observed trend changes"]}


@pytest.mark.parametrize("field", ["confidence", "risks", "invalidation_conditions"])
def test_platform_schema_requires_the_same_fields_as_consumer(field):
    payload = valid()
    del payload[field]
    with pytest.raises(ValueError):
        SnapshotPortfolioDecision.model_validate(payload)


def test_trader_cannot_author_position_size():
    with pytest.raises(ValueError):
        SnapshotTraderProposal(action="Buy", reasoning="Research", position_sizing="5% of portfolio")


def test_missing_tool_call_has_one_strict_format_repair():
    prompts, captured, diagnostics = [], [], []
    plain = SimpleNamespace(invoke=lambda prompt: (prompts.append(prompt) or AIMessage(content=json.dumps(valid()))))
    result = invoke_structured_or_freetext(SimpleNamespace(invoke=lambda _: None), plain, "Evidence context",
        render_pm_decision, "Portfolio Manager", repair_schema=SnapshotPortfolioDecision,
        on_structured=captured.append, diagnostics=diagnostics)
    assert len(prompts) == len(captured) == 1
    assert "Evidence context" in prompts[0] and "FORMAT REPAIR" in prompts[0]
    assert "## Risks" in result
    assert diagnostics[0]["error_type"] == "ValueError"


def test_invalid_repair_remains_unvalidated_and_diagnostics_exclude_values():
    captured, diagnostics = [], []
    secret = "sk-private-sensitive-value"
    result = invoke_structured_or_freetext(SimpleNamespace(invoke=lambda _: None),
        SimpleNamespace(invoke=lambda _: AIMessage(content=json.dumps({**valid(), "confidence": secret}))),
        "Evidence", render_pm_decision, "Portfolio Manager", repair_schema=SnapshotPortfolioDecision,
        on_structured=captured.append, diagnostics=diagnostics)
    assert result.startswith("UNVALIDATED RESEARCH") and captured == []
    assert secret not in json.dumps(diagnostics)
    assert diagnostics[-1]["fields"] == [{"field": "confidence", "code": "float_parsing"}]


def test_transport_failure_does_not_spend_a_schema_repair_call():
    def unavailable(_):
        raise ConnectionError("private provider transport detail")

    def forbidden(_):
        pytest.fail("transport errors must not invoke format repair")

    with pytest.raises(ConnectionError):
        invoke_structured_or_freetext(SimpleNamespace(invoke=unavailable), SimpleNamespace(invoke=forbidden),
            "Evidence", render_pm_decision, "Portfolio Manager", repair_schema=SnapshotPortfolioDecision)


def test_repair_receives_safe_field_feedback_and_does_not_leak_extra_keys():
    secret = "sk-private-sensitive-field-name"
    prompts, diagnostics = [], []
    def broken(_):
        SnapshotPortfolioDecision.model_validate({**valid(), secret: "private", "confidence": "bad"})
    invoke_structured_or_freetext(SimpleNamespace(invoke=broken),
        SimpleNamespace(invoke=lambda prompt: (prompts.append(prompt) or AIMessage(content=json.dumps(valid())))),
        "Evidence", render_pm_decision, "Portfolio Manager", repair_schema=SnapshotPortfolioDecision,
        diagnostics=diagnostics)
    assert "confidence" in prompts[0] and "previous attempt failed" in prompts[0]
    assert secret not in json.dumps(diagnostics) and secret not in prompts[0]
