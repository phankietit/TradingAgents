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
        if self.status in {DecisionStatus.DRAFT, DecisionStatus.REVIEW} and self.rating is not DecisionRating.REVIEW:
            raise ValueError("review decisions must use the Review rating")
        if self.status not in {DecisionStatus.DRAFT, DecisionStatus.REVIEW} and self.rating is DecisionRating.REVIEW:
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
