from datetime import date
from uuid import uuid4

import pytest

from tradingagents.agents.utils.agent_utils import build_instrument_context
from tradingagents.contracts import AssetClass, InstrumentContract, Tradability
from tradingagents.platform.analysis import AnalysisEngine, AnalysisRequest


def _instrument(asset_class, symbol, tradability=Tradability.INVESTABLE):
    return InstrumentContract(
        instrument_id=uuid4(),
        symbol=symbol,
        canonical_symbol=symbol,
        display_name=symbol,
        asset_class=asset_class,
        tradability=tradability,
        venue="CME" if asset_class is AssetClass.REFERENCE_FUTURE else "NASDAQ",
        quote_currency="USD",
        timezone="UTC" if asset_class is AssetClass.CRYPTO else "America/New_York",
        session_calendar="24/7" if asset_class is AssetClass.CRYPTO else "XNYS",
    )


class FakeGraph:
    calls = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def propagate(self, *args, **kwargs):
        self.calls.append((self.kwargs, args, kwargs))
        return {}, "REVIEW"


@pytest.mark.unit
@pytest.mark.parametrize(
    ("asset_class", "symbol", "tradability", "analysts", "asset_type"),
    [
        (AssetClass.EQUITY, "AAPL", Tradability.INVESTABLE,
         ("market", "social", "news", "fundamentals"), "stock"),
        (AssetClass.ETF, "SPY", Tradability.INVESTABLE, ("market", "news"), "etf"),
        (AssetClass.CRYPTO, "BTC-USD", Tradability.INVESTABLE,
         ("market", "social", "news"), "crypto"),
        (AssetClass.REFERENCE_FUTURE, "NQ=F", Tradability.REFERENCE_ONLY,
         ("market", "news"), "reference"),
    ],
)
def test_default_profile_selects_asset_specific_analysts(
    asset_class, symbol, tradability, analysts, asset_type
):
    FakeGraph.calls.clear()
    result = AnalysisEngine(base_config={}, graph_factory=FakeGraph).analyze(
        AnalysisRequest(
            instrument=_instrument(asset_class, symbol, tradability),
            analysis_date=date(2026, 9, 25),
        )
    )
    init, _args, kwargs = FakeGraph.calls[-1]
    assert init["selected_analysts"] == analysts
    assert kwargs["asset_type"] == asset_type
    assert result.reference_only is (tradability is Tradability.REFERENCE_ONLY)


@pytest.mark.unit
def test_etf_rejects_company_fundamentals_analyst():
    request = AnalysisRequest(
        instrument=_instrument(AssetClass.ETF, "SPY"),
        analysis_date=date(2026, 9, 25),
        selected_analysts=("market", "fundamentals"),
    )
    with pytest.raises(ValueError, match="not allowed"):
        AnalysisEngine(base_config={}, graph_factory=FakeGraph).analyze(request)


@pytest.mark.unit
def test_crypto_scope_is_allowlisted():
    request = AnalysisRequest(
        instrument=_instrument(AssetClass.CRYPTO, "DOGE-USD"),
        analysis_date=date(2026, 9, 25),
    )
    with pytest.raises(ValueError, match="BTC-USD and ETH-USD"):
        AnalysisEngine(base_config={}, graph_factory=FakeGraph).analyze(request)


@pytest.mark.unit
def test_prompt_context_states_etf_and_reference_boundaries():
    assert "Do not apply company balance-sheet reasoning" in build_instrument_context(
        "SPY", "etf"
    )
    assert "reference-only" in build_instrument_context("NQ=F", "reference")
