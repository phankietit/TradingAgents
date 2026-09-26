from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from tradingagents.contracts import (
    AssetClass,
    DataQualityStatus,
    PolicyContract,
    PolicyResult,
    PortfolioSnapshot,
    Tradability,
)
from tradingagents.platform.risk import RiskEngine, RiskProposal

NOW = datetime(2026, 9, 25, tzinfo=UTC)


def _portfolio(owner_id, instrument_id):
    return PortfolioSnapshot(
        portfolio_id=uuid4(), owner_id=owner_id, as_of=NOW, base_currency="USD",
        cash=({"currency": "USD", "amount": Decimal("600")},),
        positions=({"instrument_id": instrument_id, "quantity": Decimal("4"),
                    "market_price": Decimal("100"), "market_value": Decimal("400"),
                    "weight": 0.4},), net_asset_value=Decimal("1000"),
        content_hash="sha256:" + "a" * 64,
    )


def _policy(owner_id):
    return PolicyContract(
        policy_id=uuid4(), owner_id=owner_id, name="Owner equity limits",
        policy_version="2026-09-25", asset_class=AssetClass.EQUITY,
        effective_at=NOW, parameters={
            "max_position_weight": 0.5, "max_asset_class_weight": 0.8,
            "max_gross_exposure": 0.9, "max_turnover": 0.2,
            "max_correlation": 0.8, "min_cash_weight": 0.1,
        },
    )


@pytest.mark.unit
def test_risk_engine_evaluates_all_deterministic_policy_dimensions():
    owner_id, held_id, proposed_id = uuid4(), uuid4(), uuid4()
    proposal = RiskProposal(
        instrument_id=proposed_id, asset_class=AssetClass.EQUITY,
        tradability=Tradability.INVESTABLE, target_weight=0.15,
        data_quality=DataQualityStatus.OK,
        position_asset_classes={held_id: AssetClass.EQUITY, proposed_id: AssetClass.EQUITY},
        correlations={held_id: 0.5},
    )
    assessment = RiskEngine().evaluate(
        portfolio=_portfolio(owner_id, held_id), proposal=proposal, policy=_policy(owner_id)
    )
    assert assessment.passed is True
    assert {check.check_id for check in assessment.checks} == {
        "data_quality", "tradability", "max_position_weight", "max_asset_class_weight",
        "max_gross_exposure", "max_turnover", "max_correlation", "min_cash_weight",
    }


@pytest.mark.unit
def test_failed_data_and_limits_cannot_be_overridden_by_narrative():
    owner_id, held_id, proposed_id = uuid4(), uuid4(), uuid4()
    proposal = RiskProposal(
        instrument_id=proposed_id, asset_class=AssetClass.EQUITY,
        tradability=Tradability.INVESTABLE, target_weight=0.5,
        data_quality=DataQualityStatus.STALE,
        position_asset_classes={held_id: AssetClass.EQUITY, proposed_id: AssetClass.EQUITY},
        correlations={held_id: 0.95},
    )
    assessment = RiskEngine().evaluate(
        portfolio=_portfolio(owner_id, held_id), proposal=proposal, policy=_policy(owner_id)
    )
    failed = {c.check_id for c in assessment.checks if c.result is PolicyResult.FAIL}
    assert {"data_quality", "max_asset_class_weight", "max_turnover", "max_correlation"} <= failed
    assert assessment.passed is False


@pytest.mark.unit
def test_reference_future_is_always_blocked_from_portfolio_proposal():
    owner_id, held_id = uuid4(), uuid4()
    policy = _policy(owner_id).model_copy(update={"asset_class": AssetClass.REFERENCE_FUTURE})
    proposal = RiskProposal(
        instrument_id=uuid4(), asset_class=AssetClass.REFERENCE_FUTURE,
        tradability=Tradability.REFERENCE_ONLY, target_weight=0.05,
        data_quality=DataQualityStatus.OK,
        position_asset_classes={held_id: AssetClass.EQUITY},
    )
    assessment = RiskEngine().evaluate(
        portfolio=_portfolio(owner_id, held_id), proposal=proposal, policy=policy
    )
    assert next(c for c in assessment.checks if c.check_id == "tradability").result is PolicyResult.FAIL
