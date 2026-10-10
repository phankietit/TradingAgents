"""Unreferenced word-percent controls; not a qualitative entailment evaluator."""

from types import SimpleNamespace

import pytest

from tests.test_report_compiler import draft
from tradingagents.agents.utils.report_compiler import compile_report
from tradingagents.platform.analysis.market_facts import SnapshotMarketFacts
from tradingagents.platform.analysis.research_validation import unsupported_financial_numbers


@pytest.mark.parametrize("text", [
    "Return 30 percent.", "Return 30 per cent.", "Return -30 percent.",
    "Return −30 PER CENT.", "Return 30.00 PERCENT.", "Return 30\u00a0percent.",
])
def test_word_percentage_requires_reference_and_binding(text):
    assert unsupported_financial_numbers(text, ())
    number = -30 if "-30" in text or "−30" in text else 30
    assert not unsupported_financial_numbers(text, (SimpleNamespace(value=number),))
    raw, source = draft()
    raw["executive_summary"] = text
    with pytest.raises(ValueError):
        compile_report(raw, {source["snapshot_id"]: SnapshotMarketFacts(source)})


@pytest.mark.parametrize("text", [
    "SMA 50 and EMA 10.", "Lookback 252 daily observations.",
    "Analysis date 2026-10-07.", "A 4-week research horizon.",
    "No calibrated percentage forecast is available.",
])
def test_dates_periods_and_qualitative_prose_not_financial_amounts(text):
    assert not unsupported_financial_numbers(text, ())


@pytest.mark.parametrize("text", ["Return 30%.", "Value $30.", "Value USD 30."])
def test_existing_symbol_and_money_refusal_retained(text):
    assert unsupported_financial_numbers(text, ())
