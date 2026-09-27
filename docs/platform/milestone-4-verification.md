# M4 verification ledger

This ledger consolidates current evidence; historical ticket checkpoints in
`milestone-4-plan.md` and `web/README.md` are not final acceptance declarations.
Local implementation/QA status: **PASS** at code candidate
`967aa24ab148d8dc4b78979a0134ea3b254be1d6`. PR/merge status remains **UNVERIFIED**
until the delivery receipt is recorded. No production deployment or live trading
is in scope. The latest acceptance matrix below supersedes earlier checkpoints.

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
- Earlier frontend checkpoint: 84 tests, lint/typecheck/build PASS. Precise decimal
  display, invalid portfolio/policy responses and view-level recovery are tested;
  injected render failures have component evidence, not browser-injection evidence.

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
  no auth protection was relaxed. Actual five-minute expiry is verified below.
  Failed-graph retry/exhaustion is verified below.

## Session expiry, cancellation and operator docs — 2026-09-27

- Runtime code: clean `8056c54`; subsequent `b5e0f5f` changes documentation only.
  Continued the existing fixture process/tab without restarting its session.
  Login observed at 00:36:42 UTC with 300-second TTL; at 00:41:48 UTC the next
  analysis polling request had returned the UI to sign-in, with private content
  unmounted. Signing in again restored the workspace. **PASS** for real TTL
  expiry on request, not a guarantee of a client-side idle-screen timeout.
- **PASS:** queued a fresh synthetic run with worker absent, cancelled it,
  opened `Configure new attempt`, verified sources/cost authorization unchecked
  and queue disabled, then explicitly configured and queued a separate run.
  Reload showed three history rows: seed, cancelled run and distinct new queued
  run. Cancellation did not rewrite history or silently execute a retry.
- IAB `http://127.0.0.1:8000`, correct page identity, no blank/error overlay,
  empty warning/error console. Screenshots retained in the external run above:
  `Results/session-ttl-expired.png`, `Results/cancel-new-attempt.png`.
  Temporary tab and fixture process stopped normally; synthetic DB retained.
- README/CHANGELOG now describe the implemented local Web UI, not a future UI.
  [Startup guide](local-web-startup.md) documents explicit storage/migration/owner
  bootstrap, separate frontend build and worker opt-in, ingestion/cadence and
  no-order boundaries. Fresh-DB bootstrap example smoke passed outside checkout
  against the clean installed package: one synthetic owner and nine instrument
  identities. No existing owner database was touched.
- **PASS:** `npm audit --omit=dev` and `npm audit`: zero reported vulnerabilities
  for the locked dependency tree at this date. Not a guarantee against unknown
  vulnerabilities. Python advisory scan remains **UNVERIFIED**: `pip_audit` is
  not installed in the developer environment; dependency consistency did pass.

## Worker exhaustion and dependency advisories — 2026-09-27

- Source: `4b6763c` plus accompanying Analysis display/test change. Browser used
  `.venv/bin/python -m scripts.web_fixture --synthetic-local-only --built-web
  --fixture-worker --graph-result failed`; no vendor/model call was possible.
- **PASS:** AAPL source selection/enqueue → real durable worker failure →
  `Waiting to retry`, attempt 1/3 then 2/3 with earliest retry timestamps →
  `Research failed`, attempt 3/3. Reload retained terminal failure, no report
  artifacts, and explicit configuration of a new attempt rather than automatic
  unbounded retry. No successful investment conclusion was displayed.
- Failure copy is now plain language; diagnostic code stays in collapsed
  `Failure details`. **PASS:** 84 frontend tests, lint, TypeScript/build,
  `index-B6nZIz6u.js`; rendered copy verified after reload. Browser console clean,
  page meaningful with no framework overlay. Screenshot in external run above:
  `Results/worker-retry-exhausted.png`. Tab/server/worker stopped normally.
- **PASS:** `pip-audit 2.10.1` run with `--path` against the exact developer
  `.venv/lib/python3.14/site-packages`: 109 dependencies, zero known advisories.
  Editable `tradingagents` intentionally skipped (source review is separate).
  Auditor installed only in the external QA environment, not application deps.
  JSON retained at external run `Logs/developer-dependency-audit.json`.
- Tracked-file key/certificate/database inventory found only example environment
  files and key-related source/tests. High-signal private-key/provider/GitHub token
  pattern scan returned no matching tracked files (values never printed).
  This is limited manual-pattern evidence, not exhaustive secret detection or
  completion of the pending security source review. `gitleaks` was unavailable.

## Readable saved portfolio limits — 2026-09-27

- Source: `9b1aef6` plus accompanying frontend-only patch. Snapshot selectors
  show time/currency/record number instead of truncated internal IDs; values
  submitted remain exact original IDs. Portfolio copy describes historical
  valuations. Known policy limits display financial labels and percentages;
  correlation remains a coefficient. Invalid values are unavailable, not zero.
  Original parameters and policy identity remain in collapsed audit details.
- **PASS:** 85 component/unit tests, ESLint, TypeScript/Vite build. Built assets
  `index-C5vKVsWv.js` and `index-Cr-i7T3Z.css`. No backend/risk-policy changes.
- **PASS:** built UI with isolated `--all-assets --screening` synthetic fixture,
  real local session/API/SQLite. Desktop 1280×720 and narrow 390×844 inspected;
  policy table wraps its labels rather than clipping financial values. Keyboard
  Enter opens disclosure with visible focus, original JSON remains collapsed,
  page width equals 390px, console warnings/errors empty. Title and URL checked.
  Screenshots in external QA run above: `Results/portfolio-policy-finance.png`
  and `Results/portfolio-policy-narrow.png`. Tab and fixture stopped normally.
- Manual follow-up review: display-only allowlisted labels/formatting and CSS;
  no new HTML sinks, endpoint, provider, authentication or mutation behavior.

## Final research language, approval conflict and reconnect — 2026-09-27

- Source: `7134dec` plus accompanying frontend-only patch; final built bundle
  `index-Bf2JLK8C.js`. **PASS:** 87 tests/16 files, lint, TypeScript/Vite build.
  Research groups have financial labels; irrelevant sources no longer repeat
  under every group. Missing research coverage remains explicit. Daily OHLCV has
  a readable label. Owner allocation input includes a 0.20 = 20% explanation;
  the request value, backend freshness/role checks and explicit consent remain
  unchanged. Exact mechanical policy reasons have plain labels; specific warning
  text is preserved. Correlation's backend no-comparison sentinel is explained,
  not represented as evidence of diversification.
- **PASS — real browser approval:** built fixture with synthetic worker,
  all asset groups and screening. AAPL → owner-entered 0.2 target and fixture
  portfolio/policy → queued → worker complete → eight blocking risk checks
  passed → explicit reason/confirmation → Approved. A second tab with stale
  approval state received conflict, kept its reason and showed no false success.
  Close/refresh and full reload confirmed one original approval event, with
  both transition buttons disabled. No model/provider/broker calls were made.
- **PASS — outage/reconnect:** stop fixture API/worker normally, navigate Markets
  in the already-loaded browser; visible local-API error and no fake quotes.
  Restart `create_app(ApiSettings(...))` through loopback Uvicorn against the
  **same task-owned** `.cache/web-fixture-bvwr67m6/fixture.db` and artifacts, with
  built web, synthetic model labels and no worker. Reload saved data restored
  authenticated AAPL 60-bar history and explicit synthetic provenance. No owner
  database, migrations or historical content were changed during restart.
- **PASS — presentation:** readable risk names/values/reasons and collapsed
  identity/evidence details inspected on desktop; 390px decision page has no
  document overflow, tables scroll within labelled regions. Browser console
  warning/error inventory empty after recovery. Screenshots in external QA run:
  `Results/approval-conflict.png`, `Results/final-decisions.png`,
  `Results/final-decisions-narrow.png`, `Results/api-outage.png`,
  `Results/api-recovered.png`, `Results/final-markets.png`,
  `Results/final-analysis.png`. Synthetic data is not market validation.
- Manual source follow-up: only text/display filtering was changed. Unknown
  research IDs retain text, prototype keys are guarded; source selection still
  uses unchanged role/ID checks and payloads. No new HTML sinks, providers,
  network endpoints, risk limits or approval rules.

## Final code candidate acceptance — 2026-09-27

Clean branch `feature/TA-M4-local-web-ui`, code SHA
`967aa24ab148d8dc4b78979a0134ea3b254be1d6`, base
`e45e079b718c29f5fef8de399ed3ce002bcf1f97`. Following receipt edits are docs only.
Release boundary: local research Web UI / private-platform development milestone,
**not** production-private-platform, paper-trading or live-provider readiness.

| Gate | Status | Exact evidence / limit |
| --- | --- | --- |
| Frontend | PASS | `npm test && npm run lint && npm run build`: 87 tests in 16 files; ESLint/TypeScript/Vite; bundle `index-Bf2JLK8C.js`. Node 26.8.1/npm 11.19.0. |
| Python/SQLite regression | PASS | `bash scripts/verify-local.sh`: 1266 tests + 88 subtests, 29.63s; 20 skips, 22 warnings. Ruff/pip check/diff check pass. Python 3.14.7. |
| PostgreSQL regression | PASS | `TA_ALLOW_TEST_DB_RESET=1 TEST_POSTGRES_URL=<disposable> bash scripts/verify-local.sh --postgres`: 1284 tests + 88 subtests, 41.08s; 2 skips, 22 warnings. PostgreSQL 16.14. Migration/schema/rollback, owner isolation, concurrency and ledger receipts included. |
| Browser workflow | PASS | Real local API/database/worker with labelled synthetic graph: login, saved charts/watchlist/screener, source selection, queue/progress/report, risk review, approval/rejection and reload. Group-specific fixtures cover ETF, BTC/ETH and reference-only NQ/ES; not real market-calendar or live-provider evidence. |
| Browser failure/recovery | PASS | Missing/stale data, invalid output remains REVIEW, failed worker bounded retries, cancellation/new attempt, real 300-second session expiry and cross-tab revocation, approval/rejection conflicts, API outage and same-DB recovery, logout. Receipts above preserve individual candidate scope. |
| Finance-first presentation | PASS | Four workspaces, desktop 1280×720 and narrow 390×844; chart/table alternative, keyboard/disclosures, no document overflow. Native controls, readable financial labels, warning/provenance visible, IDs/JSON collapsed. Final form screenshot `Results/final-analysis-narrow.png`. No Image Gen. |
| Authorization/security | PASS | Manual report plus follow-up display-diff review; API tests prove cross-owner/CSRF/Host/Origin denial. Browser happy-path auth and rejected transitions are distinct evidence, not browser exploit coverage. Dependency advisories and limited secret scan are scoped receipts, not exhaustive certification. |
| Malformed rendering | PASS | Component/validator tests, including view recovery; deliberate browser injection remains UNVERIFIED and is not claimed. |
| Clean installation | PASS | Non-editable installation receipt above; packaging unchanged since that receipt. Web assets remain separate from the wheel. |
| Documentation | PASS | README/CHANGELOG, startup/bootstrap, operator-controlled ingestion cadence, local tickets, design and security/evidence docs reconciled. |
| PR/merge | UNVERIFIED | Local checks do not replace merge verification; record PR identity, final head and merged tree separately. |
| Paid/live provider and optional Bedrock | UNVERIFIED | DeepSeek live call withheld; optional `langchain_aws` absent. No paid/model/vendor test authorized. |
| Public deployment, broker, simulator | NOT_IN_SCOPE | No exposure, orders, automated execution or portfolio simulator added. |

Disposable PostgreSQL container `ta-m4-final-967aa24`, label
`codex.task=tradingagents-m4-final-967aa24`, tmpfs database, loopback port 32792;
stopped after testing. Other containers untouched. Temporary browser tabs, API
and synthetic worker stopped; ignored synthetic DB/artifacts and external QA
screenshots retained. No owner data deletion or history backfill.

Current `origin/main` fetched and unchanged at the base above. GitHub Actions
permission still `enabled=false`; no hosted CI required or enabled.

## Pull request and final delivery receipt

[PR #4](https://github.com/phankietit/TradingAgents/pull/4) is the delivery PR.
Its timeline/merge record is authoritative for the final merge SHA and post-merge
tree verification; the table above is the **pre-merge** acceptance receipt.
Do not treat an open PR as delivery complete. Review confirmed the submitted
application tree is identical to tested `967aa24`; later commits change only
documentation. Base remained `e45e079`, the branch was mergeable with no checks
configured, and Actions remained disabled. Manual review is scoped as documented
in the security report, not independent third-party certification.
