import json
from types import SimpleNamespace

import pytest
from langchain_core.messages import AIMessage

from tests.test_snapshot_market_facts import source
from tradingagents.agents.utils.financial_validation import create_financial_validation


def candidate(snapshot_id, *, incorrect=False):
    thesis = "Close $499.00 supports the trend. Coverage is price only."
    return {"rating":"Hold", "confidence":.4, "investment_thesis":thesis,
        "executive_summary":"Return 30.00%" if incorrect else "Trend remains uncertain.",
        "risks":["Opposing momentum"], "invalidation_conditions":["If the trend reverses"],
        "evidence_claims":[{"claim":text,"snapshot_ids":[snapshot_id]} for text in (thesis,"Opposing momentum","If the trend reverses")],
        "observed_numbers":[{"snapshot_id":snapshot_id,"fact_id":"latest.close","value":499,"decimal_places":2}]}


def test_valid_canonical_report_does_not_spend_an_extra_model_call():
    data = source()
    class NoCalls:
        def with_structured_output(self, _):
            pytest.fail("valid research must not invoke a repair")
    node = create_financial_validation(NoCalls(), {"market":json.dumps([data])})
    assert node({"structured_decision":candidate(data["snapshot_id"])}) == {}


def test_financial_repair_preserves_rejected_candidate_and_uses_exact_evidence():
    data = source()
    prompts = []
    class Model:
        def with_structured_output(self, schema):
            return SimpleNamespace(invoke=lambda prompt: (prompts.append(prompt) or schema.model_validate(candidate(data["snapshot_id"]))))
    bad = candidate(data["snapshot_id"], incorrect=True)
    result = create_financial_validation(Model(), {"market":json.dumps([data])})({"structured_decision":bad})
    assert result["structured_decision"] is not None
    assert result["rejected_structured_decision"] == bad
    assert "financial_number_requires_verified_reference" in prompts[0]
    assert len(prompts) == 1


def test_invalid_financial_repair_cannot_publish_or_loop():
    data = source()
    bad = candidate(data["snapshot_id"], incorrect=True)
    calls = []
    class Model:
        def with_structured_output(self, schema):
            return SimpleNamespace(invoke=lambda _: schema.model_validate(bad))
        def invoke(self, prompt):
            calls.append(prompt)
            return AIMessage(content=json.dumps(bad))
    result = create_financial_validation(Model(), {"market":json.dumps([data])})({"structured_decision":bad})
    assert result["structured_decision"] is None
    assert result["rejected_structured_decision"] == bad
    assert len(calls) == 1
    assert result["final_trade_decision"].startswith("UNVALIDATED RESEARCH")


def test_metadata_is_input_only_and_extra_fields_remain_rejected():
    data = source()
    bad = {**candidate(data["snapshot_id"]), "symbol":"AAPL"}
    prompts = []
    class Model:
        def with_structured_output(self, schema):
            def invoke(prompt):
                prompts.append(prompt)
                return schema.model_validate(bad)
            return SimpleNamespace(invoke=invoke)
        def invoke(self, prompt):
            prompts.append(prompt)
            return AIMessage(content=json.dumps(bad))
    initial = candidate(data["snapshot_id"], incorrect=True)
    result = create_financial_validation(Model(), {"market":json.dumps([data])})({
        "structured_decision":initial, "instrument_context":'{"symbol":"AAPL"}',
    })
    assert result["structured_decision"] is None
    assert len(prompts) == 2
    assert all("ONLY allowed top-level field names" in p for p in prompts)
    assert '<input_context_not_output_fields>\n{"symbol":"AAPL"}' in prompts[0]
    assert result["rejected_structured_decision"] == initial
