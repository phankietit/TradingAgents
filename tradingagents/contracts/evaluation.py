"""Reproducible historical decision-evaluation contracts."""

from __future__ import annotations

from uuid import UUID

from pydantic import AwareDatetime, Field, model_validator

from .base import ContentHash, NonEmptyText, VersionedContract


class DecisionEvaluation(VersionedContract):
    decision_id: UUID
    evaluated_at: AwareDatetime
    holding_period_days: int = Field(gt=0)
    raw_return: float = Field(ge=-1, allow_inf_nan=False)
    benchmark_return: float = Field(ge=-1, allow_inf_nan=False)
    alpha_return: float = Field(allow_inf_nan=False)
    outcome_snapshot_ids: tuple[UUID, ...] = Field(min_length=1)
    outcome_hash: ContentHash
    directional_hit: bool | None


class HistoricalEvaluation(VersionedContract):
    evaluation_id: UUID
    created_at: AwareDatetime
    universe: tuple[NonEmptyText, ...] = Field(min_length=1)
    period_start: AwareDatetime
    period_end: AwareDatetime
    benchmark: NonEmptyText
    config_hash: ContentHash
    input_hash: ContentHash
    cells: tuple[DecisionEvaluation, ...]
    scored_cells: int = Field(ge=0)
    review_cells: int = Field(ge=0)
    directional_hit_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    reproducible: bool = False
    portfolio_performance_claim: bool = False

    @model_validator(mode="after")
    def enforce_evaluation_boundary(self):
        if self.period_start > self.period_end:
            raise ValueError("evaluation period_start must not exceed period_end")
        if self.portfolio_performance_claim:
            raise ValueError("independent decision evaluation is not portfolio performance")
        if self.scored_cells != len(self.cells):
            raise ValueError("scored_cells must equal the number of settled cells")
        return self
