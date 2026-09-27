# M4 verification ledger

This ledger consolidates current evidence; historical ticket checkpoints in
`milestone-4-plan.md` and `web/README.md` are not final acceptance declarations.
M4 delivery status: **UNVERIFIED** until the remaining acceptance and merge gates
below are satisfied. No production deployment or live trading is in scope.

## PostgreSQL regression — 2026-09-27

- Source: clean `feature/TA-M4-local-web-ui`,
  `d062746c948e3b7d9bdd82771eb97b1ae2e19ab0`.
- Environment: macOS, Python 3.14.7, PostgreSQL 16.14 (`postgres:16-alpine`).
  External SSD verified before work. Dedicated container
  `ta-m4-qa-d062746`, ownership label `codex.task=tradingagents-m4-d062746`,
  loopback-only ephemeral port, tmpfs database. Other containers were untouched.
- Command: `TA_ALLOW_TEST_DB_RESET=1 bash scripts/verify-local.sh --postgres`
  with the disposable database URL supplied locally (not stored here).
- **PASS**: Ruff, installed dependency consistency, whitespace checks,
  **1274 tests + 88 subtests**, 37.60 seconds; 22 warnings.
- **UNVERIFIED**: optional Bedrock dependency test (not installed), live DeepSeek
  test (credential withheld by local verification script). These two skips are
  not failures of PostgreSQL and are not promoted to provider verification.
- Coverage includes migration/schema parity/rollback, owner isolation, durable
  jobs, concurrent watchlist writes, concurrent approval/idempotency, persisted
  ledger/evaluation replay, snapshots and temporal data contracts.
- Additional test-only patch asserts persisted valuation receipt fingerprint,
  exact price/source identity and foreign-owner denial in the PostgreSQL ledger
  test. `pytest tests/test_milestone3_postgresql.py -q`: **6 PASS**, 4.47 seconds;
  Ruff PASS. No application code changed after the clean full-regression run.
- GitHub repository Actions permission read via `gh api`: `enabled=false`.
  No workflow run was triggered or required.

## Evidence already implemented (scope matters)

- Built loopback web/API, session/CSRF, watchlist and source discovery: implemented
  with API/component tests and local browser evidence in `web/README.md`.
- AAPL real queue/worker/DB pipeline with synthetic graph, risk evaluation,
  explicit approval and reload: local integration PASS. No live LLM evidence.
- Stocks/ETF/crypto/reference charts, backend benchmark metrics, saved screener,
  reports/evidence/decision links: local fixtures verified, not live market proof.
- Persisted processing states and attempt count survive browser reload.
- New portfolio valuations retain immutable source receipts; old snapshots are
  not backfilled. Missing receipts stay unavailable, not inferred from current data.
- Model configuration disclosure explicitly reports service/provider liveness as
  UNVERIFIED. It is not an authenticated connectivity or capability probe.
- Latest frontend checkpoint: 74 tests, lint/typecheck/build PASS. Precise decimal
  display, invalid portfolio/policy responses and view-level recovery are tested;
  injected render failures have component evidence, not browser evidence yet.

## Remaining M4 acceptance gates

1. **UNVERIFIED — finance-first final UX:** all four workspaces must meet the
   owner brief, not only screener/date controls. Finish readable source/status
   and decision/risk language; tuck diagnostics away without hiding warnings.
   Verify desktop/narrow layouts and routine use without internal IDs/JSON.
2. **UNVERIFIED — browser failure matrix:** complete and record actual browser
   evidence for session expiry, failed/invalid output, unavailable/stale data,
   cancellation/new attempt, approval failure/conflict and recovery. Existing
   unit/API evidence remains useful but is not a substitute for browser checks.
3. **UNVERIFIED — final candidate verification:** rerun frontend/backend gates
   on the final code candidate; isolated non-editable install/import/CLI smoke;
   final manual security, dependency and tracked-secret review with findings.
4. **UNVERIFIED — delivery documentation:** reconcile README, CHANGELOG, startup,
   ingestion/cadence guidance and ticket statuses with actual runtime behavior.
5. **UNVERIFIED — PR and merge:** fetch/compare current main, create/attach PR,
   review exact diff, resolve findings, merge and verify merged tree plus Actions
   remaining disabled. Never infer completion from this intermediate ledger.

No owner decision is currently blocking these local implementation/QA steps.
Paid-provider tests, public hosting and broker actions remain outside authorization.
