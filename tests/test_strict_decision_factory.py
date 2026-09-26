from datetime import datetime
from uuid import uuid4

import pytest

from tests.decision_fixtures import ready_inputs
from tradingagents._compat import UTC
from tradingagents.contracts import DataQualityStatus, DecisionRating, DecisionStatus
from tradingagents.platform.analysis import DecisionCandidateFactory

NOW = datetime(2026, 9, 25, tzinfo=UTC)


def _build(raw_output, **overrides):
    values = {
        "raw_output": raw_output,
        "run_id": uuid4(),
        "owner_id": uuid4(),
        "instrument_id": uuid4(),
        "as_of": NOW,
        "evidence": (),
        "data_quality": DataQualityStatus.OK,
    }
    values.update(overrides)
    return DecisionCandidateFactory().build(**values)


@pytest.mark.unit
def test_valid_structured_narrative_is_ready_but_still_requires_human_approval():
    decision = _build({
        "rating": "Buy",
        "confidence": 0.7,
        "thesis": "Evidence-backed thesis",
        "risks": ["Valuation"],
        "invalidation_conditions": ["Trend reversal"],
    }, **ready_inputs())
    assert decision.status is DecisionStatus.READY_FOR_APPROVAL
    assert decision.rating is DecisionRating.BUY
    assert decision.requires_human_approval is True


@pytest.mark.unit
@pytest.mark.parametrize(
    "payload",
    [
        "not-json",
        {"rating": "Buy"},
        {
            "rating": "Buy",
            "confidence": 0.7,
            "thesis": "x",
            "risks": ["r"],
            "invalidation_conditions": ["i"],
            "target_weight": 0.9,
        },
    ],
)
def test_invalid_or_overreaching_output_fails_closed_to_review(payload):
    decision = _build(payload, target_weight=0.05)
    assert decision.status is DecisionStatus.REVIEW
    assert decision.rating is DecisionRating.REVIEW
    assert decision.target_weight is None


@pytest.mark.unit
def test_bad_data_quality_cannot_become_approval_ready():
    decision = _build(
        {
            "rating": "Hold",
            "confidence": 0.5,
            "thesis": "Insufficient fresh data",
            "risks": ["Staleness"],
            "invalidation_conditions": ["Fresh snapshot arrives"],
        },
        data_quality=DataQualityStatus.STALE,
    )
    assert decision.status is DecisionStatus.REVIEW
    assert decision.rating is DecisionRating.REVIEW


@pytest.mark.parametrize("missing", ["evidence", "policy_checks", "target_weight"])
def test_valid_narrative_without_required_readiness_stays_review(missing):
    inputs = ready_inputs()
    inputs[missing] = None if missing == "target_weight" else ()
    decision = _build({"rating": "Buy", "confidence": 0.7, "thesis": "Thesis",
                       "risks": ["Risk"], "invalidation_conditions": ["Invalidation"]}, **inputs)
    assert decision.status is DecisionStatus.REVIEW
    assert decision.target_weight is None
