from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from tests.decision_fixtures import ready_inputs
from tradingagents.contracts import (
    DataQualityStatus,
    DecisionActorType,
    DecisionCandidate,
    DecisionLifecycleEvent,
    DecisionRating,
    DecisionStatus,
)
from tradingagents.platform.decisions import DecisionLifecycle

NOW = datetime(2026, 9, 25, tzinfo=UTC)


def _decision(owner_id):
    return DecisionCandidate(
        decision_id=uuid4(), run_id=uuid4(), as_of=NOW,
        status=DecisionStatus.READY_FOR_APPROVAL, rating=DecisionRating.BUY,
        confidence=0.7, thesis="Thesis", risks=("Risk",),
        invalidation_conditions=("Invalidation",),
        data_quality=DataQualityStatus.OK, **ready_inputs(owner_id),
    )


def _approval(decision, **overrides):
    values = {
        "event_id": uuid4(), "decision_id": decision.decision_id,
        "owner_id": decision.owner_id,
        "from_status": DecisionStatus.READY_FOR_APPROVAL,
        "to_status": DecisionStatus.APPROVED,
        "actor_id": decision.owner_id, "actor_type": DecisionActorType.OWNER,
        "reason": "Owner reviewed evidence and policy results",
        "occurred_at": NOW + timedelta(minutes=1),
        "policy_id": decision.policy_checks[0].policy_id,
        "policy_version": decision.policy_checks[0].policy_version,
    }
    values.update(overrides)
    return DecisionLifecycleEvent(**values)


@pytest.mark.unit
def test_only_owner_can_approve_with_exact_policy_version():
    decision = _decision(uuid4())
    event = _approval(decision)
    assert DecisionLifecycle().apply(decision, (event,)) is DecisionStatus.APPROVED
    with pytest.raises(ValidationError, match="human owner"):
        _approval(decision, actor_type=DecisionActorType.SYSTEM, actor_id=None)
    with pytest.raises(ValidationError, match="policy version"):
        _approval(decision, policy_id=None, policy_version=None)


@pytest.mark.unit
def test_terminal_decision_cannot_transition_again():
    decision = _decision(uuid4())
    approved = _approval(decision)
    second = approved.model_copy(update={
        "event_id": uuid4(), "from_status": DecisionStatus.APPROVED,
        "to_status": DecisionStatus.REVIEW,
        "occurred_at": NOW + timedelta(minutes=2),
    })
    with pytest.raises(ValueError, match="invalid decision transition"):
        DecisionLifecycle().apply(decision, (approved, second))


@pytest.mark.unit
def test_cross_owner_event_is_rejected():
    decision = _decision(uuid4())
    other_owner = uuid4()
    event = _approval(decision).model_copy(update={"owner_id": other_owner, "actor_id": other_owner})
    with pytest.raises(ValueError, match="does not belong"):
        DecisionLifecycle().apply(decision, (event,))


@pytest.mark.parametrize("missing", ["evidence", "policy_checks", "target_weight"])
def test_lifecycle_cannot_approve_incomplete_legacy_candidate(missing):
    decision = _decision(uuid4())
    event = _approval(decision)
    decision = decision.model_copy(update={missing: None if missing == "target_weight" else ()})
    with pytest.raises(ValueError, match="requires"):
        DecisionLifecycle().apply(decision, (event,))


def test_approval_cannot_substitute_policy_version():
    decision = _decision(uuid4())
    with pytest.raises(ValueError, match="does not match"):
        DecisionLifecycle().apply(decision, (_approval(decision, policy_version="invented"),))
