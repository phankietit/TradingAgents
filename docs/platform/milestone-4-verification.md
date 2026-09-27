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

## Non-editable installation — 2026-09-27

- Source: clean `feature/TA-M4-local-web-ui`,
  `a5f4574effdabd7a7255b79b0486a1435b4c82a6`; Python 3.14.7 on macOS.
- Fresh venv in external managed run
  `/Volumes/Data/codex-builds/TradingAgents/feature-TA-M4-local-web-ui/20260927T002717Z-16831`.
  Temporary files and pip cache stayed within this run. Installation used
  `pip install '/absolute/path/to/TradingAgents[platform]'`, not editable mode.
  Install log and resolved dependency snapshot are retained under `Logs/`.
- **PASS:** `pip check`; imports of `tradingagents`, `cli.main`, API runtime and
  worker runtime from installed `site-packages`, checked with isolated Python
  (`-I`) outside the source checkout; CLI and worker `--help` entrypoints.
- **PASS:** installed migrations on a new disposable SQLite file; API test-client
  `/health/live` and `/health/ready` return 200; separately built `web/dist`
  serves HTML at `/`; anonymous `/api/v1/runs` returns 401; empty worker processes
  no job; migration rollback succeeds. No owner database was accessed.
- Scope: packaging/import and local in-process smoke, not browser/network-server,
  PostgreSQL, paid-provider or fresh-dependency full-regression proof. The web
  build remains a separate operator artifact, not part of the Python wheel.

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
- Latest frontend checkpoint: 83 tests, lint/typecheck/build PASS. Precise decimal
  display, invalid portfolio/policy responses and view-level recovery are tested;
  injected render failures have component evidence, not browser evidence yet.

## Decision identity and concurrent review — 2026-09-27

- Source: `cf8009f` plus accompanying `Decisions.tsx` and test changes.
  Candidate identity must match the selected decision before display or actions.
  Approval additionally requires matching run ID, instrument and as-of timestamp;
  backend approval validation remains authoritative. Tests cover wrong decision,
  each mismatched run field and a valid matching run. No risk rule was loosened.
- **PASS:** 82 frontend tests, ESLint, TypeScript and built Vite bundle
  `index-AtEe107Q.js`. An initial test expected the wrong display label; corrected
  to the actual `Research complete` text before the complete passing test run.
- **PASS — real browser/API/SQLite:** isolated synthetic fixture, built web at
  `http://127.0.0.1:8000`, Codex IAB. Two tabs opened the same rejection dialog.
  First confirmation persisted one review; second confirmation displayed conflict,
  kept its dialog/reason, and did not claim success. Cancel and refresh showed only
  the first review, with both review actions disabled on the rejected candidate.
- **PASS — revoked session:** signing out in one tab followed by refreshing the
  other returned it to sign-in with `Your session ended`; private workspace content
  was unmounted. This proves revoked-session recovery, not time-based TTL expiry.
- Page title/URL, meaningful content, no framework overlay and empty error/warning
  console verified. Screenshots `review-conflict.png` and `session-ended.png` are
  retained in the external clean-install run's `Results/` directory above.
  Both temporary tabs and fixture process were closed. No worker/provider ran.
- Mismatched-response injection remains component-only evidence. Approval-specific
  conflict, time-based expiry and the rest of the browser failure matrix below
  still require their own evidence; this checkpoint does not close the matrix.

## Invalid output, missing and stale sources — 2026-09-27

- Source: `08a1fb3` plus accompanying fixture, decision copy and tests. Fixture
  modes never call models/vendors, always create a new DB, and leave normal API
  configuration unchanged. The invalid graph is also tested through the real
  worker/risk/decision pipeline; it produces REVIEW with no target allocation.
- **PASS — browser:** built UI → AAPL source selection → enqueue → real worker
  with invalid synthetic graph → report → exact linked decision. Processing
  completed, but output stayed `Needs review` and approval remained disabled.
  Reload retained the same decision. Default copy explains that no usable
  investment conclusion was produced; original validation detail is collapsed.
- **PASS — missing source:** selecting BTC in the AAPL-only fixture showed
  unavailable price history, no chart or substituted prices. Returning to AAPL
  restored its saved chart.
- **PASS — stale source:** setting maximum source age to zero in an unsent QA
  form returned the actual API `stale` reason, disabled the source checkbox and
  left queueing disabled. No risk policy or persisted source was changed.
- **PASS:** 83 frontend tests, ESLint, TypeScript/Vite build (`index-hqog1lhq.js`);
  `bash scripts/verify-local.sh`: Ruff, pip check, **1266 tests + 88 subtests**,
  28.77 seconds, 22 warnings. The 20 skipped gates (18 PostgreSQL, optional
  Bedrock and live DeepSeek) remain UNVERIFIED for this run.
- Invalid-output browser console had no error/warning; nonblank decision page,
  no framework overlay, persisted selected identity confirmed. Screenshot:
  external run above, `Results/invalid-output-review.png`.
- Initial fixture TTL of ten seconds was rejected by the existing auth minimum.
  Fixture validation was corrected to 300–43200 seconds, with boundary tests;
  no auth protection was relaxed. Actual five-minute expiry browser observation
  remains in progress, not yet a PASS. Failed-graph retry/exhaustion mode is
  available but its browser check has not yet been run.

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
   on the final code candidate; repeat clean-install smoke if packaging changes
   after the successful installation receipt above;
   final manual security, dependency and tracked-secret review with findings.
4. **UNVERIFIED — delivery documentation:** reconcile README, CHANGELOG, startup,
   ingestion/cadence guidance and ticket statuses with actual runtime behavior.
5. **UNVERIFIED — PR and merge:** fetch/compare current main, create/attach PR,
   review exact diff, resolve findings, merge and verify merged tree plus Actions
   remaining disabled. Never infer completion from this intermediate ledger.

No owner decision is currently blocking these local implementation/QA steps.
Paid-provider tests, public hosting and broker actions remain outside authorization.
