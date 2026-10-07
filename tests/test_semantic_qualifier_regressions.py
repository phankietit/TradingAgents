"""Source-bound semantic challenges, not proof of general entailment/model quality."""

import json
from types import SimpleNamespace

import pytest
from langchain_core.messages import AIMessage

from tests.test_financial_validation_stage import candidate
from tests.test_report_localization import decision, translated_blocks
from tests.test_snapshot_market_facts import source
from tradingagents.agents.utils.financial_validation import create_financial_validation
from tradingagents.agents.utils.report_localization import localize_report

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

    class Model:
        def with_structured_output(self, schema):
            def invoke(prompt):
                calls.append(prompt)
                return schema.model_validate(report)
            return SimpleNamespace(invoke=invoke)

        def invoke(self, prompt):
            calls.append(prompt)
            return AIMessage(content=json.dumps(report))

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
    assert reviewed_report(unsupported=True)["structured_decision"] is None


def test_source_bound_observation_remains_eligible_for_financial_review():
    assert reviewed_report(unsupported=False)["structured_decision"] is not None


@pytest.mark.parametrize("english,incorrect,correct", CASES)
def test_translation_withholds_changed_action_qualifier_polarity_or_opposing_case(english, incorrect, correct):
    assert translated_report(english, incorrect) is None


@pytest.mark.parametrize("english,incorrect,correct", CASES)
def test_translation_preserves_supported_action_qualifier_polarity_and_opposing_case(english, incorrect, correct):
    result = translated_report(english, correct)
    assert result is not None and correct in result.vi
