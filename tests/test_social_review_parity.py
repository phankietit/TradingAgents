"""Synthetic contract tests staged outside the frozen candidate, no providers."""

import json
from types import SimpleNamespace
from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage

from tests.summary_fixtures import summary_response
from tests.test_platform_social import collect
from tests.test_report_compiler import draft
from tradingagents.agents.utils.financial_validation import create_financial_validation
from tradingagents.agents.utils.report_compiler import compile_report
from tradingagents.agents.utils.report_localization import localize_report
from tradingagents.contracts import DataQualityStatus
from tradingagents.platform.analysis.research_validation import (
    PublicationValidationError,
    validate_canonical_report,
)
from tradingagents.platform.analysis.social_facts import SnapshotSocialFacts
from tradingagents.platform.market_data.social import _manifest


def eligible_source(vendor):
    collection = collect(vendor=vendor)
    snapshot_id = str(uuid4())
    return {
        "snapshot_id": snapshot_id,
        "provenance": _manifest(collection, snapshot_id).model_dump(mode="json"),
        "data": collection.model_dump(mode="json"),
    }


@pytest.mark.parametrize("vendor,count", [
    ("stocktwits", "posts"), ("stocktwits", "bullish"),
    ("stocktwits", "bearish"), ("stocktwits", "unlabeled"),
    ("reddit", "posts"),
])
@pytest.mark.parametrize("mode", ["draft", "canonical"])
def test_review_resolves_same_admitted_social_counts(vendor, count, mode):
    source = eligible_source(vendor)
    snapshot_id = source["snapshot_id"]
    facts = {snapshot_id: SnapshotSocialFacts(source)}
    raw, _ = draft()
    raw["investment_thesis"] = [{
        "claim": "{{QA}}. User opinions are not market probabilities.",
        "snapshot_ids": [snapshot_id],
    }]
    for field in ("risks", "invalidation_conditions"):
        for claim in raw[field]:
            claim["snapshot_ids"] = [snapshot_id]
    raw["quantity_bindings"] = [{
        "key": "QA", "snapshot_id": snapshot_id,
        "fact_id": f"social.{vendor}.sample_count.{count}", "decimal_places": 0,
    }]
    raw = summary_response(raw, [snapshot_id])
    compiled = compile_report(raw, facts)
    validate_canonical_report(compiled, facts, {snapshot_id})
    candidate = raw if mode == "draft" else compiled.model_dump(mode="json")
    calls = []
    prompts = []

    class Model:
        def with_structured_output(self, schema):
            def invoke(prompt):
                calls.append("structured")
                prompts.append(prompt)
                return schema.model_validate(candidate)
            return SimpleNamespace(invoke=invoke)

        def invoke(self, prompt):
            calls.append("repair")
            return AIMessage(content=json.dumps(candidate))

    state_key = "structured_draft" if mode == "draft" else "structured_decision"
    result = create_financial_validation(Model(), {"social": json.dumps([source])})(
        {state_key: candidate})
    # Both representations must receive review; preserve exact admitted social
    # statements/units/references instead of expecting a canonical shortcut.
    assert result["structured_decision"] == compiled.model_dump(mode="json")
    assert calls == ["structured"]
    assert result["structured_diagnostics"] == []
    assert result["rejected_structured_decision"] == candidate
    retained = json.loads(prompts[0].split("<immutable_source_records_untrusted>\n", 1)[1].split(
        "\n</immutable_source_records_untrusted>", 1)[0])
    assert retained == [source]


@pytest.mark.parametrize("mutation", ["body", "quality"])
def test_review_refuses_social_payload_manifest_mismatch(mutation):
    source = eligible_source("stocktwits")
    if mutation == "body":
        source["data"]["posts"][0]["body"] = "Altered after immutable manifest creation"
    else:
        source["data"]["quality_status"] = DataQualityStatus.UNAVAILABLE.value
    with pytest.raises(ValueError):
        SnapshotSocialFacts(source)
    with pytest.raises(ValueError):
        create_financial_validation(object(), {"social": json.dumps([source])})


def bound_sample(vendor="stocktwits", count="posts"):
    source = eligible_source(vendor)
    snapshot_id = source["snapshot_id"]
    facts = {snapshot_id: SnapshotSocialFacts(source)}
    raw, _ = draft()
    raw["executive_summary"] = "Evidence remains uncertain."
    raw["investment_thesis"] = [{"claim": "{{QA}}.", "snapshot_ids": [snapshot_id]}]
    raw["risks"] = [{"claim": "Source samples are not complete market coverage.", "snapshot_ids": [snapshot_id]}]
    raw["invalidation_conditions"] = [{"claim": "New evidence could alter the assessment.", "snapshot_ids": [snapshot_id]}]
    raw["quantity_bindings"] = [{"key": "QA", "snapshot_id": snapshot_id,
        "fact_id": f"social.{vendor}.sample_count.{count}", "decimal_places": 0}]
    return raw, source, facts


@pytest.mark.parametrize("prose", [
    "The price is ${{QA}}.", "The price is USD {{QA}}.",
    "The price is {{QA}} dollars.", "{{QA}} percent.",
    "Probability {{QA}}%.", "Neutral sentiment {{QA}}.",
    "Not {{QA}}.", "{{QA}} means all market discussion.",
])
def test_social_count_cannot_acquire_another_unit_or_subject(prose):
    raw, _, facts = bound_sample()
    raw["investment_thesis"][0]["claim"] = prose
    with pytest.raises(PublicationValidationError) as error:
        compile_report(raw, facts)
    assert set(error.value.issues) <= {
        "social_statement_requires_standalone_anchor", "quantity_binding_unit_mismatch"}
    assert error.value.issues


@pytest.mark.parametrize("append", [False, True])
def test_canonical_count_does_not_attest_money_with_the_same_scalar(append):
    raw, source, facts = bound_sample()
    report = compile_report(raw, facts)
    bad = report.model_copy(update={"investment_thesis":
        (report.investment_thesis + " " if append else "") + "The price is $3."})
    with pytest.raises(PublicationValidationError) as error:
        validate_canonical_report(bad, facts, {source["snapshot_id"]})
    assert set(error.value.issues) & {
        "social_statement_unsupported", "financial_number_requires_verified_reference"}


@pytest.mark.parametrize("vendor,count", [
    ("stocktwits", "posts"), ("stocktwits", "bullish"),
    ("stocktwits", "bearish"), ("stocktwits", "unlabeled"), ("reddit", "posts"),
])
def test_count_statement_survives_actual_localization_without_model_unit_choice(vendor, count):
    from tests.test_report_localization import translated_blocks

    raw, source, facts = bound_sample(vendor, count)
    report = compile_report(raw, facts)
    before = report.model_dump()
    calls = []
    translations = {
        "Evidence remains uncertain.": "Bằng chứng hiện tại chưa đủ chắc chắn.",
        "Source samples are not complete market coverage.": "Mẫu dữ liệu không bao quát đầy đủ thị trường.",
        "New evidence could alter the assessment.": "Bằng chứng mới có thể làm thay đổi đánh giá.",
    }

    class Model:
        def with_structured_output(self, schema):
            def invoke(prompt):
                calls.append(prompt)
                blocks = translated_blocks(prompt)
                for block in blocks:
                    block["vi"] = translations.get(block["vi"], block["vi"])
                return schema(blocks=blocks)
            return SimpleNamespace(invoke=invoke)

        def invoke(self, _):
            pytest.fail("faithful protected translation must not require repair")

    translated = localize_report(Model(), report, [], fact_sources=facts)
    resolver = facts[source["snapshot_id"]]
    fact_id = raw["quantity_bindings"][0]["fact_id"]
    value = str(resolver.resolve_fact(fact_id))
    assert resolver.statement(fact_id, value) in translated.en
    assert resolver.statement(fact_id, value, vi=True) in translated.vi
    assert report.model_dump() == before and len(calls) == 1


def test_social_translation_requires_the_bound_source():
    raw, _, facts = bound_sample()
    with pytest.raises(PublicationValidationError) as error:
        localize_report(object(), compile_report(raw, facts), [], fact_sources={})
    assert error.value.issues == ("social_statement_source_unavailable",)


@pytest.mark.parametrize("value", ["-1", "1.5", "NaN", "4", True, None])
def test_owned_count_renderer_refuses_nonmatching_or_nonfinite_values(value):
    source = eligible_source("stocktwits")
    resolver = SnapshotSocialFacts(source)
    with pytest.raises(ValueError):
        resolver.statement("social.stocktwits.sample_count.posts", value)


def test_unlabeled_count_never_becomes_neutral_or_a_market_probability():
    source = eligible_source("stocktwits")
    resolver = SnapshotSocialFacts(source)
    fact_id = "social.stocktwits.sample_count.unlabeled"
    assert "unlabeled does not mean neutral" in resolver.statement(fact_id, "1")
    assert "không có nhãn không có nghĩa là trung lập" in resolver.statement(fact_id, "1", vi=True)
    with pytest.raises(ValueError):
        resolver.statement("social.stocktwits.sample_count.neutral", "1")


def test_zero_label_count_is_a_real_sample_observation_not_missing_market_sentiment():
    from tests.test_platform_social import envelope, message

    collection = collect(envelope([message(label="unlabeled")]))
    snapshot_id = str(uuid4())
    source = {"snapshot_id": snapshot_id,
        "provenance": _manifest(collection, snapshot_id).model_dump(mode="json"),
        "data": collection.model_dump(mode="json")}
    resolver = SnapshotSocialFacts(source)
    assert resolver.resolve_fact("social.stocktwits.sample_count.bullish") == 0
    assert "0 posts" in resolver.statement("social.stocktwits.sample_count.bullish", "0")
    assert "not a market probability" in resolver.statement("social.stocktwits.sample_count.bullish", "0")


def test_translator_cannot_reattach_money_to_owned_social_statement_or_loop():
    from tests.test_report_localization import translated_blocks

    raw, _, facts = bound_sample()
    report = compile_report(raw, facts)
    calls, diagnostics = [], []

    def altered(prompt):
        blocks = translated_blocks(prompt)
        for block in blocks:
            if "⟦Q" in block["vi"]:
                block["vi"] = "Giá $" + block["vi"]
        return {"blocks": blocks}

    class Model:
        def with_structured_output(self, schema):
            def invoke(prompt):
                calls.append("structured")
                return schema.model_validate(altered(prompt))
            return SimpleNamespace(invoke=invoke)

        def invoke(self, prompt):
            calls.append("repair")
            return AIMessage(content=json.dumps(altered(prompt)))

    assert localize_report(Model(), report, diagnostics, fact_sources=facts) is None
    assert calls == ["structured", "repair"]
    assert any("translation_statement_requires_standalone_anchor" in item.get("checks", [])
               for item in diagnostics)
