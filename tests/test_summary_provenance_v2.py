"""Staged V2 schema/compiler tests; default generation activation is still pending."""

import copy
from uuid import uuid4

import pytest

from tests.test_financial_validation_stage import candidate
from tests.test_report_compiler import draft
from tradingagents.agents.research_schemas import (
    CanonicalSnapshotDecision,
    CanonicalSnapshotDecisionV2,
    SnapshotReportDraftV2,
    read_canonical_snapshot_report,
)
from tradingagents.agents.schemas import PortfolioDecision
from tradingagents.agents.utils.report_compiler import compile_report, compile_report_v2
from tradingagents.agents.utils.semantic_qualifiers import validate_price_only_attributions
from tradingagents.platform.analysis.market_facts import SnapshotMarketFacts
from tradingagents.platform.analysis.research_validation import (
    PublicationValidationError,
    validate_canonical_report,
)


def _draft():
    raw, data = draft()
    raw["report_contract_version"] = "2.0"
    raw["executive_summary"] = "The close is ${{QA}}; the outlook remains uncertain."
    raw["summary_evidence"] = {"claim": raw["executive_summary"],
                               "snapshot_ids": [data["snapshot_id"]]}
    return raw, data


def test_v2_projection_preserves_complete_summary_quantities_and_explicit_refs():
    raw, data = _draft()
    before = copy.deepcopy(raw)
    facts = {data["snapshot_id"]: SnapshotMarketFacts(data)}
    compiled = compile_report(raw, facts)
    assert isinstance(compiled, CanonicalSnapshotDecisionV2)
    assert compiled.executive_summary == "The close is $499.00; the outlook remains uncertain."
    assert compiled.summary_evidence.claim == compiled.executive_summary
    assert [str(value) for value in compiled.summary_evidence.snapshot_ids] == [data["snapshot_id"]]
    validate_canonical_report(compiled, facts, set(facts))
    assert raw == before
    assert read_canonical_snapshot_report(compiled.model_dump(mode="json")) == compiled


@pytest.mark.parametrize("field", ["summary_evidence", "report_contract_version"])
def test_v2_missing_contract_fields_never_downgrade_to_legacy(field):
    raw, data = _draft()
    raw.pop(field)
    with pytest.raises(ValueError):
        compile_report(raw, {data["snapshot_id"]: SnapshotMarketFacts(data)})


@pytest.mark.parametrize("version", [None, "1.0", "3.0", 2])
def test_explicit_unknown_version_refuses_instead_of_legacy_fallback(version):
    raw, data = _draft()
    raw["report_contract_version"] = version
    with pytest.raises(ValueError):
        compile_report(raw, {data["snapshot_id"]: SnapshotMarketFacts(data)})
    with pytest.raises(ValueError):
        read_canonical_snapshot_report(raw)


@pytest.mark.parametrize("mutation", ["changed_text", "partial_text", "empty", "duplicate"])
def test_summary_binding_requires_exact_full_text_and_unique_nonempty_refs(mutation):
    raw, data = _draft()
    if mutation == "changed_text":
        raw["summary_evidence"]["claim"] = "The outlook is certain."
    elif mutation == "partial_text":
        raw["summary_evidence"]["claim"] = "The outlook remains uncertain."
    elif mutation == "empty":
        raw["summary_evidence"]["snapshot_ids"] = []
    else:
        raw["summary_evidence"]["snapshot_ids"] *= 2
    with pytest.raises(ValueError):
        compile_report(raw, {data["snapshot_id"]: SnapshotMarketFacts(data)})


def test_unknown_summary_reference_fails_without_inventing_thesis_source_link():
    raw, data = _draft()
    raw["executive_summary"] = "The outlook remains uncertain."
    raw["summary_evidence"]["claim"] = raw["executive_summary"]
    unknown = str(uuid4())
    raw["summary_evidence"]["snapshot_ids"] = [unknown]
    before = copy.deepcopy(raw)
    facts = {data["snapshot_id"]: SnapshotMarketFacts(data)}
    compiled = compile_report(raw, facts)
    assert str(compiled.summary_evidence.snapshot_ids[0]) == unknown
    with pytest.raises(PublicationValidationError) as failure:
        validate_canonical_report(compiled, facts, set(facts))
    assert "unknown_snapshot_reference" in failure.value.issues
    assert raw == before


@pytest.mark.parametrize("conditional", [False, True])
def test_v2_summary_scope_uses_actual_refs_despite_unrelated_news(conditional):
    raw, data = _draft()
    text = "Tax-loss selling explains the latest decline."
    if conditional:
        text = "Tax-loss selling could explain the decline; this is unverified."
    raw["executive_summary"] = text
    raw["summary_evidence"]["claim"] = text
    compiled = compile_report(raw, {data["snapshot_id"]: SnapshotMarketFacts(data)})
    news = {"snapshot_id": str(uuid4()), "provenance": {"dataset": "news"},
            "data": {"headline": "Synthetic unrelated product announcement"}}
    if conditional:
        validate_price_only_attributions(compiled, [data, news])
    else:
        with pytest.raises(PublicationValidationError) as failure:
            validate_price_only_attributions(compiled, [data, news])
        assert failure.value.issues == ("external_cause_requires_nonprice_evidence",)


def test_v2_schema_has_no_implicit_version_or_guessed_summary_evidence_default():
    for schema in (SnapshotReportDraftV2, CanonicalSnapshotDecisionV2):
        assert schema.model_fields["report_contract_version"].is_required()
        assert schema.model_fields["summary_evidence"].is_required()
        assert schema.__name__ == "PortfolioDecision"  # Original provider tool identity.


def test_legacy_reader_and_cli_contract_remain_unmodified():
    _, data = _draft()
    legacy = CanonicalSnapshotDecision.model_validate(candidate(data["snapshot_id"]))
    raw = legacy.model_dump(mode="json")
    before = copy.deepcopy(raw)
    assert read_canonical_snapshot_report(raw).model_dump(mode="json") == before
    assert raw == before
    for schema in (CanonicalSnapshotDecision, PortfolioDecision):
        assert "report_contract_version" not in schema.model_fields
        assert "summary_evidence" not in schema.model_fields


def test_removing_both_v2_fields_cannot_escape_strict_generation_entry():
    raw, data = _draft()
    facts = {data["snapshot_id"]: SnapshotMarketFacts(data)}
    assert isinstance(compile_report_v2(raw, facts), CanonicalSnapshotDecisionV2)
    raw.pop("report_contract_version")
    raw.pop("summary_evidence")
    with pytest.raises(ValueError):
        compile_report_v2(raw, facts)


def test_summary_quantity_must_cite_its_actual_binding_source():
    raw, data = _draft()
    raw["summary_evidence"]["snapshot_ids"] = [str(uuid4())]
    before = copy.deepcopy(raw)
    with pytest.raises(PublicationValidationError) as failure:
        compile_report_v2(raw, {data["snapshot_id"]: SnapshotMarketFacts(data)})
    assert failure.value.issues == ("material_claim_citation_mismatch",)
    assert raw == before
