from datetime import date
from uuid import uuid4

import pytest

from tradingagents.contracts import AssetClass, InstrumentContract, Tradability
from tradingagents.platform.analysis import AnalysisEngine, AnalysisRequest


def _instrument(asset_class=AssetClass.EQUITY):
    return InstrumentContract(
        instrument_id=uuid4(),
        symbol="BTC-USD" if asset_class is AssetClass.CRYPTO else "AAPL",
        canonical_symbol="BTC-USD" if asset_class is AssetClass.CRYPTO else "AAPL",
        display_name="Bitcoin" if asset_class is AssetClass.CRYPTO else "Apple",
        asset_class=asset_class,
        tradability=Tradability.INVESTABLE,
        venue="aggregate" if asset_class is AssetClass.CRYPTO else "NASDAQ",
        quote_currency="USD",
        timezone="UTC" if asset_class is AssetClass.CRYPTO else "America/New_York",
        session_calendar="24/7" if asset_class is AssetClass.CRYPTO else "XNYS",
    )


@pytest.mark.unit
def test_analysis_engine_wraps_graph_without_changing_legacy_contract():
    calls = {}

    class FakeGraph:
        def __init__(self, **kwargs):
            calls["init"] = kwargs

        def propagate(self, *args, **kwargs):
            calls["propagate"] = (args, kwargs)
            return {"final_trade_decision": "Rating: Hold"}, "Hold"

    request = AnalysisRequest(
        instrument=_instrument(),
        analysis_date=date(2026, 9, 25),
        selected_analysts=("market", "news"),
        config_overrides={"max_debate_rounds": 1},
    )
    result = AnalysisEngine(
        base_config={"max_debate_rounds": 2}, graph_factory=FakeGraph
    ).analyze(request)

    assert calls["init"]["selected_analysts"] == ("market", "news")
    assert calls["init"]["config"]["max_debate_rounds"] == 1
    assert calls["propagate"] == (("AAPL", "2026-09-25"), {"asset_type": "stock", "portfolio": None})
    assert result.narrative_signal == "Hold"


@pytest.mark.unit
def test_analysis_engine_routes_crypto_through_existing_crypto_mode():
    calls = {}

    class FakeGraph:
        def __init__(self, **_kwargs):
            pass

        def propagate(self, *args, **kwargs):
            calls["propagate"] = (args, kwargs)
            return {}, "REVIEW"

    request = AnalysisRequest(
        instrument=_instrument(AssetClass.CRYPTO),
        analysis_date=date(2026, 9, 25),
        selected_analysts=("market",),
    )
    AnalysisEngine(base_config={}, graph_factory=FakeGraph).analyze(request)
    assert calls["propagate"][1]["asset_type"] == "crypto"
