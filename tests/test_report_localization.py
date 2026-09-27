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
    validate_financial_terms,
)


def decision():
    return CanonicalSnapshotDecision(rating="Hold", confidence=.4,
        executive_summary="BTC closed at $84,034.92; return −3.38%. EMA10 is a reference.",
        investment_thesis="Price-only evidence, with a contrary momentum signal.",
        risks=["Missing macro evidence"], invalidation_conditions=["If the trend reverses"],
        time_horizon="3–6 months")


def test_roundtrip_protects_prices_signed_percentages_dates_and_indicator_digits():
    original = reader_report(decision()) + "\nAs of 2026-09-27, EMA10, $84,034.92."
    protected, values = protect_quantities(original)
    assert not any(char.isdecimal() for char in protected)
    assert restore_quantities(protected, values) == original


def test_ranges_and_dates_remain_indivisible_translation_atoms():
    protected, values = protect_quantities("EMA10; horizon 3-6 months; as of 2026-09-27.")
    assert list(values.values()) == ["10", "3-6", "2026-09-27"]
    restored = restore_quantities(protected.replace("EMA", "EMA "), values)
    LocalizedResearchReport(en="EMA10; horizon 3-6 months; as of 2026-09-27.", vi=restored)


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
    protected, _ = protect_quantities(reader_report(canonical))
    class Model:
        def with_structured_output(self, schema):
            def invoke(prompt):
                assert "phạm vi dữ liệu" in prompt and "not as a word-for-word translation" in prompt
                assert "retaining every opposing argument and condition" in prompt
                return schema(vi=protected.replace("Price-only evidence", "Chỉ có dữ liệu giá"))
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
            return SimpleNamespace(invoke=lambda _: schema(vi="Made up 25%"))
        def invoke(self, prompt):
            calls.append(prompt)
            return AIMessage(content=json.dumps({"vi": "Still invented 30%"}))
    assert localize_report(Model(), decision(), diagnostics) is None
    assert len(calls) == 1 and len(diagnostics) == 2


def test_canonical_generation_cannot_embed_a_second_language_report():
    with pytest.raises(ValueError):
        CanonicalSnapshotDecision.model_validate({**decision().model_dump(), "localized_report": {"en": "a", "vi": "b"}})


@pytest.mark.parametrize("english,vietnamese", [
    ("Low volatility may persist.", "Thanh khoản thấp có thể kéo dài."),
    ("Volume expands.", "Thanh khoản giãn nở."),
    ("MACD signal cross.", "Phân kỳ MACD."),
])
def test_financial_concept_substitution_is_rejected(english, vietnamese):
    with pytest.raises(ValueError):
        validate_financial_terms(english, vietnamese)


def test_distinct_financial_terms_and_genuine_liquidity_divergence_are_allowed():
    validate_financial_terms("Volume expands; volatility rises; MACD crosses signal.",
                             "Khối lượng giao dịch tăng; biến động tăng; MACD giao cắt đường tín hiệu.")
    validate_financial_terms("No liquidity or divergence evidence.", "Chưa có bằng chứng thanh khoản hay phân kỳ.")
