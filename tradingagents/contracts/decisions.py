"""Structured decision candidate contract at the LLM/policy boundary."""

from __future__ import annotations

from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, Field, model_validator

from .base import NonEmptyText, VersionedContract, Weight
from .data import DataQualityStatus, EvidenceReference
from .policy import PolicyCheck, PolicyResult


class DecisionRating(str, Enum):
    REVIEW = "Review"
    BUY = "Buy"
    OVERWEIGHT = "Overweight"
    HOLD = "Hold"
    UNDERWEIGHT = "Underweight"
    SELL = "Sell"


class DecisionStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    READY_FOR_APPROVAL = "ready_for_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class DecisionActorType(str, Enum):
    OWNER = "owner"
    SYSTEM = "system"


class DecisionLifecycleEvent(VersionedContract):
    event_id: UUID
    decision_id: UUID
    owner_id: UUID
    from_status: DecisionStatus
    to_status: DecisionStatus
    actor_id: UUID | None = None
    actor_type: DecisionActorType
    reason: NonEmptyText
    occurred_at: AwareDatetime
    policy_id: UUID | None = None
    policy_version: str | None = Field(default=None, min_length=1, max_length=64)

    @model_validator(mode="after")
    def validate_audit_authority(self):
        if self.actor_type is DecisionActorType.OWNER and self.actor_id != self.owner_id:
            raise ValueError("owner lifecycle action requires the matching owner actor")
        if self.to_status is DecisionStatus.APPROVED:
            if self.actor_type is not DecisionActorType.OWNER:
                raise ValueError("only the human owner may approve a decision")
            if self.policy_id is None or self.policy_version is None:
                raise ValueError("approval requires the exact policy version")
        return self


class DecisionCandidate(VersionedContract):
    decision_id: UUID
    run_id: UUID
    owner_id: UUID
    instrument_id: UUID
    as_of: AwareDatetime
    status: DecisionStatus
    rating: DecisionRating
    confidence: float = Field(ge=0.0, le=1.0)
    thesis: NonEmptyText
    risks: tuple[NonEmptyText, ...]
    invalidation_conditions: tuple[NonEmptyText, ...]
    evidence: tuple[EvidenceReference, ...]
    data_quality: DataQualityStatus
    current_weight: Weight | None = None
    target_weight: Weight | None = None
    max_allowed_weight: Weight | None = None
    policy_checks: tuple[PolicyCheck, ...]
    requires_human_approval: Literal[True] = True

    @model_validator(mode="after")
    def enforce_decision_boundary(self):
        # V1 persisted review records may contain a narrative rating. Keep them
        # readable, but readiness is enforced separately at every write/approval
        # boundary. A narrative rating alone never grants approval authority.
        if self.status in {DecisionStatus.READY_FOR_APPROVAL, DecisionStatus.APPROVED} and self.rating is DecisionRating.REVIEW:
            raise ValueError("Review rating requires review status")
        if (
            self.target_weight is not None
            and self.max_allowed_weight is not None
            and self.target_weight > self.max_allowed_weight
        ):
            raise ValueError("target_weight must not exceed max_allowed_weight")
        if self.status in {DecisionStatus.READY_FOR_APPROVAL, DecisionStatus.APPROVED}:
            if self.data_quality is not DataQualityStatus.OK:
                raise ValueError("approval-ready decisions require OK data quality")
            if any(check.blocking and check.result is not PolicyResult.PASS for check in self.policy_checks):
                raise ValueError("blocking policy checks must pass before approval")
        return self


REQUIRED_RISK_CHECKS = frozenset({
    "data_quality", "tradability", "max_position_weight", "max_asset_class_weight",
    "max_gross_exposure", "max_turnover", "max_correlation", "min_cash_weight",
})


def require_decision_readiness(decision: DecisionCandidate) -> None:
    """Validate readiness without rewriting historical V1 serialized records."""
    if decision.rating is DecisionRating.REVIEW or decision.data_quality is not DataQualityStatus.OK:
        raise ValueError("decision is not eligible for approval")
    if not decision.evidence or not decision.risks or not decision.invalidation_conditions:
        raise ValueError("decision requires evidence, risks and invalidation conditions")
    evidence_ids = [item.evidence_id for item in decision.evidence]
    if len(evidence_ids) != len(set(evidence_ids)):
        raise ValueError("duplicate decision evidence")
    if any(item.source_at is None or item.source_at > decision.as_of or item.observed_at < item.source_at for item in decision.evidence):
        raise ValueError("decision evidence is not point-in-time eligible")
    if any(value is None for value in (decision.current_weight, decision.target_weight, decision.max_allowed_weight)):
        raise ValueError("decision requires deterministic weights")
    checks = {item.check_id: item for item in decision.policy_checks}
    if len(checks) != len(decision.policy_checks) or not checks.keys() >= REQUIRED_RISK_CHECKS:
        raise ValueError("decision requires complete unique risk checks")
    if any(not checks[key].blocking or checks[key].result is not PolicyResult.PASS for key in REQUIRED_RISK_CHECKS):
        raise ValueError("all required risk checks must pass and be blocking")
    if any(item.blocking and item.result is not PolicyResult.PASS for item in decision.policy_checks):
        raise ValueError("blocking policy failure")
    if len({(item.policy_id, item.policy_version) for item in decision.policy_checks}) != 1:
        raise ValueError("risk checks must reference one exact policy version")
