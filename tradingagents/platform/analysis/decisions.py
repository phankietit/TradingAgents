"""Strict conversion of untrusted model output into decision candidates."""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID, uuid4

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, ValidationError

from tradingagents.contracts import (
    DataQualityStatus,
    DecisionCandidate,
    DecisionRating,
    DecisionStatus,
    EvidenceReference,
    PolicyCheck,
)
from tradingagents.contracts.base import NonEmptyText
from tradingagents.contracts.decisions import require_decision_readiness


class StructuredDecisionNarrative(BaseModel):
    """Fields an LLM may author; portfolio math is intentionally absent."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    rating: DecisionRating
    confidence: float = Field(ge=0.0, le=1.0)
    thesis: str = Field(min_length=1, max_length=20_000)
    risks: tuple[NonEmptyText, ...] = Field(min_length=1)
    invalidation_conditions: tuple[NonEmptyText, ...] = Field(min_length=1)

    def model_post_init(self, __context: Any) -> None:
        if self.rating is DecisionRating.REVIEW:
            raise ValueError("the model cannot self-authorize the Review fallback")


class DecisionCandidateFactory:
    """Fail closed when model output is absent, malformed, or overreaching."""

    def build(
        self,
        *,
        raw_output: str | dict[str, Any],
        run_id: UUID,
        owner_id: UUID,
        instrument_id: UUID,
        as_of: AwareDatetime,
        evidence: tuple[EvidenceReference, ...],
        data_quality: DataQualityStatus,
        policy_checks: tuple[PolicyCheck, ...] = (),
        current_weight: float | None = None,
        target_weight: float | None = None,
        max_allowed_weight: float | None = None,
        decision_id: UUID | None = None,
    ) -> DecisionCandidate:
        try:
            payload = json.loads(raw_output) if isinstance(raw_output, str) else raw_output
            narrative = StructuredDecisionNarrative.model_validate(payload)
        except (json.JSONDecodeError, TypeError, ValidationError, ValueError) as exc:
            return DecisionCandidate(
                decision_id=decision_id or uuid4(),
                run_id=run_id,
                owner_id=owner_id,
                instrument_id=instrument_id,
                as_of=as_of,
                status=DecisionStatus.REVIEW,
                rating=DecisionRating.REVIEW,
                confidence=0.0,
                thesis="Structured decision unavailable; manual review is required.",
                risks=(f"Schema validation failed: {type(exc).__name__}",),
                invalidation_conditions=("Supply a schema-valid decision payload.",),
                evidence=evidence,
                data_quality=data_quality,
                current_weight=current_weight,
                target_weight=None,
                max_allowed_weight=max_allowed_weight,
                policy_checks=policy_checks,
            )

        status = DecisionStatus.READY_FOR_APPROVAL
        if data_quality is not DataQualityStatus.OK or any(
            check.blocking and check.result.value != "PASS" for check in policy_checks
        ):
            status = DecisionStatus.REVIEW
        if status is DecisionStatus.REVIEW:
            return DecisionCandidate(
                decision_id=decision_id or uuid4(),
                run_id=run_id,
                owner_id=owner_id,
                instrument_id=instrument_id,
                as_of=as_of,
                status=status,
                rating=DecisionRating.REVIEW,
                confidence=0.0,
                thesis=narrative.thesis,
                risks=narrative.risks,
                invalidation_conditions=narrative.invalidation_conditions,
                evidence=evidence,
                data_quality=data_quality,
                current_weight=current_weight,
                target_weight=None,
                max_allowed_weight=max_allowed_weight,
                policy_checks=policy_checks,
            )
        candidate = DecisionCandidate(
            decision_id=decision_id or uuid4(),
            run_id=run_id,
            owner_id=owner_id,
            instrument_id=instrument_id,
            as_of=as_of,
            status=status,
            rating=narrative.rating,
            confidence=narrative.confidence,
            thesis=narrative.thesis,
            risks=narrative.risks,
            invalidation_conditions=narrative.invalidation_conditions,
            evidence=evidence,
            data_quality=data_quality,
            current_weight=current_weight,
            target_weight=target_weight,
            max_allowed_weight=max_allowed_weight,
            policy_checks=policy_checks,
        )
        try:
            require_decision_readiness(candidate)
        except ValueError:
            return DecisionCandidate.model_validate({
                **candidate.model_dump(), "status": DecisionStatus.REVIEW,
                "rating": DecisionRating.REVIEW, "target_weight": None,
            })
        return candidate
