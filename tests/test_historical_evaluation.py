from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from tradingagents.contracts import (
    DataQualityStatus,
    DecisionCandidate,
    DecisionRating,
    DecisionStatus,
)
from tradingagents.platform.evaluation import EvaluationObservation, HistoricalEvaluationService

NOW = datetime(2026, 9, 25, tzinfo=UTC)
HASH = "sha256:" + "a" * 64


def _decision(rating=DecisionRating.BUY, status=DecisionStatus.READY_FOR_APPROVAL):
    if rating is DecisionRating.REVIEW:
        status = DecisionStatus.REVIEW
    return DecisionCandidate(
        decision_id=uuid4(), run_id=uuid4(), owner_id=uuid4(), instrument_id=uuid4(),
        as_of=NOW, status=status, rating=rating, confidence=0.7,
        thesis="Thesis", risks=("Risk",), invalidation_conditions=("Invalidation",),
        evidence=(), data_quality=DataQualityStatus.OK, policy_checks=(),
    )


def _observation(decision, **overrides):
    values = {
        "decision_id": decision.decision_id,
        "evaluated_at": NOW + timedelta(days=7),
        "holding_period_days": 5,
        "raw_return": 0.04,
        "benchmark_return": 0.01,
        "outcome_snapshot_ids": (uuid4(),),
        "outcome_hash": HASH,
    }
    values.update(overrides)
    return EvaluationObservation(**values)


@pytest.mark.unit
def test_evaluation_is_reproducible_and_scores_independent_decisions():
    buy, sell = _decision(), _decision(DecisionRating.SELL)
    result = HistoricalEvaluationService().build(
        decisions=(buy, sell),
        observations=(_observation(buy), _observation(sell, raw_return=-0.03)),
        universe=("AAPL", "MSFT"), benchmark="SPY", config_hash=HASH,
        created_at=NOW + timedelta(days=8),
    )
    assert result.scored_cells == 2
    assert result.directional_hit_rate == 1.0
    assert result.input_hash.startswith("sha256:")
    assert result.portfolio_performance_claim is False


@pytest.mark.unit
def test_review_is_counted_but_never_scored():
    review = _decision(DecisionRating.REVIEW)
    result = HistoricalEvaluationService().build(
        decisions=(review,), observations=(_observation(review),),
        universe=("AAPL",), benchmark="SPY", config_hash=HASH,
        created_at=NOW + timedelta(days=8),
    )
    assert result.review_cells == 1
    assert result.scored_cells == 0
    assert result.directional_hit_rate is None


@pytest.mark.unit
def test_outcome_known_at_or_before_decision_is_rejected():
    decision = _decision()
    with pytest.raises(ValueError, match="after the decision"):
        HistoricalEvaluationService().build(
            decisions=(decision,), observations=(_observation(decision, evaluated_at=NOW),),
            universe=("AAPL",), benchmark="SPY", config_hash=HASH,
            created_at=NOW + timedelta(days=8),
        )


def test_duplicate_cells_and_future_outcomes_are_rejected():
    decision = _decision()
    observation = _observation(decision)
    common = {"universe": ("AAPL",), "benchmark": "SPY", "config_hash": HASH,
              "created_at": NOW + timedelta(days=8)}
    with pytest.raises(ValueError, match="duplicate decision"):
        HistoricalEvaluationService().build(decisions=(decision, decision), observations=(), **common)
    with pytest.raises(ValueError, match="duplicate outcome"):
        HistoricalEvaluationService().build(decisions=(decision,), observations=(observation, observation), **common)
    with pytest.raises(ValueError, match="future"):
        HistoricalEvaluationService().build(decisions=(decision,), observations=(observation,),
                                             **{**common, "created_at": NOW + timedelta(days=1)})


def test_evaluation_hash_does_not_depend_on_input_order():
    first, second = _decision(), _decision()
    observations = (_observation(first), _observation(second))
    common = {"benchmark": "SPY", "config_hash": HASH, "created_at": NOW + timedelta(days=8)}
    one = HistoricalEvaluationService().build(decisions=(first, second), observations=observations,
                                               universe=("AAPL", "MSFT"), **common)
    two = HistoricalEvaluationService().build(decisions=(second, first), observations=tuple(reversed(observations)),
                                               universe=("MSFT", "AAPL"), **common)
    assert one == two
    assert one.reproducible is False  # caller-supplied returns are not verified source replay
