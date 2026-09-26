"""Deterministic decision state transitions with human-approval enforcement."""

from __future__ import annotations

from tradingagents.contracts import (
    DecisionCandidate,
    DecisionLifecycleEvent,
    DecisionStatus,
)
from tradingagents.contracts.decisions import require_decision_readiness

TRANSITIONS = {
    DecisionStatus.DRAFT: {DecisionStatus.REVIEW, DecisionStatus.READY_FOR_APPROVAL},
    DecisionStatus.REVIEW: {
        DecisionStatus.READY_FOR_APPROVAL,
        DecisionStatus.REJECTED,
        DecisionStatus.EXPIRED,
    },
    DecisionStatus.READY_FOR_APPROVAL: {
        DecisionStatus.REVIEW,
        DecisionStatus.APPROVED,
        DecisionStatus.REJECTED,
        DecisionStatus.EXPIRED,
    },
    DecisionStatus.APPROVED: set(),
    DecisionStatus.REJECTED: set(),
    DecisionStatus.EXPIRED: set(),
}


class DecisionLifecycle:
    def apply(
        self,
        decision: DecisionCandidate,
        events: tuple[DecisionLifecycleEvent, ...],
    ) -> DecisionStatus:
        status = decision.status
        last_time = decision.as_of
        seen = set()
        for event in sorted(events, key=lambda item: (item.occurred_at, str(item.event_id))):
            event = DecisionLifecycleEvent.model_validate(event.model_dump())
            if event.event_id in seen:
                raise ValueError("duplicate lifecycle event")
            seen.add(event.event_id)
            if event.decision_id != decision.decision_id or event.owner_id != decision.owner_id:
                raise ValueError("lifecycle event does not belong to the decision owner")
            if event.occurred_at < last_time:
                raise ValueError("lifecycle event time cannot move backwards")
            if event.from_status is not status:
                raise ValueError("lifecycle event from_status does not match current status")
            if event.to_status not in TRANSITIONS[status]:
                raise ValueError(f"invalid decision transition {status.value} -> {event.to_status.value}")
            if event.to_status in {DecisionStatus.READY_FOR_APPROVAL, DecisionStatus.APPROVED}:
                require_decision_readiness(decision)
            if event.to_status is DecisionStatus.APPROVED and {
                (check.policy_id, check.policy_version) for check in decision.policy_checks
            } != {(event.policy_id, event.policy_version)}:
                raise ValueError("approval policy does not match evaluated policy")
            status = event.to_status
            last_time = event.occurred_at
        return status
