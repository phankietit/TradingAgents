# Milestone 3 implementation and verification tracker

Scope: PLAN-030 through PLAN-037. PLAN-038 remains outside this milestone.
Base: `f76c353ee912e6d6d16ff1ba660287a6a383a291`.
Branch: `feature/TA-030-analysis-engine`.

The initial ticket commits provide services and contracts. They are **not yet
completion evidence** for the integrated milestone. The full local suite at
`37d9193` passed 1124 tests with 14 skips and 88 subtests; that result predates
the structured graph bridge and does not establish the
following missing integration and correctness requirements.

## Remaining completion checks

- PLAN-030/031: durable research handler now runs AnalysisEngine and atomically
  persists report plus REVIEW candidate, with idempotent completion recovery
  and cancellation tests. A snapshot-only engine/real graph path now validates
  source bytes/times and disables live tools/memory/logs. Worker snapshot
  selection and evidence/risk orchestration are now connected through immutable
  run inputs and the authenticated API. The worker command supports one-shot
  and continuous processing with explicit private storage; empty-queue smoke
  and shutdown tests pass. Long calls now renew leases;
  publication uses a transaction-level lease/cancellation fence, with tests for
  reclaim races and renewal-thread cleanup.
- PLAN-032: PM structured payload is now retained separately from CLI prose;
  AnalysisEngine validates the narrative and rejects missing/extra fields.
  Durable handler passes this payload to the candidate factory. Snapshot runs
  require exact thesis/risk/invalidation source claims and deterministic policy
  checks; offline integration covers readiness then owner approval. Legacy tool
  reads remain unattested, so legacy-mode candidates intentionally remain REVIEW;
  evidence/complete policy checks/weights are now required at factory readiness;
  previously persisted review candidates remain readable.
- PLAN-033: deterministic IDs/hash, source-time validation and owner/run-bound
  artifact persistence are implemented. Worker integration now persists evidence
  alongside candidates, with invalid citations routed to REVIEW. PostgreSQL
  verification remains.
- PLAN-034: timestamped/quality-checked quotes, explicit freshness limits,
  simultaneous-event sequencing, complete event/quote hashes and deterministic
  snapshot IDs are implemented. SQLite tests verify immutable writes and owner
  isolation. The valuation service now resolves hash-verified owner snapshots,
  enforces source cutoffs and raw-close pricing, and persists replay idempotently.
  PostgreSQL evidence remains.
- PLAN-035: validate classification/correlation coverage, reconciled accounting,
  effective policy and all limits. Coverage fixes now have targeted regression
  tests; snapshot-worker integration now covers the decision factory through
  readiness and owner approval. PostgreSQL verification remains.
- PLAN-036: readiness, matching policy, owner/run source checks, idempotent
  events and transactional projection writes now have SQLite integration tests.
  Authenticated state/transition API wiring is covered by tests for sessions,
  CSRF, actor spoofing, policy mismatch, state projection and retry behavior.
  Ready writes/approvals now recompute risk against an owner-scoped portfolio,
  policy and instrument master, rejecting forged checks/weights. Correlation
  replays hash-verified owner/run-bound daily price snapshots under explicit
  policy windows/freshness; SQLite covers multi-asset approval and source bypass
  rejection. Concurrent PostgreSQL validation remains.
- PLAN-037: hash-verified snapshot outcome helper, duplicate/future outcome
  rejection, canonical ordering and deterministic evaluation IDs have targeted
  tests. Caller-supplied returns remain `reproducible=False`. Owner-scoped
  persisted replay remains. Calendar integration now uses a pinned exchange
  calendar library, verifies asset/benchmark alignment, and hashes exact session
  windows into outcomes; tests cover DST, holidays, early closes and 24/7 data.
- Run PostgreSQL upgrade/schema parity/rollback, persistence integration,
  clean installation, full regression and scoped security checks after fixes.
- Update README, consolidate the changelog, produce a candidate-SHA receipt,
  create/review the fork PR and merge only after all in-scope gates pass.

No production readiness or performance claim follows from this tracker.
