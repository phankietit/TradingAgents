"""Versioned deterministic checks; model prose has no input to this engine."""

from __future__ import annotations

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
    correlations: dict[UUID, float] = Field(default_factory=dict)


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
        if policy.owner_id != portfolio.owner_id:
            raise ValueError("policy and portfolio owners must match")
        if policy.asset_class is not proposal.asset_class:
            raise ValueError("policy asset class does not match the proposal")
        limits = RiskLimits.model_validate(policy.parameters)
        weights = {position.instrument_id: float(position.weight) for position in portfolio.positions}
        current = weights.get(proposal.instrument_id, 0.0)
        projected = dict(weights)
        projected[proposal.instrument_id] = proposal.target_weight
        class_weight = sum(
            weight
            for instrument_id, weight in projected.items()
            if proposal.position_asset_classes.get(instrument_id) is proposal.asset_class
        )
        gross = sum(projected.values())
        base_cash = sum(
            (balance.amount for balance in portfolio.cash if balance.currency == portfolio.base_currency),
            start=0,
        )
        cash_weight = float(base_cash / portfolio.net_asset_value) if portfolio.net_asset_value else 0.0
        projected_cash = cash_weight - max(0.0, proposal.target_weight - current)
        turnover = abs(proposal.target_weight - current)
        material_correlations = [
            value
            for instrument_id, value in proposal.correlations.items()
            if weights.get(instrument_id, 0.0) > 0
        ]
        max_correlation = max(material_correlations, default=-1.0)

        checks = (
            self._check(policy, "data_quality", proposal.data_quality is DataQualityStatus.OK,
                        proposal.data_quality.value, DataQualityStatus.OK.value),
            self._check(policy, "tradability", proposal.tradability is Tradability.INVESTABLE,
                        proposal.tradability.value, Tradability.INVESTABLE.value),
            self._check(policy, "max_position_weight", proposal.target_weight <= limits.max_position_weight,
                        proposal.target_weight, limits.max_position_weight),
            self._check(policy, "max_asset_class_weight", class_weight <= limits.max_asset_class_weight,
                        class_weight, limits.max_asset_class_weight),
            self._check(policy, "max_gross_exposure", gross <= limits.max_gross_exposure,
                        gross, limits.max_gross_exposure),
            self._check(policy, "max_turnover", turnover <= limits.max_turnover,
                        turnover, limits.max_turnover),
            self._check(policy, "max_correlation", max_correlation <= limits.max_correlation,
                        max_correlation, limits.max_correlation),
            self._check(policy, "min_cash_weight", projected_cash >= limits.min_cash_weight,
                        projected_cash, limits.min_cash_weight),
        )
        passed = all(check.result is PolicyResult.PASS for check in checks)
        return RiskAssessment(
            policy_id=policy.policy_id,
            policy_version=policy.policy_version,
            checks=checks,
            max_allowed_weight=min(
                limits.max_position_weight,
                max(0.0, limits.max_asset_class_weight - (class_weight - proposal.target_weight)),
                max(0.0, current + limits.max_turnover),
            ),
            passed=passed,
        )

    @staticmethod
    def _check(policy, check_id, passed, observed, limit) -> PolicyCheck:
        return PolicyCheck(
            check_id=check_id,
            policy_id=policy.policy_id,
            policy_version=policy.policy_version,
            result=PolicyResult.PASS if passed else PolicyResult.FAIL,
            blocking=True,
            reason=f"{check_id} {'passed' if passed else 'failed'}",
            observed_value=observed,
            limit_value=limit,
        )
