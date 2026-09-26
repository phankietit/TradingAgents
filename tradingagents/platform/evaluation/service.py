"""Build reproducible independent-cell decision evaluations."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from uuid import NAMESPACE_URL, UUID, uuid5

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from tradingagents.contracts import (
    DecisionCandidate,
    DecisionEvaluation,
    DecisionRating,
    HistoricalEvaluation,
)


class EvaluationObservation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    decision_id: UUID
    evaluated_at: AwareDatetime
    holding_period_days: int = Field(gt=0)
    raw_return: float = Field(ge=-1, allow_inf_nan=False)
    benchmark_return: float = Field(ge=-1, allow_inf_nan=False)
    outcome_snapshot_ids: tuple[UUID, ...] = Field(min_length=1)
    outcome_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")


class HistoricalEvaluationService:
    def build(
        self,
        *,
        decisions: tuple[DecisionCandidate, ...],
        observations: tuple[EvaluationObservation, ...],
        universe: tuple[str, ...],
        benchmark: str,
        config_hash: str,
        created_at: datetime,
        evaluation_id: UUID | None = None,
    ) -> HistoricalEvaluation:
        if not decisions:
            raise ValueError("historical evaluation requires at least one decision")
        if not universe:
            raise ValueError("historical evaluation requires a non-empty universe")
        if created_at.tzinfo is None or created_at.utcoffset() is None:
            raise ValueError("evaluation clock requires timezone")
        decisions = tuple(DecisionCandidate.model_validate(item.model_dump()) for item in decisions)
        observations = tuple(EvaluationObservation.model_validate(item.model_dump()) for item in observations)
        decisions = tuple(sorted(decisions, key=lambda item: str(item.decision_id)))
        observations = tuple(sorted(observations, key=lambda item: str(item.decision_id)))
        universe = tuple(sorted(universe))
        if len(universe) != len(set(universe)):
            raise ValueError("duplicate universe symbols")
        by_decision = {decision.decision_id: decision for decision in decisions}
        if len(by_decision) != len(decisions):
            raise ValueError("duplicate decision ids")
        if len({item.decision_id for item in observations}) != len(observations):
            raise ValueError("duplicate outcome cells")
        if any(item.as_of > created_at for item in decisions):
            raise ValueError("decision is future to the evaluation clock")
        cells: list[DecisionEvaluation] = []
        reviews = sum(1 for decision in decisions if decision.rating is DecisionRating.REVIEW)
        for observation in observations:
            decision = by_decision.get(observation.decision_id)
            if decision is None:
                raise ValueError("observation references an unknown decision")
            if observation.evaluated_at <= decision.as_of:
                raise ValueError("outcome must become knowable after the decision as_of")
            if observation.evaluated_at > created_at:
                raise ValueError("outcome is future to the evaluation clock")
            if len(observation.outcome_snapshot_ids) != len(set(observation.outcome_snapshot_ids)):
                raise ValueError("duplicate outcome snapshots")
            if decision.rating is DecisionRating.REVIEW:
                continue
            alpha = observation.raw_return - observation.benchmark_return
            cells.append(
                DecisionEvaluation(
                    decision_id=decision.decision_id,
                    evaluated_at=observation.evaluated_at,
                    holding_period_days=observation.holding_period_days,
                    raw_return=observation.raw_return,
                    benchmark_return=observation.benchmark_return,
                    alpha_return=alpha,
                    outcome_snapshot_ids=observation.outcome_snapshot_ids,
                    outcome_hash=observation.outcome_hash,
                    directional_hit=self._directional_hit(decision.rating, alpha),
                )
            )
        hits = [cell.directional_hit for cell in cells if cell.directional_hit is not None]
        period_start = min(decision.as_of for decision in decisions)
        period_end = max(cell.evaluated_at for cell in cells) if cells else max(
            decision.as_of for decision in decisions
        )
        canonical = {
            "decisions": [decision.model_dump(mode="json") for decision in decisions],
            "observations": [observation.model_dump(mode="json") for observation in observations],
            "universe": universe,
            "benchmark": benchmark,
            "config_hash": config_hash,
        }
        input_hash = "sha256:" + hashlib.sha256(
            json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        return HistoricalEvaluation(
            evaluation_id=evaluation_id or uuid5(NAMESPACE_URL, "tradingagents:evaluation:" + input_hash),
            created_at=created_at,
            universe=universe,
            period_start=period_start,
            period_end=period_end,
            benchmark=benchmark,
            config_hash=config_hash,
            input_hash=input_hash,
            cells=tuple(cells),
            scored_cells=len(cells),
            review_cells=reviews,
            directional_hit_rate=sum(hits) / len(hits) if hits else None,
            reproducible=False,
        )

    @staticmethod
    def _directional_hit(rating: DecisionRating, alpha: float) -> bool | None:
        if rating in {DecisionRating.BUY, DecisionRating.OVERWEIGHT}:
            return alpha > 0
        if rating in {DecisionRating.SELL, DecisionRating.UNDERWEIGHT}:
            return alpha < 0
        return None
