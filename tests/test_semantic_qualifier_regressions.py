"""Source-bound semantic challenges, not proof of general entailment/model quality."""

import json
from types import SimpleNamespace

import pytest
from langchain_core.messages import AIMessage

from tests.summary_fixtures import summary_response
from tests.test_financial_validation_stage import candidate
from tests.test_report_localization import decision, translated_blocks
from tests.test_snapshot_market_facts import source
from tradingagents.agents.utils.financial_validation import create_financial_validation
from tradingagents.agents.utils.report_localization import localize_report
from tradingagents.agents.utils.semantic_qualifiers import validate_translation_qualifiers
from tradingagents.platform.analysis.research_validation import PublicationValidationError

CASES = [
    ("Avoid aggressive new buying until the trend confirms.",
     "Tránh mọi hoạt động mua mới.",
     "Tránh mua mới mạnh tay cho đến khi xu hướng được xác nhận."),
    ("The evidence does not establish a bullish reversal.",
     "Bằng chứng xác nhận sự đảo chiều tăng giá.",
     "Bằng chứng chưa xác lập sự đảo chiều tăng giá."),
    ("Volume may improve, but this is not confirmed.",
     "Khối lượng giao dịch sẽ cải thiện.",
     "Khối lượng giao dịch có thể cải thiện, nhưng điều này chưa được xác nhận."),
    ("Reduce exposure gradually if support breaks.",
     "Giảm tỷ trọng ngay lập tức.",
     "Giảm tỷ trọng dần nếu hỗ trợ bị phá vỡ."),
    ("Only reconsider buying after evidence improves.",
     "Có thể mua ngay.",
     "Chỉ xem xét lại việc mua sau khi bằng chứng được cải thiện."),
    ("The bearish case remains possible despite the rebound.",
     "Nhịp hồi phục loại bỏ kịch bản giảm giá.",
     "Kịch bản giảm giá vẫn có thể xảy ra dù có nhịp hồi phục."),
]


def reviewed_report(*, unsupported):
    data = source()
    report = candidate(data["snapshot_id"])
    if unsupported:
        report["investment_thesis"] += " Tax-loss selling explains the latest decline."
        report["evidence_claims"][0]["claim"] = report["investment_thesis"]
    calls = []
    response = summary_response(report, [data["snapshot_id"]])

    class Model:
        def with_structured_output(self, schema):
            def invoke(prompt):
                calls.append(prompt)
                return schema.model_validate(response)
            return SimpleNamespace(invoke=invoke)

        def invoke(self, prompt):
            calls.append(prompt)
            return AIMessage(content=json.dumps(response))

    result = create_financial_validation(Model(), {"market":json.dumps([data])})({"structured_decision":report})
    assert 1 <= len(calls) <= 2  # Original bounded structured + repair, no new call loop.
    return result


def translated_report(english, vietnamese):
    canonical = decision().model_copy(update={"investment_thesis":english})
    before = canonical.model_dump()
    calls, output = [], None

    class Model:
        def with_structured_output(self, schema):
            def invoke(prompt):
                nonlocal output
                calls.append(prompt)
                blocks = translated_blocks(prompt)
                for block in blocks:
                    if block["vi"] == english:
                        block["vi"] = vietnamese
                output = {"blocks":blocks}
                return schema.model_validate(output)
            return SimpleNamespace(invoke=invoke)

        def invoke(self, prompt):
            calls.append(prompt)
            return AIMessage(content=json.dumps(output))

    result = localize_report(Model(), canonical, [])
    assert canonical.model_dump() == before
    assert 1 <= len(calls) <= 2
    return result


def test_price_only_evidence_cannot_publish_an_unsupported_factual_cause():
    result = reviewed_report(unsupported=True)
    assert result["structured_decision"] is None
    assert any('external_cause_requires_nonprice_evidence' in item.get('checks', [])
               for item in result['structured_diagnostics'])


def test_source_bound_observation_remains_eligible_for_financial_review():
    result = reviewed_report(unsupported=False)
    assert result["structured_decision"] is not None
    assert result["structured_decision"]["report_contract_version"] == "2.0"


@pytest.mark.parametrize("english,incorrect,correct", CASES)
def test_translation_withholds_changed_action_qualifier_polarity_or_opposing_case(english, incorrect, correct):
    assert translated_report(english, incorrect) is None


@pytest.mark.parametrize("english,incorrect,correct", CASES)
def test_translation_preserves_supported_action_qualifier_polarity_and_opposing_case(english, incorrect, correct):
    result = translated_report(english, correct)
    assert result is not None and correct in result.vi


@pytest.mark.parametrize("english,incorrect,correct", [
    ("Avoid aggressive buying until support is confirmed.",
     "Tránh mua mới. Phân tích được thực hiện mạnh tay cho đến khi xong.",
     "Tránh mua mạnh tay cho đến khi hỗ trợ được xác nhận."),
    ("The evidence does not confirm reversal. Volume improves.",
     "Bằng chứng xác nhận đảo chiều. Không có khuyến nghị mua mới.",
     "Bằng chứng chưa xác nhận đảo chiều. Khối lượng giao dịch cải thiện."),
    ("If price breaks support, reconsider the thesis.",
     "Giá phá vỡ hỗ trợ, xem xét lại luận điểm.",
     "Nếu giá phá vỡ hỗ trợ, xem xét lại luận điểm."),
    ("Price may rise 3.38% if support holds.",
     "Giá sẽ tăng 3.38% khi hỗ trợ giữ vững.",
     "Giá có thể tăng 3.38% nếu hỗ trợ giữ vững."),
])
def test_qualifiers_cannot_move_to_unrelated_sentences_or_disappear_at_decimal_boundary(english, incorrect, correct):
    with pytest.raises(PublicationValidationError, match="research publication checks failed"):
        validate_translation_qualifiers(english, incorrect)
    validate_translation_qualifiers(english, correct)


def test_two_distinct_action_conditions_cannot_be_covered_by_one_target_marker():
    source_text = "Reduce exposure if support breaks. Buy only if evidence improves."
    with pytest.raises(PublicationValidationError):
        validate_translation_qualifiers(source_text, "Giảm tỷ trọng nếu hỗ trợ bị phá vỡ. Chỉ mua.")
    validate_translation_qualifiers(source_text, "Giảm tỷ trọng nếu hỗ trợ bị phá vỡ. Chỉ mua nếu bằng chứng tốt hơn.")
    validate_translation_qualifiers(source_text, "Giảm tỷ trọng khi hỗ trợ bị phá vỡ. Chỉ mua khi bằng chứng tốt hơn.")


@pytest.mark.parametrize("english,vietnamese", [
    ("Avoid aggressive purchases until price stabilizes.", "Tránh mua mạnh tay đến khi giá ổn định."),
    ("Gradually reduce exposure if momentum declines.", "Giảm tỷ trọng từng bước khi động lượng giảm."),
    ("Evidence is unverified; reversal might occur.", "Bằng chứng chưa được kiểm chứng; đảo chiều có thể xảy ra."),
])
def test_natural_qualifier_paraphrases_are_not_blanket_rejected(english, vietnamese):
    validate_translation_qualifiers(english, vietnamese)


@pytest.mark.parametrize("english,vietnamese", [
    ("In May price rose.", "Trong tháng Năm, giá tăng."),
    ("Price rose on May 10.", "Giá tăng vào ngày 10 tháng Năm."),
    ("The evidence could not establish reversal.", "Bằng chứng không thể xác lập đảo chiều."),
])
def test_calendar_month_and_negative_ability_are_not_misread_as_lost_uncertainty(english, vietnamese):
    validate_translation_qualifiers(english, vietnamese)


def test_price_only_motivation_may_remain_an_explicit_unverified_hypothesis():
    from tradingagents.agents.research_schemas import CanonicalSnapshotDecision
    from tradingagents.agents.utils.semantic_qualifiers import validate_price_only_attributions

    data = source()
    report = candidate(data["snapshot_id"])
    for text in ("Tax-loss selling could explain the decline; this is an unverified hypothesis.",
                 "Tax-loss selling is not established as the cause by these prices."):
        report["investment_thesis"] = text
        validate_price_only_attributions(CanonicalSnapshotDecision.model_validate(report), [data])


def test_qualifier_repair_uses_one_existing_repair_and_preserves_canonical_content():
    english, incorrect, correct = CASES[0]
    canonical = decision().model_copy(update={"investment_thesis":english})
    before = canonical.model_dump()
    repaired, calls, diagnostics = None, [], []

    class Model:
        def with_structured_output(self, schema):
            def invoke(prompt):
                nonlocal repaired
                calls.append(prompt)
                blocks = translated_blocks(prompt)
                repaired = {"blocks":[dict(block) for block in blocks]}
                for block in blocks:
                    if block["vi"] == english:
                        block["vi"] = incorrect
                for block in repaired["blocks"]:
                    if block["vi"] == english:
                        block["vi"] = correct
                return schema(blocks=blocks)
            return SimpleNamespace(invoke=invoke)

        def invoke(self, prompt):
            calls.append(prompt)
            assert "translation_qualifier_requires_review" in prompt
            return AIMessage(content=json.dumps(repaired))

    result = localize_report(Model(), canonical, diagnostics)
    assert result is not None and correct in result.vi
    assert canonical.model_dump() == before
    assert len(calls) == 2 and len(diagnostics) == 1


def test_unsupported_cause_repair_preserves_the_rejected_complete_report():
    data = source()
    original = candidate(data["snapshot_id"])
    original["investment_thesis"] += " Tax-loss selling explains the decline."
    original["evidence_claims"][0]["claim"] = original["investment_thesis"]
    corrected = candidate(data["snapshot_id"])
    original_response = summary_response(original, [data["snapshot_id"]])
    corrected_response = summary_response(corrected, [data["snapshot_id"]])
    calls = []

    class Model:
        def with_structured_output(self, schema):
            def invoke(prompt):
                calls.append(prompt)
                return schema.model_validate(original_response)
            return SimpleNamespace(invoke=invoke)

        def invoke(self, prompt):
            calls.append(prompt)
            assert "external_cause_requires_nonprice_evidence" in prompt
            return AIMessage(content=json.dumps(corrected_response))

    result = create_financial_validation(Model(), {"market":json.dumps([data])})({"structured_decision":original})
    assert result["structured_decision"]["investment_thesis"] == corrected["investment_thesis"]
    assert result["structured_decision"]["report_contract_version"] == "2.0"
    assert result["structured_decision"]["summary_evidence"] == corrected_response["summary_evidence"]
    assert result["rejected_structured_decision"] == original
    assert len(calls) == 2
