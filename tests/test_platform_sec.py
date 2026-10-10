"""SEC platform adapter retains filed vintage and does not invent coverage."""

from datetime import datetime
from uuid import uuid4

import pytest

from tests.test_price_preparation import AAPL
from tradingagents._compat import UTC
from tradingagents.contracts import DataQualityStatus
from tradingagents.dataflows.platform_sec import SecPreparationError, collect_sec_facts
from tradingagents.platform.instruments.catalog import INITIAL_INSTRUMENT_CATALOG

NOW = datetime(2026, 10, 1, 12, tzinfo=UTC)


def fact(value, filed, *, end="2025-09-27", start=None, form="10-K", accn="0000320193-26-000001"):
    row = {"end": end, "val": value, "filed": filed, "form": form, "accn": accn}
    if start:
        row["start"] = start
    return row


def document(rows, *, revenue=None):
    gaap = {"Assets": {"units": {"USD": rows}}}
    if revenue is not None:
        gaap["RevenueFromContractWithCustomerExcludingAssessedTax"] = {
            "units": {"USD": revenue}}
    return {"cik": 320193, "facts": {"us-gaap": gaap}}


def collect(doc, *, now=NOW):
    return collect_sec_facts(AAPL, clock=lambda: now,
        fetch_cik=lambda _: "0000320193", fetch_facts=lambda _: doc)


def test_sec_filed_vintage_restated_only_after_amendment_and_not_by_period_end():
    doc = document([
        fact(100, "2025-11-01"),
        fact(105, "2026-11-01", form="10-K/A"),
    ])
    current = collect(doc)
    assert current.quality_status is DataQualityStatus.OK
    assert len(current.facts) == 1
    assert current.facts[0].value == 100
    assert current.facts[0].filed_at.isoformat() == "2025-11-01"
    later = collect(doc, now=datetime(2026, 12, 1, 12, tzinfo=UTC))
    assert later.facts[0].value == 105
    before_filing = collect(doc, now=datetime(2025, 10, 1, 12, tzinfo=UTC))
    assert before_filing.quality_status is DataQualityStatus.NO_DATA


def test_sec_quarter_not_confused_with_ytd_and_alternate_tag_not_summed():
    doc = document([], revenue=[
        fact(81, "2026-01-29", end="2025-12-31", start="2025-10-01", form="10-Q"),
        fact(159, "2026-01-29", end="2025-12-31", start="2025-07-01", form="10-Q"),
    ])
    result = collect(doc)
    assert [(item.metric, item.frequency, item.value) for item in result.facts] == [
        ("Revenue", "quarterly", 81)]


def test_sec_malformed_fact_is_invalid_not_partial_ok():
    result = collect(document([fact(100, "2025-11-01"), {"filed": "2025-11-01"}]))
    assert result.quality_status is DataQualityStatus.INVALID
    assert result.invalid_records == 1
    assert result.facts == ()


def test_sec_non_equity_or_unapproved_symbol_has_no_fallback():
    spy = INITIAL_INSTRUMENT_CATALOG[1].instrument
    with pytest.raises(SecPreparationError, match="unsupported"):
        collect_sec_facts(spy, fetch_cik=lambda _: "0000320193")


def test_sec_live_path_requires_real_contact_not_placeholder(monkeypatch):
    monkeypatch.delenv("SEC_EDGAR_USER_AGENT", raising=False)
    with pytest.raises(SecPreparationError, match="unavailable"):
        collect_sec_facts(AAPL)
    monkeypatch.setenv("SEC_EDGAR_USER_AGENT", "TradingAgents (contact@example.com)")
    with pytest.raises(SecPreparationError, match="unavailable"):
        collect_sec_facts(AAPL)


def test_sec_final_quantity_binding_uses_filed_fact_and_explicit_millions_unit():
    from types import SimpleNamespace

    from tests.test_report_compiler import draft
    from tests.test_report_localization import translated_blocks
    from tradingagents.agents.utils.report_compiler import compile_report
    from tradingagents.agents.utils.report_localization import localize_report
    from tradingagents.platform.analysis.fundamental_facts import SnapshotFundamentalFacts
    from tradingagents.platform.analysis.research_validation import validate_canonical_report

    collection = collect(document([fact(100_000_000, "2025-11-01")]))
    snapshot_id = str(uuid4())
    source = {"snapshot_id": snapshot_id,
        "provenance": {"dataset": "fundamentals", "vendor": "sec_edgar",
            "instrument_id": str(AAPL.instrument_id),
            "retrieved_at": collection.retrieved_at.isoformat()},
        "data": collection.model_dump(mode="json")}
    facts = SnapshotFundamentalFacts(source)
    raw, _ = draft()
    raw["investment_thesis"] = [{"claim": "{{QA}}. Coverage excludes unreported tags.",
        "snapshot_ids": [snapshot_id]}]
    raw["risks"] = [{"claim": "Other disclosures require review.", "snapshot_ids": [snapshot_id]}]
    raw["invalidation_conditions"] = [{"claim": "If the filing is amended, reassess.",
        "snapshot_ids": [snapshot_id]}]
    raw["quantity_bindings"] = [{"key": "QA", "snapshot_id": snapshot_id,
        "fact_id": "sec.total_assets.annual.2025-09-27.usd_millions", "decimal_places": 2}]
    result = compile_report(raw, {snapshot_id: facts})
    assert "Total assets as of 2025-09-27, reported in the annual filing: USD 100.00 million." in result.investment_thesis
    assert result.observed_numbers[0].value == 100
    validate_canonical_report(result, {snapshot_id: facts}, {snapshot_id})
    original = result.model_dump()

    class Model:
        def with_structured_output(self, schema):
            return SimpleNamespace(invoke=lambda prompt: schema(blocks=translated_blocks(prompt)))

        def invoke(self, _):
            pytest.fail("valid protected SEC statement must not trigger repair")

    localized = localize_report(Model(), result, [])
    assert "Tổng tài sản tại ngày 2025-09-27, theo báo cáo năm: 100.00 triệu USD." in localized.vi
    assert "USD 100.00 million" not in localized.vi
    assert "100.00 triệu USD.." not in localized.vi
    assert result.model_dump() == original


@pytest.mark.parametrize("claim", [
    "Reported assets were ${{QA}} billion.",
    "Reported assets were ${{QA}} per share.",
    "Quarterly revenue was ${{QA}} million.",
    "Assets for the current quarter were ${{QA}} million.",
])
def test_sec_bound_scalar_cannot_change_unit_metric_or_reporting_period(claim):
    from tests.test_report_compiler import draft
    from tradingagents.agents.utils.report_compiler import compile_report
    from tradingagents.platform.analysis.fundamental_facts import SnapshotFundamentalFacts
    from tradingagents.platform.analysis.research_validation import PublicationValidationError

    collection = collect(document([fact(100_000_000, "2025-11-01")]))
    snapshot_id = str(uuid4())
    source = {"snapshot_id": snapshot_id,
        "provenance": {"dataset": "fundamentals", "vendor": "sec_edgar",
            "instrument_id": str(AAPL.instrument_id),
            "retrieved_at": collection.retrieved_at.isoformat()},
        "data": collection.model_dump(mode="json")}
    raw, _ = draft()
    raw["investment_thesis"] = [{"claim": claim, "snapshot_ids": [snapshot_id]}]
    raw["risks"] = [{"claim": "Other disclosures require review.", "snapshot_ids": [snapshot_id]}]
    raw["invalidation_conditions"] = [{"claim": "If the filing is amended, reassess.",
        "snapshot_ids": [snapshot_id]}]
    raw["quantity_bindings"] = [{"key": "QA", "snapshot_id": snapshot_id,
        "fact_id": "sec.total_assets.annual.2025-09-27.usd_millions", "decimal_places": 2}]
    with pytest.raises(PublicationValidationError) as failure:
        compile_report(raw, {snapshot_id: SnapshotFundamentalFacts(source)})
    assert failure.value.issues == ("fundamental_statement_requires_standalone_anchor",)
    assert failure.value.binding_keys == ("QA",)
