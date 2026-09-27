import copy
import json
from types import SimpleNamespace

import pytest

from tests.test_financial_validation_stage import candidate
from tests.test_snapshot_market_facts import source
from tradingagents.agents.utils.financial_validation import create_financial_validation
from tradingagents.agents.utils.report_compiler import compile_report, validate_percentage_context
from tradingagents.platform.analysis.market_facts import SnapshotMarketFacts
from tradingagents.platform.analysis.research_validation import (
    PublicationValidationError,
    validate_canonical_report,
)


def draft():
    data = source()
    payload = candidate(data["snapshot_id"])
    payload["investment_thesis"] = payload["investment_thesis"].replace("499.00", "{{QA}}")
    def linked(claim):
        return {"claim":claim,"snapshot_ids":[data["snapshot_id"]]}
    payload["investment_thesis"] = [linked(payload["investment_thesis"])]
    payload["risks"] = [linked(text) for text in payload["risks"]]
    payload["invalidation_conditions"] = [linked(text) for text in payload["invalidation_conditions"]]
    payload["evidence_claims"] = []
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
    with pytest.raises(ValueError):
        compile_report(raw, {data["snapshot_id"]: SnapshotMarketFacts(data)})


def test_draft_requires_one_financial_meaning_review_even_when_math_passes():
    raw, data = draft()
    calls = []
    class Model:
        def with_structured_output(self, schema):
            return SimpleNamespace(invoke=lambda prompt: calls.append(prompt) or schema.model_validate(raw))
    node = create_financial_validation(Model(), {"market": json.dumps([data])})
    result = node({"structured_draft": raw})
    assert result["structured_decision"]["observed_numbers"][0]["value"] == 499
    assert "{{QA}}" not in result["final_trade_decision"]
    assert len(calls) == 1


def test_paragraph_citations_compile_without_losing_source_coverage():
    raw, data = draft()
    raw["investment_thesis"].append({"claim":"Opposing evidence remains material.", "snapshot_ids":[data["snapshot_id"]]})
    facts = {data["snapshot_id"]:SnapshotMarketFacts(data)}
    result = compile_report(raw, facts)
    assert result.investment_thesis.endswith("\n\nOpposing evidence remains material.")
    validate_canonical_report(result, facts, set(facts))
    assert result.evidence_claims[0].claim == result.investment_thesis


def test_unknown_material_source_is_not_invented_during_compilation():
    raw, data = draft()
    raw["risks"][0]["snapshot_ids"] = ["00000000-0000-0000-0000-000000000000"]
    facts = {data["snapshot_id"]:SnapshotMarketFacts(data)}
    result = compile_report(raw, facts)
    with pytest.raises(PublicationValidationError):
        validate_canonical_report(result, facts, set(facts))


@pytest.mark.parametrize("mutation,code", [
    ("unused", "quantity_binding_unused"),
    ("missing", "quantity_binding_missing"),
    ("duplicate", "quantity_binding_duplicate"),
    ("unknown", "quantity_binding_unknown_fact"),
    ("malformed", "quantity_anchor_malformed"),
])
def test_binding_diagnostics_identify_repair_without_weakening_gate(mutation, code):
    raw, data = draft()
    if mutation == "unused":
        raw["quantity_bindings"].append({**raw["quantity_bindings"][0], "key":"QB"})
    elif mutation == "missing":
        raw["quantity_bindings"] = []
    elif mutation == "duplicate":
        raw["quantity_bindings"].append(copy.deepcopy(raw["quantity_bindings"][0]))
    elif mutation == "unknown":
        raw["quantity_bindings"][0]["fact_id"] = "untrusted-secret-like-unknown-id"
    else:
        raw["executive_summary"] += " {{Qbad}}"
    before = copy.deepcopy(raw)
    with pytest.raises(PublicationValidationError) as failure:
        compile_report(raw, {data["snapshot_id"]:SnapshotMarketFacts(data)})
    assert failure.value.issues == (code,)
    assert "untrusted-secret" not in str(failure.value)
    assert raw == before


@pytest.mark.parametrize("prose,fact,value", [
    ("The close is {{QA}}% below the window high.", "observed_window.latest_close_vs_high_pct", -1.24),
    ("The 50-SMA is currently {{QA}}% below the latest close.", "indicator.close_50_sma.latest_close_distance_magnitude_pct", 5.98),
    ("The 10-day EMA at ${{QB}} sits only {{QA}}% below the close as nearest support.", "indicator.close_10_ema.latest_close_vs_indicator_pct", 1.68),
    ("A move to the SMA would represent a {{QA}}% drawdown from the current close.", "indicator.close_50_sma.latest_close_distance_magnitude_pct", 5.98),
    ("A move to the SMA would represent a {{QA}}% move from the current close.", "indicator.close_50_sma.latest_close_vs_indicator_pct", 5.98),
    ("The close sits {{QA}}% below the upper Bollinger band.", "indicator.boll_ub.distance_from_latest_close_pct", 1.49),
])
def test_reproduced_percentage_semantic_errors_fail_closed(prose, fact, value):
    with pytest.raises(PublicationValidationError) as error:
        validate_percentage_context(prose, {"key":"QA", "fact_id":fact}, value)
    assert error.value.issues == ("percentage_relation_requires_review",)
    assert error.value.binding_keys == ("QA",)


def test_percentage_guard_tracks_binding_not_coincidentally_equal_numbers():
    validate_percentage_context("Price is {{QA}}% above its SMA; return {{QB}}%.",
        {"key":"QA", "fact_id":"indicator.close_50_sma.latest_close_distance_magnitude_pct"}, 5.98)
    validate_percentage_context("The close is {{QA}}% below the window high.",
        {"key":"QA", "fact_id":"observed_window.drawdown_magnitude_pct"}, 1.24)
    validate_percentage_context("The 50-SMA is currently {{QA}}% below the latest close.",
        {"key":"QA", "fact_id":"calc.abs_pct_change(indicator.close_50_sma,latest.close)"}, 5.64)
    validate_percentage_context("The upper Bollinger band is {{QA}}% above the latest close.",
        {"key":"QA", "fact_id":"indicator.boll_ub.distance_from_latest_close_pct"}, 1.49)


def test_all_affected_bindings_are_reported_without_raw_provider_text():
    from tradingagents.agents.utils.structured import _safe_diagnostic

    raw, data = draft()
    raw["risks"][0]["claim"] = "The close is {{QB}}% below the window high. The 50-SMA is currently {{QC}}% below the latest close."
    raw["quantity_bindings"].extend([
        {**raw["quantity_bindings"][0], "key":"QB", "fact_id":"observed_window.latest_close_vs_high_pct"},
        {**raw["quantity_bindings"][0], "key":"QC", "fact_id":"indicator.close_50_sma.latest_close_distance_magnitude_pct"},
    ])
    with pytest.raises(PublicationValidationError) as error:
        compile_report(raw, {data["snapshot_id"]:SnapshotMarketFacts(data)})
    assert error.value.binding_keys == ("QB", "QC")
    diagnostic = _safe_diagnostic("Review", error.value, "publication")
    assert diagnostic["binding_keys"] == ["QB", "QC"]
    safe = PublicationValidationError(["percentage_relation_requires_review"], binding_keys=["QA", "private-token-value"])
    assert safe.binding_keys == ("QA",)
