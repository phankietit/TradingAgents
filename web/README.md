# Local research Web UI (M4)

## English / Tiếng Việt

Use VI/EN on login or in the workspace header. Only the locale code is stored
in `tradingagents.ui-language.v1`; storage denial falls back to in-memory
selection. An unset preference follows a Vietnamese browser locale, otherwise
English. Switching does not remount forms, submit requests or translate saved
source text. Currency/percentage displays follow the locale; timestamps stay
explicitly UTC and numeric input values retain their existing API conventions.

New analysis defaults to **English + Vietnamese**; English and Vietnamese
alone are also selectable. The language is included in the immutable run,
configuration hash and job payload. Changing it resets paid-call consent.
Old reports are shown verbatim with legacy language attribution, not silently
translated. The bilingual model instruction preserves JSON keys/enums, amounts,
citations, uncertainty and risks; compliance is not independently certified.
See [the full language contract](../docs/platform/bilingual.md).

This checkpoint implements the React shell, session boundary and Markets with
real API instrument discovery, persisted watchlists, saved price chart/table,
backend metrics and source provenance. Analysis now supports snapshot selection,
explicit cost authorization, durable queue submission, SSE progress, cancellation,
new-attempt configuration and artifact downloads/inline inspection. Portfolio renders persisted
snapshots/cash/holdings/policies without recomputing portfolio math. Decisions
renders original/current state, narrative/evidence/risk checks and explicit
approve/reject dialogs. Worker-to-approval integration is verified locally with a
labelled synthetic graph. Finance-first presentation keeps ordinary research,
portfolio and review flows readable while retaining diagnostics in disclosures.
The historical M4 acceptance checkpoint was `967aa24`; see its
[verification ledger](../docs/platform/milestone-4-verification.md) for exact
commands, browser receipts and PR/merge status. Historical checkpoints below
retain their original counts and limitations. Live-provider validation and
production deployment are not implied. Start with the
[local startup guide](../docs/platform/local-web-startup.md).

The R01–R14 candidate adds snapshot-bound research tools, strict bilingual report
validation, saved-history charts, safe Markdown, real graph-stage progress and
the charcoal/sage workspace redesign. Current status and live limitations are
tracked in [research remediation](../docs/platform/research-remediation.md);
historical M4 receipts do not certify this candidate.

On screens up to 600px, the workspace uses a compact brand/account/navigation
header and tighter report-context spacing. Owner identity, sign-out, language
switching, run selection, coverage warnings, source details and human-review
controls remain available. The decorative page tagline is omitted and report
tabs share one horizontally scrollable row with 44px touch targets; no safety
notice is hidden. This is
presentation only: no role, source,
authorization, report or approval contract changes. Rendered desktop/mobile
acceptance must be recorded against the exact candidate SHA; build/unit tests
alone do not prove layout quality.

The workflow keeps saved-report availability separate from job completion:
only a `succeeded` status can show the finished-processing message. A retained
report during queued, running, retry, cancellation, review or failure states
instead asks the owner to verify processing status and report validation.
Neither message grants financial validity or human approval.
If a processing-status refresh fails or returns another run's identity, its
previous observation is withdrawn from the workflow and history row. The
separately fetched run status remains available; the warning does not invent
job completion, a retry, or a new paid request.
Read-only polling coalesces ticks while a fetch is still pending, then performs
one follow-up refresh. A slow request is not cancelled every five seconds.
Changing the resource or leaving the screen still aborts it and ignores late
responses. Decision/approval refreshes retain their default clear-and-cancel
behavior; this does not cache approvals or authorize any retry of analysis.
Artifact previews bind their read state to the complete run/manifest identity.
Equal metadata copies from polling do not restart a pending immutable read.
Changed hash, size, kind, media type, creation time, artifact or run withdraws
previous contents immediately; late responses cannot restore the old preview.
Failed reads show no report contents. This is display isolation, not a new
integrity attestation, financial validity or approval authority; server-side
artifact and decision checks remain required.
When a report is retained during active processing, only the observed processing
phase is marked current. Report availability does not simultaneously mark owner
review as the current phase; a queued job cannot invent a current phase.

The analysis setup now has an independent **Add recent headlines** action
beside price preparation. It saves owner-scoped Yahoo news only when the
current-vintage feed passes identity, content and cutoff checks. The action is
optional, does not start AI, clears prior paid-call consent, and never presents
the recent feed as exhaustive or historically replayable. Social,
fundamentals and macro acquisition remain unimplemented; see
[data preparation](../docs/platform/data-preparation.md).

## Development

Verified with Node 26.8.1 and npm 11.19.0. Dependencies are locked; TypeScript
6.0.3 is used because the selected lint integration does not support TypeScript 7.

```sh
cd web
npm ci
npm run dev
```

Open `http://127.0.0.1:5173`. The server binds loopback with a strict port and
proxies `/api` to `http://127.0.0.1:8000`, preserving Origin. Set the API's
`TRADINGAGENTS_ALLOWED_ORIGIN=http://127.0.0.1:5173` and explicitly set
`TRADINGAGENTS_SECURE_COOKIES=false` only for this local HTTP workflow. Follow
the existing API runbook for migrations, owner bootstrap and API startup; do
not put backend/provider credentials in Vite environment variables.

```sh
npm run typecheck
npm run lint
npm test
npm run build
```

These commands run locally; no hosted CI. Do not publicly expose the development
server or use it as a production deployment.

## Run the built local web

After `npm run build`, use the existing `tradingagents-api` process with:

```sh
export TRADINGAGENTS_WEB_ROOT="/absolute/path/to/TradingAgents/web/dist"
export TRADINGAGENTS_ALLOWED_ORIGIN="http://127.0.0.1:8000"
export TRADINGAGENTS_API_PORT=8000
export TRADINGAGENTS_SECURE_COOKIES=false
tradingagents-api
```

Set the existing `TRADINGAGENTS_DATABASE_URL` and `TRADINGAGENTS_ARTIFACT_ROOT`
in that process environment first, using your approved local database/store.
The package initializer may load `.env` and `.env.enterprise` from the current
directory/parents without overriding exported variables; keep those files local
and ignored, and launch from the intended checkout. API startup does not migrate,
bootstrap an owner, seed data or start a worker. Follow [API setup](../docs/platform/api.md),
[owner bootstrap](../docs/platform/owner-authentication.md) and
[worker operation](../docs/platform/durable-jobs.md). Run `tradingagents-worker`
separately with the same database/store only after authorizing its model use.
Missing data/worker/credentials is not repaired with synthetic production data.

Open `http://127.0.0.1:8000`; no Vite process is needed. UI, API and SSE share
one origin. Do not use localhost aliases or another port: the configured Host
and Origin must match exactly. `secure_cookies=false` is for this loopback HTTP
mode only. Omit WEB_ROOT to retain API-only operation. The build is a separate
operator-generated artifact, not bundled into the Python wheel.

For **isolated synthetic QA only**, from repo root after building:

```sh
.venv/bin/python -m scripts.web_fixture --synthetic-local-only --fixture-worker --built-web
```

This creates a new ignored database/store and uses labelled synthetic graph
output; it does not load owner records or call models/vendors. Never point the
fixture script at an owner database. Stop with Ctrl-C; fixture data is retained
for inspection. This is not a populated investment product or live-data demo.
The synthetic app explicitly refuses both price and news vendor acquisition;
the news button can be used to verify its unavailable state without a Yahoo
request.
Add `--all-assets` only for cross-asset QA: it seeds labelled synthetic daily
series for SPY/QQQ, BTC/ETH and NQ/ES, in addition to AAPL. Values are scaled
fixtures, not real market returns, calendar-session coverage or futures roll
history. Original missing-data checks can still use the default AAPL-only mode.

Failure QA remains opt-in and synthetic: add `--graph-result invalid` together
with `--fixture-worker` to publish an unusable output through the real REVIEW
path, or `--graph-result failed` to exercise durable retry/exhaustion. Neither
graph has a live-provider fallback. `--session-seconds 300` uses the existing
minimum five-minute session lifetime to test actual expiry; it does not change
normal API settings or bypass authentication rules. Each invocation creates a
new isolated database. Reusing a browser cookie from a stopped fixture does not
authenticate it against the new fixture; sign in again.

Built-mode QA: 1280×720 IAB login → saved AAPL → CSRF watchlist save → reload
and session restoration → logout PASS, no console/CSP errors or framework
overlay. Static/API gate: 43 tests PASS, including no API-to-HTML fallback,
path traversal/symlink/dotfile/source-map refusal, Host/Origin rejection,
same-origin session/CSRF and local bind/port checks. Narrow built-mode and full
cross-asset acceptance remain pending; earlier narrow checks used Vite.

## Security and verification boundary

- Private data is mounted only after `/auth/me` or login validates the owner.
- Mutations bootstrap the existing session-bound CSRF token; no credentials,
  reports or financial records are stored in browser local/session storage.
- A 401 unmounts private components; failed logout remains visible and retryable.
- Request errors use local safe messages, not unrestricted backend payloads.
- Component tests use explicitly synthetic responses. They are not live-provider
  or browser-to-backend integration evidence.
- IAB verification at 1280×720 and 390×844: real API login → AAPL saved snapshot
  → add watchlist → reload/session restoration → watchlist filter → price table
  → index reference with missing series → logout/private data unmount. No
  framework overlay or app warning/error captured. Narrow viewport has no
  document-level horizontal overflow; OHLCV table scrolls within its region.
- Reproduce isolated synthetic QA from the repository root with
  `.venv/bin/python -m scripts.web_fixture --synthetic-local-only`, then start
  Vite. Fixture credentials are documented in that script, not owner credentials.
  Each run creates a new ignored `.cache/web-fixture-*` database and artifacts.
  By default no worker starts. Add `--fixture-worker` to run the real durable job,
  evidence and risk pipeline with explicitly labelled synthetic graph output.
  Neither mode calls a vendor/model; the fixture graph has no live-tool fallback.
  Provider/model metadata is synthetic, not OpenAI. The synthetic vendor label
  is visible beside the chart. This is integration evidence, not live data.
- Analysis IAB check: Markets Analyze → choose market snapshot → explicit queue
  authorization → real queued run → cancel → SSE `run.cancelled`. No worker or
  model ran. Browser logs had no app errors. Generated report/risk/decision paths
  were UNVERIFIED at that checkpoint. Unit tests cover disabled stale inputs, required consent and
  stable idempotency keys after failed unchanged submissions.
- Portfolio/Decisions IAB: backend replay of synthetic deposit and historical
  holding gives NAV 10180.20 USD, cash 8200 USD, 10 AAPL units at 198.02 USD.
  Seeded REVIEW candidate cannot be approved; explicit reason/reject persists an
  audit event after reload. This is seeded local QA, not generated model output.
  Multi-asset browser risk integration remains UNVERIFIED.
- Analysis risk input check: choose a persisted portfolio and existing effective
  policy, enter an owner target, select market evidence, authorize and enqueue.
  API accepted the pinned timestamp/risk payload. Price sources are disabled for
  unrelated analysts. No worker/model ran in this browser check; policy fixture
  is explicitly synthetic and does not change owner limits.
- Worker fixture check (2026-09-27 local, 1280×720, IAB): login → AAPL market
  snapshot → synthetic portfolio/policy → owner target 0.2 → queue → worker
  succeeded → two integrity-checked artifact manifests → eight risk checks PASS
  → confirm approval with reason → reload → approved audit persists. Source run
  `26dc48fa-…`, decision `156eadfd-fa5a-5cfd-ad7f-fd4e33aaad54`. Original research
  state remains ready_for_approval while current state is approved; actions are
  disabled afterward. No order or paid model call occurs. Browser console clean,
  meaningful page/title and no framework overlay; screenshot inspected.
  A discovered stale history-row status was fixed with stable status propagation
  from the fetched run detail; a second queued run reached succeeded in both
  list and detail without manual refresh. Regression test checks no SSE reconnect.
  Local gates: 24 frontend tests, 6 snapshot-worker tests, lint/typecheck/build PASS.
- Report inspection checkpoint: a user-triggered preview reads the existing
  owner-authorized, integrity-checked artifact endpoint. Only analysis-report and
  decision-evidence JSON up to 1 MB is previewed; both manifest and streamed-byte
  bounds apply. Run identity, report shape and claim/source links are checked
  before rendering. Malformed, mismatched or integrity-failed data yields an
  explicit unavailable state, not a narrative fallback. HTML remains plain text;
  there is no HTML/Markdown injection, iframe, external asset fetch or browser
  persistence. Other formats/sizes retain explicit download only.
  Reports link to the exact decision, including older candidates outside the
  latest history page; missing/forbidden IDs do not silently select another row.
  Selection survives reload. Immutable research and current lifecycle are labelled
  separately; a successful run without risk inputs still cannot be approved.
  Built-mode IAB at 1280×720 and 390×844: synthetic worker publication → inspect
  narrative/structured output → claim/source/time/hash drilldown → correct linked
  REVIEW decision → reload PASS; Enter opens preview/disclosure, visible focus,
  no document overflow, console/CSP errors or framework overlay. 34 frontend
  tests plus lint/typecheck/build PASS. This remains offline fixture evidence.
- Market query checkpoint: an explicit daily saved-data cutoff/start/end and
  benchmark selector sends the window to the existing backend. Asset/benchmark
  return, correlation and tracking error are never recomputed in React.
  Benchmark provenance is required before comparison metrics are shown. Malformed
  price payloads are withheld rather than crashing the workspace; invalid local
  timestamps stop submission. Missing benchmark coverage does not fall back to
  an unrelated source. Editing query fields does not fetch until Apply is clicked.
  Built IAB 1280×720: AAPL–SPY window gives 25 aligned observations with source
  hash; unavailable ^GSPC comparison has no fabricated chart/metrics. SPY/QQQ,
  BTC/ETH and ES/NQ show their instrument calendars and reference/crypto labels.
  Synthetic worker runs produce profiles etf, large-cap-crypto and
  futures-reference; NQ portfolio input is disabled and report remains reference
  only. At 390×844 the crypto query form stacks, Enter/focus works, and document
  width stays 390px. No console warnings/errors. These are normalized synthetic
  chart/profile checks, not live-provider, roll-series or calendar-vintage proof.
- Saved stock screener checkpoint: Markets → View screened candidates reads
  owner-scoped immutable rankings, exclusions, policy, input/universe hashes and
  source IDs. Configure research opens the selected instrument without queuing a
  run. Missing history, valid empty universes and invalid artifacts are distinct.
  Generate synthetic screening QA with `--screening` added to the fixture command;
  its policy is labelled `SYNTHETIC-QA-NOT-OWNER-POLICY`, and its inputs are separate
  synthetic facts, not measurements inferred from the daily chart.
  Built-mode IAB at 1280×720 and 390×844 verified AAPL candidate, SPY exclusion,
  policy disclosure, keyboard switching and AAPL analysis handoff. Screening
  inputs are disabled as analyst evidence. No document overflow, framework
  overlay or console warnings/errors. Scoped backend: 7 PASS, 1 PostgreSQL skip;
  frontend: 45 PASS plus lint/typecheck/build. Live data remains UNVERIFIED.
  Full local Python regression on Python 3.14.7: 1248 tests and 88 subtests PASS,
  20 skipped (PostgreSQL, optional Bedrock dependency, live DeepSeek); Ruff and
  dependency consistency PASS. These skipped gates are not release approval.
- Finance-first screening pass: compact USD values, explicit annualized volatility
  and 20-day liquidity labels, optional financial definitions, collapsed exact
  amounts/rank details/source IDs and raw exclusion codes. Synthetic warning and
  as-of caveat remain visible; no backend policy or ranking changes. 45 frontend
  tests, lint/typecheck/build PASS. Built IAB 1280×720/390×844 verified default
  presentation, keyboard-opened audit details, exclusion switching, clean console
  and no document overflow. Other workspaces still require the finance-first pass.
- Research setup disclosure: the analysis form explains possible charges and
  unverified background-service/provider availability before authorization.
  Configured model names and retry limit are collapsed details; no credentials or
  paid connectivity probe is involved. Authenticated API contract tests: 30 PASS;
  frontend: 48 PASS, lint/typecheck/build PASS. Built-mode IAB verified keyboard
  disclosure, truthful synthetic model settings, clean console and narrow layout.
  This does not prove a production worker or provider is available.
- Research-time form: native date/time selection explicitly labelled UTC replaces
  routine ISO entry. Exact timestamps and the unchanged source-age setting live
  in Advanced data settings. Portfolio-bound timestamps retain their exact
  original value and remain locked; tests assert request payloads, UTC conversion,
  unchanged 604800-second default and empty-date denial. 49 frontend tests plus
  lint/typecheck/build PASS. Built IAB desktop/390px: native keyboard date change
  matches the exact UTC display, earlier date makes future sources ineligible,
  advanced disclosure works, no document overflow or console errors. The browser
  driver's fill alone did not dispatch a React state update for the native date
  field; validation used the visible native keyboard interaction instead.
- Durable processing detail: Analysis reloads owner-scoped job state by run ID,
  with readable status, attempt count, explicit retry/cancellation semantics and
  collapsed processing IDs/timestamps. Missing jobs never imply active work.
  54 frontend tests, lint/typecheck/build and 9 scoped Python tests PASS; one
  PostgreSQL test skipped (UNVERIFIED). IAB desktop/390px: new AAPL fixture analysis
  → queued → real local worker publication → complete, attempt 1/3 → browser
  reload preserves result; keyboard details, console and overflow checks PASS.
  No live model or vendor calls. Retry-wait and invalid-data states have component
  coverage; this browser flow verifies successful processing, not a provider retry.
- Portfolio source drilldown: View valuation sources loads the saved receipt on
  demand. Prices/currency/vendor/source times remain readable, with IDs/hashes
  collapsed. Legacy missing receipts are explained without a fabricated live
  fallback. New valuation receipts do not change portfolio math or rewrite history.
  24 scoped backend tests and 58 frontend tests PASS; lint/typecheck/build PASS.
  Full local Python regression: 1256 tests + 88 subtests PASS, 20 skips (same
  PostgreSQL/optional Bedrock/live DeepSeek limitations). IAB desktop/390px:
  source price 198.02 USD matches the synthetic AAPL holding, vendor/time visible,
  keyboard disclosure and console checks PASS. No live market validation.
- Display safety: portfolio/policy response shapes are validated before rendering
  and before use in risk configuration; invalid responses are distinct from empty
  holdings. Decimal strings (including scientific notation for small crypto
  quantities) are expanded without binary floating-point portfolio calculations.
  Render failures keep navigation/logout outside the failed view; explicit retry
  remounts only the view, and caught-error console reporting is generic/redacted.
  74 frontend tests plus lint/typecheck/build PASS. Component tests cover invalid
  arrays/amounts/weights, duplicate holdings, exact precision and explicit boundary
  recovery. IAB desktop verified valid fixture NAV/holdings and reload without
  console errors. Browser fault injection and final all-workspace QA remain open;
  component failure tests are not presented as live browser fault evidence.
- Decision readability pass: symbol/rating, current human-review state, thesis,
  key risks and invalidation conditions precede technical context. Model confidence
  stays in audit details and is explicitly not a profit probability. All six data
  quality states retain distinct labels. Known allocation/exposure/turnover/cash
  checks display percentages; correlation and other checks keep their own values.
  Confirmation identifies symbol/rating/date and keeps exact identity available.
  Analysis event timeline and file metadata are collapsed; event names use readable
  labels. No authorization, risk threshold or state-transition logic changed.
  77 frontend tests plus lint/typecheck/build PASS. IAB desktop/390px verified
  REVIEW approval denied, keyboard-opened rejection, required reason, persisted
  rejection after reload, original/current distinction and clean console. The
  final all-workspace visual/failure matrix remains open.
