# R01–R14 verification receipt

Candidate branch: `fix/TA-R01-research-quality`.
Backend checkpoint: `e3c269725bf109436091408cfb6b2acd179caa1a`.
Frontend/readability checkpoint: `6621fb8` (backend behavior unchanged).
Runtime: macOS, Python 3.14.7, Node 26.8.1, npm 11.19.0.
No hosted CI, broker, public deployment, provider replacement or policy change.

## Local evidence

| Gate | Status | Evidence |
| --- | --- | --- |
| Full regression including PostgreSQL 16 | PASS | Clean e3c2697: `TA_ALLOW_TEST_DB_RESET=1 bash scripts/verify-postgres-local.sh`; 1350 passed, 88 subtests, 2 optional-provider skips, 22 warnings, 48.26s |
| Ruff, dependency consistency, diff whitespace | PASS | Included in the exact-SHA local script |
| Frontend lockfile install | PASS | `npm ci --ignore-scripts`; 284 packages installed; npm audit reports zero known vulnerabilities, not a security certification |
| TypeScript, Vite build, ESLint | PASS | Local production build; initial JS about 285KB uncompressed, route/report chunks split |
| Frontend regression | PASS | 108 tests, 19 files; saved-language switch causes no request, exact number preserved; no raw HTML execution |
| Full graph/asset fixtures | PASS | 9-stage market-only and 12-stage all-equity-analyst graph; original SentimentReport schema; no live tools/memory/legacy writes; AAPL/SPY/BTC/ETH/NQ/ES profile fixtures |
| Data regression | PASS | Calendar endpoints, session-vs-close labels, warmup, alternating sequences, historic tool references, immutable source/cutoff checks |
| Lifecycle and authority | PASS | Retry-wait cancellation/reload, fenced publication, bounded repair, malformed output REVIEW, deterministic risk/owner approval regression |
| Optional Bedrock / live DeepSeek | UNVERIFIED | Deliberately not installed/called for the existing MiniMax local candidate |
| Other Python versions | UNVERIFIED | One local interpreter is not matrix evidence |
| Non-editable wheel smoke | PASS | Built 0.5.0 wheel at 6621fb8, installed with `--no-deps --target` outside checkout, imported CLI/API/worker/snapshot facts from installed location; archive contains no env/database files |
| Fresh dependency environment | UNVERIFIED | Wheel smoke reused existing venv dependencies; this is not a clean dependency resolution matrix. Initial `--no-build-isolation` lacked setuptools; standard isolated build succeeded without changing runtime dependencies |

Disposable PostgreSQL containers used task-specific labels, loopback ephemeral
ports and tmpfs. The helper verifies ownership before stopping/removing only its
own container. Owner databases and pre-existing containers were not modified.

## Live MiniMax / Yahoo evidence

Existing approved MiniMax endpoint, model M3 and Token Plan credentials were
retained. Credentials and account identifiers are excluded from this receipt.
All runs used saved Yahoo BTC daily history; non-price coverage was not present
and was explicitly disclosed. None evaluated an owner portfolio or placed orders.

- `a12ef815-fd0b-4926-808d-99393a42fe9e`, worker checkpoint 97f4d70 plus safe
  location-only diagnostics: processing succeeded on attempt 2, but report
  acceptance **FAIL**. All nine graph stages completed. PM bilingual numeric
  parity and excessive decimal precision failed both initial output and repair.
  No structured decision or fabricated confidence was published. Provider
  reported 232893 input / 98509 output / 331402 total tokens for attempt 2 only;
  attempt 1 usage was not recorded and must not be treated as zero.
- `ed1842bf-a702-45d3-8da8-ab021a64208a`, attempt 1 at 03ffeae: **FAIL** from
  `SnapshotToolBudgetError`. The eight-query cap incorrectly conflated indicator
  selection with multi-page history queries. ec26375 permits up to 128 read-only
  queries per round, still bounded by 16 rounds and the run limits; a 12-query
  regression test passes. No history was truncated or source gate weakened.
- The same run's attempt 2 at `ec263751172ab446aaa98fcfd24e5e39c8a9c7d6`:
  **FAIL**, `OpenAITimeoutError` at Portfolio Manager after the preceding eight
  stages completed. No final report was published. The snapshot-only 180-second
  per-call timeout was too restrictive for the long final reasoning response;
  fdc3700 restores a bounded 600-second allowance, retaining one SDK retry and
  the graph's boundary-checked run budget. No output truncation or reduced
  debate depth was introduced.
- Attempt 3 at fdc3700, 06:20:45–06:32:44 UTC: all nine stages completed and
  bilingual numeric parity passed after one schema repair. Report acceptance
  **FAIL**: `financial_number_requires_verified_reference`, no structured
  decision published. Artifact `832ae89a-bf8a-5ef7-99c8-7d8e95b960a9` remains
  immutable. Usage: 233251 input / 139898 output / 373149 total, ten calls.
  Manual review found reversed Bollinger percentage denominators and unnatural
  Vietnamese with internal fact IDs. cbfc947 adds explicit reciprocal formulas
  and preserves rejected quantitative references for future audit; e3c2697 adds
  the editorial contract. Neither rewrites or approves the failed report.
- This run's reported usage across attempts is 629515 tokens, with attempt 2
  incomplete because the timed-out call returned no usage. This is a lower
  bound, not total billed quota or dollars.
- The owner explicitly approved one additional BTC execution after these
  fixes. API was restarted at e3c2697 and the new run will use that checkpoint.
  No further automatic paid analysis is authorized if it fails.
  Run `f3d03960-c88a-4b22-a111-0516f37a2c74`, job
  `ff4f2e50-07b3-4d12-bec4-f8f641f66196`, submitted through the actual UI after
  price preparation. The worker is invoked with `--once`, not a retry loop.

## Operational and review boundaries

- Run completion is processing status, not a valid financial conclusion.
  Source quality, research validity and portfolio readiness are separate.
- Numeric-reference validation does not prove all qualitative reasoning or
  translation semantics. Inferences, unusual patterns and causal claims still
  require human financial review. Model confidence is not calibrated probability.
- News/social/fundamentals/macroeconomic data are not fetched by price preparation.
  Select only eligible saved sources; never relabel price-only research comprehensive.
- New daily sources use schema 1.1 with explicit session dates, vendor v4.
  Old artifacts remain unchanged/readable; missing legacy labels remain unknown.
- Upgrade API and worker together for the new `model.usage` event. Stop workers
  cleanly between jobs, rebuild `web/dist`, then restart API. Reload an already
  open browser after a new bundle; do not automatically discard unsaved forms.
- No SQL migration is needed for these additive JSON/event fields. Rollback must
  retain all data; older workers must not claim queued runs using new contracts.
- Local scripts never enable CI or touch an existing database. Use the existing
  live environment only for explicitly authorized provider tests; `--once` is
  not a dry run. Read-only report and locale changes consume no model tokens.
- For usage totals, take the latest cumulative `model.usage` event per attempt.
  In-flight cancellation/transport failures may lack provider usage; cost remains
  unknown when the provider does not report it, including subscription accounting.

## Browser evidence

Local authenticated in-app browser, 1280px desktop and 390x844 mobile. Temporary
mobile emulation was removed after testing. The task used a separate QA tab;
owner tabs and portfolio records were preserved.

- PASS: four routes, source/coverage states, actual graph progress and attempt
  count, legacy cancellation status, invalid-report warning separate from valid
  source, no-portfolio state, collapsible technical sections, language controls.
- PASS: immutable chart range selection and candle inspection; full-history
  range includes 1825 saved points. High/low labels remain readable on mobile.
- PASS: no horizontal page overflow at observed widths; final QA tab console
  returned no errors/warnings after stable reload. An earlier tab with stale
  lazy chunks required reload after replacing the build; the error boundary
  now offers an explicit reload with an unsaved-form warning.
- Screenshots remain local outside Git under the task runtime directory:
  `remediation-mobile-decisions.png` and `remediation-desktop-progress.png`.
  They are UI evidence, not proof that the pending live report is valid.

Final live report acceptance remains UNVERIFIED pending the separately approved
post-fix BTC run. Saved EN/VI switching was verified on the rejected report;
that proves presentation behavior, not research validity or translation quality.
