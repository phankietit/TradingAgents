import json
from types import SimpleNamespace

import pytest
from langchain_core.messages import AIMessage

from tradingagents.agents.research_schemas import CanonicalSnapshotDecision, LocalizedResearchReport
from tradingagents.agents.utils.report_localization import (
    localize_report,
    protect_quantities,
    reader_report,
    restore_quantities,
    validate_editorial_quality,
    validate_financial_terms,
)


def decision():
    return CanonicalSnapshotDecision(rating="Hold", confidence=.4,
        executive_summary="BTC closed at $84,034.92; return −3.38%. EMA10 is a reference.",
        investment_thesis="Price-only evidence, with a contrary momentum signal.",
        risks=["Missing macro evidence"], invalidation_conditions=["If the trend reverses"],
        time_horizon="3–6 months")


def translated_blocks(prompt):
    source = json.loads(prompt.split("<translation_blocks>\n", 1)[1].split("\n</translation_blocks>", 1)[0])
    return [{"block_id":item["block_id"], "vi":item["en"]} for item in source]


def test_roundtrip_protects_prices_signed_percentages_dates_and_indicator_digits():
    original = reader_report(decision()) + "\nAs of 2026-09-27, EMA10, $84,034.92."
    protected, values = protect_quantities(original)
    assert not any(char.isdecimal() for char in protected)
    assert restore_quantities(protected, values) == original


def test_ranges_and_dates_remain_indivisible_translation_atoms():
    protected, values = protect_quantities("EMA10; horizon 3-6 months; as of 2026-09-27.")
    assert list(values.values()) == ["EMA10", "3-6", "2026-09-27"]
    restored = restore_quantities(protected.replace("EMA", "EMA "), values)
    LocalizedResearchReport(en="EMA10; horizon 3-6 months; as of 2026-09-27.", vi=restored)


def test_indicator_names_are_indivisible_from_their_periods():
    original = "The +18.52% premium over the 200-SMA; EMA 10 and SMA50 remain references."
    protected, values = protect_quantities(original)
    assert list(values.values()) == ["+18.52%", "200-SMA", "EMA 10", "SMA50"]
    assert "SMA" not in protected and "EMA" not in protected
    assert restore_quantities(protected, values) == original


@pytest.mark.parametrize("vietnamese", [
    "EMA20, kỳ hạn 3-6 tháng, lợi suất -3.38%.",
    "EMA10, kỳ hạn 3-7 tháng, lợi suất -3.38%.",
    "EMA10, kỳ hạn 3-6 tháng, lợi suất 3.38%.",
])
def test_shared_parity_still_rejects_indicator_period_range_and_sign_changes(vietnamese):
    with pytest.raises(ValueError):
        LocalizedResearchReport(en="EMA10, horizon 3-6 months, return -3.38%.", vi=vietnamese)


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "unknown", "added_digit", "unicode_digit"])
def test_translation_rejects_changed_quantities(mutation):
    protected, values = protect_quantities("Close $84,034.92 with return -3.38%.")
    key = next(iter(values))
    altered = {"missing": protected.replace(key, ""), "duplicate": protected + key,
               "unknown": protected + "⟦QZZZ⟧", "added_digit": protected + " 7", "unicode_digit": protected + " ７"}[mutation]
    with pytest.raises(ValueError):
        restore_quantities(altered, values)


def test_translation_is_saved_separately_and_cannot_mutate_canonical_decision():
    canonical = decision()
    original = canonical.model_dump()
    class Model:
        def with_structured_output(self, schema):
            def invoke(prompt):
                assert "phạm vi dữ liệu" in prompt and "not as a word-for-word translation" in prompt
                assert "retaining every opposing argument and condition" in prompt
                blocks = translated_blocks(prompt)
                for block in blocks:
                    block["vi"] = block["vi"].replace("Price-only evidence", "Chỉ có dữ liệu giá")
                return schema(blocks=blocks)
            return SimpleNamespace(invoke=invoke)
        def invoke(self, _):
            pytest.fail("valid translation must not trigger repair")
    result = localize_report(Model(), canonical, [])
    assert "Chỉ có dữ liệu giá" in result.vi and "$84,034.92" in result.vi
    assert result.en == reader_report(canonical)
    assert canonical.model_dump() == original


def test_translation_has_one_bounded_repair_then_fails_closed():
    calls, diagnostics = [], []
    class Model:
        def with_structured_output(self, schema):
            return SimpleNamespace(invoke=lambda _: schema(blocks=[{"block_id":"BA", "vi":"Made up 25%"}]))
        def invoke(self, prompt):
            calls.append(prompt)
            return AIMessage(content=json.dumps({"blocks":[{"block_id":"BA", "vi":"Still invented 30%"}]}))
    assert localize_report(Model(), decision(), diagnostics) is None
    assert len(calls) == 1 and len(diagnostics) == 2


def test_canonical_generation_cannot_embed_a_second_language_report():
    with pytest.raises(ValueError):
        CanonicalSnapshotDecision.model_validate({**decision().model_dump(), "localized_report": {"en": "a", "vi": "b"}})


@pytest.mark.parametrize("english,vietnamese", [
    ("Low volatility may persist.", "Thanh khoản thấp có thể kéo dài."),
    ("Volume expands.", "Thanh khoản giãn nở."),
    ("MACD signal cross.", "Phân kỳ MACD."),
    ("A +18.52% premium over the 200-SMA.", "Giãn cách 200 so với SMA +18.52%."),
])
def test_financial_concept_substitution_is_rejected(english, vietnamese):
    with pytest.raises(ValueError):
        validate_financial_terms(english, vietnamese)


def test_distinct_financial_terms_and_genuine_liquidity_divergence_are_allowed():
    validate_financial_terms("Volume expands; volatility rises; MACD crosses signal.",
                             "Khối lượng giao dịch tăng; biến động tăng; MACD giao cắt đường tín hiệu.")
    validate_financial_terms("No liquidity or divergence evidence.", "Chưa có bằng chứng thanh khoản hay phân kỳ.")


@pytest.mark.parametrize("text", ["Bộ xu hướng còn nguyên vẹn.", "Không có so sánh biên.",
    "Tư thế phù hợp là giữ vị thế.", "Chế độ thông tin mỏng.", "Khối lượng trên thanh giảm.",
    "Diễn biến trùng phùng với phá vỡ hỗ trợ.", "Tại thời điểm của bộ dữ liệu tại thời điểm phân tích."])
def test_reproduced_editorial_calques_require_review(text):
    with pytest.raises(ValueError):
        validate_editorial_quality(text)


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "unknown", "cross_block", "empty", "heading"])
def test_translation_cannot_omit_merge_or_move_evidence_between_blocks(mutation):
    bad = None
    class Model:
        def with_structured_output(self, schema):
            def invoke(prompt):
                nonlocal bad
                blocks = translated_blocks(prompt)
                if mutation == "missing":
                    blocks.pop()
                elif mutation == "duplicate":
                    blocks.append(blocks[0].copy())
                elif mutation == "unknown":
                    blocks[0]["block_id"] = "BZZZ"
                elif mutation == "cross_block":
                    from tradingagents.agents.utils.report_localization import ANCHOR
                    anchor = ANCHOR.search(blocks[0]["vi"]).group()
                    blocks[0]["vi"] = blocks[0]["vi"].replace(anchor, "")
                    blocks[1]["vi"] += anchor
                elif mutation == "empty":
                    blocks[1]["vi"] = " "
                else:
                    blocks[1]["vi"] = "## Injected section\n" + blocks[1]["vi"]
                bad = {"blocks":blocks}
                return schema.model_validate(bad)
            return SimpleNamespace(invoke=invoke)
        def invoke(self, _):
            return AIMessage(content=json.dumps(bad))
    diagnostics = []
    assert localize_report(Model(), decision(), diagnostics) is None
    assert len(diagnostics) == 2


def test_output_order_is_owned_by_source_not_translator():
    class Model:
        def with_structured_output(self, schema):
            return SimpleNamespace(invoke=lambda prompt: schema(blocks=list(reversed(translated_blocks(prompt)))))
        def invoke(self, _):
            pytest.fail("correct unordered blocks do not need repair")
    result = localize_report(Model(), decision(), [])
    assert result.vi.index("## Tóm tắt") < result.vi.index("## Luận điểm đầu tư") < result.vi.index("## Rủi ro")
    assert result.vi.count("## Điều kiện mất hiệu lực") == 1


def test_editorial_failure_uses_existing_single_repair_without_changing_source():
    canonical = decision().model_copy(update={"investment_thesis":"The trend structure remains intact."})
    before = canonical.model_dump()
    corrected = None
    calls = []
    class Model:
        def with_structured_output(self, schema):
            def invoke(prompt):
                nonlocal corrected
                blocks = translated_blocks(prompt)
                blocks[1]["vi"] = "Bộ xu hướng vẫn còn nguyên vẹn."
                corrected = {"blocks":[dict(block) for block in blocks]}
                corrected["blocks"][1]["vi"] = "Cấu trúc xu hướng vẫn được duy trì."
                return schema(blocks=blocks)
            return SimpleNamespace(invoke=invoke)
        def invoke(self, prompt):
            calls.append(prompt)
            assert "translation_editorial_requires_review" in prompt
            return AIMessage(content=json.dumps(corrected))
    diagnostics = []
    result = localize_report(Model(), canonical, diagnostics)
    assert "Cấu trúc xu hướng vẫn được duy trì." in result.vi
    assert canonical.model_dump() == before
    assert len(calls) == 1 and len(diagnostics) == 1
