# Decision lifecycle

Decision state changes are append-only audit events. The deterministic lifecycle
supports draft/review/readiness followed by owner approval, rejection, or
expiry. Every event records actor, reason, timestamp, and the exact policy
version where applicable.

Only the matching human owner may transition a decision to `approved`; terminal
states cannot be reopened. Approval records no order and does not create a
broker or execution path.
