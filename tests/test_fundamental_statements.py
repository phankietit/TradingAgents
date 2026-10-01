import re

import pytest

from tradingagents.agents.research_schemas import LocalizedResearchReport
from tradingagents.agents.utils.fundamental_statements import METRICS, fundamental_statement
from tradingagents.dataflows.sec_edgar import _STATEMENTS


@pytest.mark.parametrize("metric", METRICS)
@pytest.mark.parametrize("frequency", ["annual", "quarterly"])
def test_all_supported_sec_metrics_have_exact_units_period_and_bilingual_numeric_parity(metric, frequency):
    unit = "usd_per_share" if metric == "diluted_eps" else "usd_millions"
    fact_id = f"sec.{metric}.{frequency}.2025-09-27.{unit}"
    en = fundamental_statement(fact_id, "-100.25")
    vi = fundamental_statement(fact_id, "-100.25", vi=True)
    assert "2025-09-27" in en and "2025-09-27" in vi
    assert ("per share" if metric == "diluted_eps" else "million") in en
    assert ("USD/cổ phiếu" if metric == "diluted_eps" else "triệu USD") in vi
    LocalizedResearchReport(en=en, vi=vi)


def test_renderer_covers_existing_sec_adapter_without_guessing_new_metrics():
    adapter = {re.sub(r"[^a-z0-9]+", "_", metric.lower()).strip("_")
               for statement in _STATEMENTS.values() for metric, _ in statement}
    assert adapter == set(METRICS)


@pytest.mark.parametrize("fact_id", [
    "sec.total_assets.annual.2025-09-27.usd_per_share",
    "sec.diluted_eps.annual.2025-09-27.usd_millions",
    "sec.total_assets.annual.2025-99-27.usd_millions",
    "sec.invented.annual.2025-09-27.usd_millions",
    "sec.revenue.monthly.2025-09-27.usd_millions",
    "sec.revenue.annual.2025-09-27.usd_billions",
])
def test_unsupported_sec_identity_cannot_be_rendered(fact_id):
    with pytest.raises(ValueError):
        fundamental_statement(fact_id, "100.00")


def test_balance_instant_is_not_described_as_income_over_a_period():
    assert "as of" in fundamental_statement("sec.total_assets.annual.2025-09-27.usd_millions", "100.00")
    assert "period ended" in fundamental_statement("sec.revenue.annual.2025-09-27.usd_millions", "100.00")
    assert fundamental_statement("latest.close", "100.00") is None
