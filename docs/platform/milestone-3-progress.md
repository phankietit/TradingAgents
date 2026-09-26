# Milestone 3 implementation and verification tracker

Scope: PLAN-030 through PLAN-037. PLAN-038 remains outside this milestone.
Base: `f76c353ee912e6d6d16ff1ba660287a6a383a291`.
Branch: `feature/TA-030-analysis-engine`.

Final acceptance update: the owner approved manual/local security review in
place of sealed plugin output. Local PostgreSQL regression and scoped manual
security gates PASS at `ebc954c`; see the top of the verification receipt.
Earlier plugin/CI blockers below are historical and superseded by these owner
decisions. Merge remains subject to the actual PR receipt, not test counts alone.

Delivery update: [PR #3](https://github.com/phankietit/TradingAgents/pull/3)
is open as a draft against `main`. Initial remote head `a7909fc` matches the
local candidate and GitHub reports MERGEABLE with no hosted checks/runs.
Actions remains disabled. Push/workflow permission is no longer a blocker
after withdrawing the workflow diff. Security report finalization remains
BLOCKED; no merge or milestone-complete claim has been made.

Policy update, 2026-09-27: the owner now requires local/manual verification
instead of hosted CI. Repository Actions is disabled. The new M3 workflow
changes are withdrawn and `scripts/verify-local.sh` provides the local gate.
See [local policy](local-verification.md). Earlier hosted-CI blocker statements
below are historical; they do not authorize spending or re-enabling Actions.

The integrated local suite at `8364663` passed 1207 tests with 2 optional skips
and 88 subtests, including PostgreSQL. Clean non-editable platform installation,
installed imports/worker smoke, lint and diff checks also pass. See
[candidate evidence](milestone-3-verification.md). This is **not yet completion**:
GitHub rejected the branch push because OAuth lacks `workflow` scope; no PR
exists, CI and merge remain blocked, and security source review is not finished.

Follow-up at `a96ff29`: old-SHA security source review has completed and surfaced
functional gaps, not confirmed security vulnerabilities. Fixed observation
cutoffs at pure replay/evidence/readiness boundaries and approval/cancel races.
Full local suite now passes 1200 tests/88 subtests with 19 skips (PostgreSQL
not running plus two optional providers). The sealed old-SHA scan reports
partial coverage due to retained checkpoint metadata; new candidate review
and PostgreSQL/clean-install refresh remain required. See the verification
receipt for all remaining functional and evidence tasks.

## Remaining completion checks

Latest runtime checkpoint: `129696b` passes 1228 tests and 88 subtests with
PostgreSQL (2 optional provider skips). Snapshot asset guidance, exception log
redaction, UTC compatibility and research-receipt lifecycle regression tests are
implemented. Installed package refresh/smoke and scoped dependency/secret checks
pass. Post-fix source review evidence is saved, but its report finalization
failed and remains BLOCKED. See the verification receipt's requirement table
for exact evidence and limitations. Cross-version CI and PR/merge remain
BLOCKED by missing GitHub `workflow` authorization; milestone is incomplete.

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
  risk/evaluation persistence verification passes.
- PLAN-034: timestamped/quality-checked quotes, explicit freshness limits,
  simultaneous-event sequencing, complete event/quote hashes and deterministic
  snapshot IDs are implemented. SQLite tests verify immutable writes and owner
  isolation. The valuation service now resolves hash-verified owner snapshots,
  enforces source cutoffs and raw-close pricing, and persists replay idempotently.
  PostgreSQL persisted valuation replay and owner isolation pass.
- PLAN-035: validate classification/correlation coverage, reconciled accounting,
  effective policy and all limits. Coverage fixes now have targeted regression
  tests; snapshot-worker integration now covers the decision factory through
  readiness and owner approval. PostgreSQL risk/approval replay passes.
- PLAN-036: readiness, matching policy, owner/run source checks, idempotent
  events and transactional projection writes now have SQLite integration tests.
  Authenticated state/transition API wiring is covered by tests for sessions,
  CSRF, actor spoofing, policy mismatch, state projection and retry behavior.
  Ready writes/approvals now recompute risk against an owner-scoped portfolio,
  policy and instrument master, rejecting forged checks/weights. Correlation
  replays hash-verified owner/run-bound daily price snapshots under explicit
  policy windows/freshness; SQLite covers multi-asset approval and source bypass
  rejection. Concurrent PostgreSQL approval/rejection and identical-event retry
  validation pass; exactly one audit event is persisted.
- PLAN-037: hash-verified snapshot outcome helper, duplicate/future outcome
  rejection, canonical ordering and deterministic evaluation IDs have targeted
  tests. Caller-supplied returns remain `reproducible=False`. Owner-scoped
  persisted receipt replay now reconstructs successful snapshot-attested runs,
  owner sources and calendar windows with idempotent artifact persistence and
  verification tests. Calendar integration uses a pinned exchange
  calendar library, verifies asset/benchmark alignment, and hashes exact session
  windows into outcomes; tests cover DST, holidays, early closes and 24/7 data.
- PostgreSQL upgrade/schema parity/rollback, persistence integration, clean
  installation and full regression pass. Scoped security review remains.
- README and changelog are updated and candidate evidence is recorded. Obtain
  GitHub workflow permission, create/review the fork PR, verify CI and merge only
  after all in-scope gates pass.

No production readiness or performance claim follows from this tracker.
