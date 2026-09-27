import copy
import json

import pytest

from tests.test_financial_validation_stage import candidate
from tests.test_snapshot_market_facts import source
from tradingagents.agents.utils.financial_validation import create_financial_validation
from tradingagents.agents.utils.report_compiler import compile_report
from tradingagents.platform.analysis.market_facts import SnapshotMarketFacts
from tradingagents.platform.analysis.research_validation import (
    PublicationValidationError,
    validate_canonical_report,
)


def draft():
    data = source()
    payload = candidate(data["snapshot_id"])
    payload["investment_thesis"] = payload["investment_thesis"].replace("499.00", "{{QA}}")
    payload["evidence_claims"][0]["claim"] = payload["investment_thesis"]
    payload["observed_numbers"] = []
    payload["quantity_bindings"] = [
        {
            "key": "QA",
            "snapshot_id": data["snapshot_id"],
            "fact_id": "latest.close",
            "decimal_places": 2,
        }
    ]
    return payload, data


def test_compilation_uses_source_and_preserves_material_claims():
    raw, data = draft()
    before = copy.deepcopy(raw)
    facts = {data["snapshot_id"]: SnapshotMarketFacts(data)}
    report = compile_report(raw, facts)
    assert "$499.00" in report.investment_thesis
    assert report.observed_numbers[0].value == 499
    assert raw == before
    validate_canonical_report(report, facts, set(facts))


@pytest.mark.parametrize(
    "mutation",
    [
        "unknown",
        "duplicate",
        "unused",
        "missing",
        "raw_number",
        "wrong_snapshot",
        "literal_expression",
    ],
)
def test_invalid_binding_cannot_publish(mutation):
    raw, data = draft()
    binding = raw["quantity_bindings"][0]
    if mutation == "unknown":
        binding["fact_id"] = "invented.close"
    if mutation == "duplicate":
        raw["quantity_bindings"].append(copy.deepcopy(binding))
    if mutation == "unused":
        binding["key"] = "QB"
    if mutation == "missing":
        raw["quantity_bindings"] = []
    if mutation == "raw_number":
        raw["executive_summary"] = "Return 30.00%"
    if mutation == "wrong_snapshot":
        binding["snapshot_id"] = "00000000-0000-0000-0000-000000000000"
    if mutation == "literal_expression":
        binding["fact_id"] = "calc.ratio(latest.close,100)"
    with pytest.raises(PublicationValidationError):
        compile_report(raw, {data["snapshot_id"]: SnapshotMarketFacts(data)})


def test_draft_validates_without_extra_model_call():
    raw, data = draft()
    node = create_financial_validation(object(), {"market": json.dumps([data])})
    result = node({"structured_draft": raw})
    assert result["structured_decision"]["observed_numbers"][0]["value"] == 499
    assert "{{QA}}" not in result["final_trade_decision"]
