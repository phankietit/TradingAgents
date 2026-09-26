# Decision lifecycle

Decision state changes are append-only audit events. The deterministic lifecycle
supports draft/review/readiness followed by owner approval, rejection, or
expiry. Every event records actor, reason, timestamp, and the exact policy
version where applicable.

Only the matching human owner may transition a decision to `approved`; terminal
states cannot be reopened. Approval records no order and does not create a
broker or execution path.

Approval readiness requires nonempty dated evidence, deterministic weights and
the complete set of blocking risk checks from one policy version. Older v1
review records with a narrative rating remain readable, but must satisfy the
same readiness checks before transition. New invalid/incomplete factory results
use `REVIEW` and withhold target weight.

The repository serializes event writes on the decision row, compares the
expected status/version, and writes the projection and event in one transaction.
Retries with the same event ID/content are idempotent. Readiness and approval
transitions validate source identities/hashes/times against persisted run
snapshots and resolve the policy by owner and version. Concurrent PostgreSQL
verification and authenticated API integration remain milestone gates.
