from decimal import Decimal
from types import SimpleNamespace

import pytest

from tests.test_report_compiler import draft
from tests.test_report_localization import translated_blocks
from tradingagents.agents.utils.quantitative_statements import percentage_statement
from tradingagents.agents.utils.report_compiler import compile_report
from tradingagents.agents.utils.report_localization import (
    localize_report,
    protect_quantities,
    reader_report,
    restore_quantities,
)
from tradingagents.platform.analysis.market_facts import SnapshotMarketFacts
from tradingagents.platform.analysis.research_validation import (
    PublicationValidationError,
    number_tokens,
    validate_canonical_report,
)


@pytest.mark.parametrize("fact", [
    "return.30_calendar_days.pct", "observed_window.latest_close_vs_high_pct",
    "observed_window.drawdown_magnitude_pct", "indicator.atr.pct_of_latest_close",
    "indicator.close_10_ema.distance_from_latest_close_pct",
    "indicator.close_10_ema.latest_close_vs_indicator_pct",
    "indicator.close_10_ema.latest_close_distance_magnitude_pct",
    "calc.pct_change(latest.close,indicator.close_10_ema)",
    "calc.abs_pct_change(indicator.close_10_ema,latest.close)",
    "calc.pct_change(latest.volume,history.0.candle.volume)",
    "calc.abs_pct_change(latest.close,window.30.candle.high.max)",
    "calc.pct_change(return.30_calendar_days.pct,return.7_calendar_days.pct)",
    "calc.abs_pct_change(indicator.atr.pct_of_latest_close,return.30_calendar_days.pct)",
])
def test_typed_percentage_statements_preserve_values_and_locale_numbers(fact):
    en = percentage_statement(fact, "1.68")
    vi = percentage_statement(fact, "1.68", vi=True)
    assert number_tokens(en) == number_tokens(vi)
    protected, values = protect_quantities(en, {en: vi})
    assert len(values) == 1
    assert restore_quantities(protected, values) == vi


def test_reciprocal_relations_have_different_subject_and_baseline():
    close_over_ema = percentage_statement("indicator.close_10_ema.latest_close_vs_indicator_pct", "1.68")
    ema_over_close = percentage_statement("indicator.close_10_ema.distance_from_latest_close_pct", "-1.66")
    assert "latest close relative to 10-day EMA" in close_over_ema
    assert "10-day EMA relative to latest close" in ema_over_close
    assert "-1.66%" in ema_over_close


def test_compiler_owns_entire_percentage_sentence_and_preserves_interpretation():
    raw, data = draft()
    raw["quantity_bindings"].append({**raw["quantity_bindings"][0], "key":"QB",
                                    "fact_id":"indicator.close_10_ema.latest_close_vs_indicator_pct"})
    raw["investment_thesis"][0]["claim"] += " {{QB}}. The opposing case remains material."
    facts = {data["snapshot_id"]: SnapshotMarketFacts(data)}
    report = compile_report(raw, facts)
    value = Decimal(str(facts[data["snapshot_id"]].resolve_fact(raw["quantity_bindings"][1]["fact_id"]))).quantize(Decimal(".01"))
    assert percentage_statement(raw["quantity_bindings"][1]["fact_id"], format(value, "f")) in report.investment_thesis
    assert report.investment_thesis.endswith("The opposing case remains material.")
    validate_canonical_report(report, facts, set(facts))


@pytest.mark.parametrize("text", [
    "The EMA is {{QB}}% below the close.", "A return of {{QB}}.",
    "{{QB}}%.", "{{QB}} below the close.", "Not {{QB}}.",
])
def test_percentage_cannot_be_reattached_to_free_prose(text):
    raw, data = draft()
    raw["quantity_bindings"].append({**raw["quantity_bindings"][0], "key":"QB",
                                    "fact_id":"indicator.close_10_ema.latest_close_vs_indicator_pct"})
    raw["risks"][0]["claim"] = text
    with pytest.raises(PublicationValidationError) as failure:
        compile_report(raw, {data["snapshot_id"]: SnapshotMarketFacts(data)})
    assert failure.value.issues == ("percentage_statement_requires_standalone_anchor",)
    assert failure.value.binding_keys == ("QB",)


def test_unknown_percentage_template_is_not_guessed():
    with pytest.raises(ValueError):
        percentage_statement("indicator.secret_formula.pct_of_latest_close", "1.68")
    assert percentage_statement("latest.close", "341.07") is None


@pytest.mark.parametrize("suffix", ["%", " percent", " per cent"])
def test_ratio_fact_cannot_bypass_percentage_contract_by_adding_unit(suffix):
    raw, data = draft()
    raw["quantity_bindings"].append({**raw["quantity_bindings"][0], "key":"QB",
                                    "fact_id":"calc.ratio(latest.close,indicator.close_10_ema)"})
    raw["risks"][0]["claim"] = "The distance is {{QB}}" + suffix + "."
    with pytest.raises(PublicationValidationError) as failure:
        compile_report(raw, {data["snapshot_id"]:SnapshotMarketFacts(data)})
    assert failure.value.issues == ("quantity_binding_unit_mismatch",)


def test_entire_catalog_has_bilingual_percentage_templates():
    _, data = draft()
    for fact, value in SnapshotMarketFacts(data).fact_catalog().items():
        number = format(Decimal(str(value)).quantize(Decimal(".01")), "f")
        en = percentage_statement(fact, number)
        if en:
            vi = percentage_statement(fact, number, vi=True)
            assert number_tokens(en) == number_tokens(vi), fact


def test_presentation_restores_verified_relationship_without_model_translation():
    raw, data = draft()
    raw["quantity_bindings"].append({**raw["quantity_bindings"][0], "key":"QB",
                                    "fact_id":"return.30_calendar_days.pct"})
    raw["investment_thesis"][0]["claim"] += " {{QB}}. The opposing case remains material."
    canonical = compile_report(raw, {data["snapshot_id"]:SnapshotMarketFacts(data)})
    english = reader_report(canonical)
    observed = canonical.observed_numbers[-1]
    number = format(Decimal(str(observed.value)).quantize(Decimal(".01")), "f")
    en = percentage_statement(observed.fact_id, number)
    vi = percentage_statement(observed.fact_id, number, vi=True)
    class Model:
        def with_structured_output(self, schema):
            def invoke(prompt):
                assert "complete verified financial statement" in prompt
                assert en not in prompt
                return schema(blocks=translated_blocks(prompt))
            return SimpleNamespace(invoke=invoke)
        def invoke(self, _):
            pytest.fail("valid protected presentation must not need repair")
    result = localize_report(Model(), canonical, [])
    assert vi in result.vi and en not in result.vi
    assert result.en == english
