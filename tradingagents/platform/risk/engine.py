"""Versioned deterministic checks; model prose has no input to this engine."""

from __future__ import annotations

from decimal import Decimal
from math import isclose
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from tradingagents.contracts import (
    AssetClass,
    DataQualityStatus,
    PolicyCheck,
    PolicyContract,
    PolicyResult,
    PortfolioSnapshot,
    Tradability,
)

Ratio = Annotated[float, Field(ge=0.0, le=1.0)]


class RiskLimits(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    max_position_weight: Ratio
    max_asset_class_weight: Ratio
    max_gross_exposure: Ratio
    max_turnover: Ratio
    max_correlation: Annotated[float, Field(ge=-1.0, le=1.0)]
    min_cash_weight: Ratio


class RiskProposal(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    instrument_id: UUID
    asset_class: AssetClass
    tradability: Tradability
    target_weight: Ratio
    data_quality: DataQualityStatus
    position_asset_classes: dict[UUID, AssetClass]
    correlations: dict[UUID, Annotated[float, Field(ge=-1.0, le=1.0, allow_inf_nan=False)]] = Field(default_factory=dict)


class RiskAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    policy_id: UUID
    policy_version: str
    checks: tuple[PolicyCheck, ...]
    max_allowed_weight: Ratio
    passed: bool


class RiskEngine:
    def evaluate(
        self,
        *,
        portfolio: PortfolioSnapshot,
        proposal: RiskProposal,
        policy: PolicyContract,
    ) -> RiskAssessment:
        portfolio = PortfolioSnapshot.model_validate(portfolio.model_dump())
        proposal = RiskProposal.model_validate(proposal.model_dump())
        policy = PolicyContract.model_validate(policy.model_dump())
        if policy.owner_id != portfolio.owner_id:
            raise ValueError("policy and portfolio owners must match")
        if policy.asset_class is not proposal.asset_class:
            raise ValueError("policy asset class does not match the proposal")
        if policy.effective_at > portfolio.as_of:
            raise ValueError("policy is not effective at the portfolio as_of")
        self._validate_accounting(portfolio)
        limits = RiskLimits.model_validate(policy.parameters)
        weights = {position.instrument_id: float(position.weight) for position in portfolio.positions}
        current = weights.get(proposal.instrument_id, 0.0)
        projected = dict(weights)
        projected[proposal.instrument_id] = proposal.target_weight
        classes = dict(proposal.position_asset_classes)
        if classes.get(proposal.instrument_id, proposal.asset_class) is not proposal.asset_class:
            raise ValueError("proposal instrument has conflicting asset classifications")
        classes[proposal.instrument_id] = proposal.asset_class
        missing_classes = {key for key, weight in projected.items() if weight > 0 and key not in classes}
        class_weight = sum(
            weight
            for instrument_id, weight in projected.items()
            if classes.get(instrument_id) is proposal.asset_class
        )
        gross = sum(projected.values())
        base_cash = sum(
            (balance.amount for balance in portfolio.cash if balance.currency == portfolio.base_currency),
            start=0,
        )
        cash_weight = float(base_cash / portfolio.net_asset_value) if portfolio.net_asset_value else 0.0
        projected_cash = cash_weight - (proposal.target_weight - current)
        turnover = abs(proposal.target_weight - current)
        required_correlations = {
            key for key, weight in weights.items()
            if weight > 0 and key != proposal.instrument_id and proposal.target_weight > 0
        }
        missing_correlations = required_correlations - proposal.correlations.keys()
        material_correlations = [proposal.correlations[key] for key in required_correlations if key in proposal.correlations]
        max_correlation = max(material_correlations, default=-1.0)

        checks = (
            self._check(policy, "data_quality", proposal.data_quality is DataQualityStatus.OK,
                        proposal.data_quality.value, DataQualityStatus.OK.value),
            self._check(policy, "tradability", proposal.tradability is Tradability.INVESTABLE and proposal.asset_class in {AssetClass.EQUITY, AssetClass.ETF, AssetClass.CRYPTO},
                        proposal.tradability.value, Tradability.INVESTABLE.value),
            self._check(policy, "max_position_weight", proposal.target_weight <= limits.max_position_weight,
                        proposal.target_weight, limits.max_position_weight),
            self._check(policy, "max_asset_class_weight", None if missing_classes else class_weight <= limits.max_asset_class_weight,
                        None if missing_classes else class_weight, limits.max_asset_class_weight),
            self._check(policy, "max_gross_exposure", gross <= limits.max_gross_exposure,
                        gross, limits.max_gross_exposure),
            self._check(policy, "max_turnover", turnover <= limits.max_turnover,
                        turnover, limits.max_turnover),
            self._check(policy, "max_correlation", None if missing_correlations else max_correlation <= limits.max_correlation,
                        None if missing_correlations else max_correlation, limits.max_correlation),
            self._check(policy, "min_cash_weight", projected_cash >= limits.min_cash_weight,
                        projected_cash, limits.min_cash_weight),
        )
        passed = all(check.result is PolicyResult.PASS for check in checks)
        return RiskAssessment(
            policy_id=policy.policy_id,
            policy_version=policy.policy_version,
            checks=checks,
            max_allowed_weight=0.0 if not passed else min(
                limits.max_position_weight,
                max(0.0, limits.max_asset_class_weight - (class_weight - proposal.target_weight)),
                max(0.0, current + limits.max_turnover),
                max(0.0, limits.max_gross_exposure - (gross - proposal.target_weight)),
                max(0.0, current + cash_weight - limits.min_cash_weight),
            ),
            passed=passed,
        )

    @staticmethod
    def _validate_accounting(portfolio: PortfolioSnapshot) -> None:
        if portfolio.net_asset_value <= 0:
            raise ValueError("risk evaluation requires positive NAV")
        currencies = [balance.currency for balance in portfolio.cash]
        if len(currencies) != len(set(currencies)) or any(currency != portfolio.base_currency for currency in currencies):
            raise ValueError("risk evaluation requires unique base-currency cash")
        total = sum((balance.amount for balance in portfolio.cash), Decimal(0))
        for position in portfolio.positions:
            if position.quantity * position.market_price != position.market_value:
                raise ValueError("position value does not reconcile")
            if not isclose(position.weight, float(position.market_value / portfolio.net_asset_value), rel_tol=1e-12, abs_tol=1e-12):
                raise ValueError("position weight does not reconcile")
            total += position.market_value
        if total != portfolio.net_asset_value:
            raise ValueError("portfolio NAV does not reconcile")

    @staticmethod
    def _check(policy, check_id, passed, observed, limit) -> PolicyCheck:
        result = PolicyResult.REVIEW if passed is None else PolicyResult.PASS if passed else PolicyResult.FAIL
        return PolicyCheck(
            check_id=check_id,
            policy_id=policy.policy_id,
            policy_version=policy.policy_version,
            result=result,
            blocking=True,
            reason=f"{check_id}: missing coverage" if passed is None else f"{check_id} {result.value}",
            observed_value=observed,
            limit_value=limit,
        )
