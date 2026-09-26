# Milestone 3 implementation and verification tracker

Scope: PLAN-030 through PLAN-037. PLAN-038 remains outside this milestone.
Base: `f76c353ee912e6d6d16ff1ba660287a6a383a291`.
Branch: `feature/TA-030-analysis-engine`.

The initial ticket commits provide services and contracts. They are **not yet
completion evidence** for the integrated milestone. The full local suite at
`587f449` passed 1082 tests with 14 skips; that result does not establish the
following missing integration and correctness requirements.

## Remaining completion checks

- PLAN-030/031: connect the adapter to the durable worker path; verify real
  graph profile/tool enforcement, snapshot context, and CLI compatibility.
- PLAN-032: connect validated structured graph output to the candidate factory;
  require evidence and deterministic policy results before approval readiness;
  preserve compatibility for previously persisted review candidates.
- PLAN-033: validate snapshot identity, source eligibility and graph hash;
  establish deterministic identifiers and persistence with owner/run scope.
- PLAN-034: validate valuation timestamps, transaction ordering, finite decimal
  amounts and complete event hashes; test durable ledger owner isolation,
  idempotency and immutable history.
- PLAN-035: validate classification/correlation coverage, reconciled accounting,
  effective policy and all limits. Coverage fixes now have targeted regression
  tests; integration with the decision factory remains to be verified.
- PLAN-036: enforce policy/evidence readiness on each transition and enforce
  authorization, serialization and audit in the persistence/API write path.
  A pure lifecycle replay test is insufficient proof of approval enforcement.
- PLAN-037: derive outcomes from validated immutable price snapshots and
  calendars; reject duplicate/future outcomes; verify deterministic replay.
- Run PostgreSQL upgrade/schema parity/rollback, persistence integration,
  clean installation, full regression and scoped security checks after fixes.
- Update README, consolidate the changelog, produce a candidate-SHA receipt,
  create/review the fork PR and merge only after all in-scope gates pass.

No production readiness or performance claim follows from this tracker.
