# Milestone 4 — local quant research web

Base: `e45e079b718c29f5fef8de399ed3ce002bcf1f97` (M3 PR #3 merged).
Branch: `feature/TA-M4-local-web-ui`; reuse the clean managed M3 checkout.
Owner: this Codex task only. Root checkout and other worktrees remain untouched.

## Current ticket disposition — 2026-09-27

Code candidate: `967aa24ab148d8dc4b78979a0134ea3b254be1d6`.
The detailed paragraphs below retain the chronological implementation history;
this table and `milestone-4-verification.md` supersede their old checkpoint status.

| Local ticket | Acceptance status | Delivered scope |
| --- | --- | --- |
| M4-FOUNDATION | PASS | Native quant design, finance-first contract, loopback architecture and local gate commands. |
| M4-API | PASS | Owner-scoped discovery, persisted watchlist, sources/screener/report/valuation receipts; SQLite/PostgreSQL tests. |
| M4-SHELL | PASS | Built same-origin UI, session/CSRF/login/logout/expiry, responsive accessible navigation and recovery. |
| M4-MARKETS | PASS | Saved chart/table/benchmark, groups/watchlists/screener, provenance, missing/stale states and analysis handoff. |
| M4-ANALYSIS | PASS | Native research time, suitable source selection, explicit spend consent, durable queue/progress/cancel/bounded retry and reports; synthetic worker E2E. |
| M4-PORTFOLIO | PASS | Exact stored values, readable policy limits, immutable source drill-down, no frontend risk math or historical backfill. |
| M4-DECISIONS | PASS | Thesis/risks/invalidation/evidence, deterministic checks, explicit human approve/reject, conflict handling and persistent audit. |
| M4-ACCEPTANCE | PASS for local gates | Final delivery is conditional on [PR #4](https://github.com/phankietit/TradingAgents/pull/4) being merged; consult its timeline for exact merge/tree/Actions verification. |

Live data/model calls remain UNVERIFIED; real multi-currency provider operation,
public hosting, simulator and broker execution are not delivered by fixture QA.
Review approval never sends an order. No hosted CI or Image Gen was used.

GitHub Issues is disabled (verified through repository API). No M4 ticket file
was found in the current tracked tree. IDs below are **local ticket keys**, not
claims of existing GitHub issues or old PLAN assignments. The branch uses the
milestone identifier because no numeric GitHub issue is available.

## Product and delivery boundary

Build a local web application on the existing FastAPI/worker/database stack.
First complete AAPL end-to-end, then apply existing asset profiles to equities,
ETFs, BTC/ETH and NQ/ES context. Approval records a human decision, not an order.
No simulator, broker, production deployment, paid service setup or hosted CI.
Manual security review is the owner-approved acceptance format; failed historical
plugin finalization is neither rewritten nor represented as completed evidence.

At the milestone base no frontend framework existed. Implemented stack: React + TypeScript +
Vite in `web/`, same-origin `/api` requests through a loopback-only development
proxy. Backend remains authoritative. Pin actual installed package versions in
a lockfile; inspect current official documentation before implementation.
Avoid SSR, hosted auth, analytics and other unnecessary service dependencies.
Keep authentication state in HTTP-only cookies, never browser bearer storage.
Select a safe local serving path for the built app as part of the foundation;
the Vite dev server alone is not a deployment strategy.

## UX contract

Primary navigation: Markets, Analysis, Portfolio, Decisions. Account/logout is
secondary chrome. No marketing hero, fake performance cards or decorative ticker
tape. Dark neutral surfaces, a restrained cool accent, semantic warning/error
colors, tabular numbers and compact but readable controls. Tables use row
selection/detail, not a card for every metric. All text/controls are native UI.

Markets: asset-group filters → searchable instruments/watchlist → selected
instrument chart and OHLCV table → source, timestamp, quality and analysis action.
Analysis: create-run flow → run history → job/progress/cancellation → report and
evidence inspector. Portfolio: owner snapshots → holdings/cash/allocation →
deterministic valuation provenance. Decisions: candidate list → current lifecycle
and policy checks → explicit approval/rejection confirmation → immutable audit.

Every surface specifies loading, empty, error, expired-session and partial-data
behavior. Financial values have currency/units, dates have timezone, reference
futures are visibly non-investable. Stale/unavailable sources never look live.
Keyboard navigation, visible focus, reduced motion and readable narrow viewport
are required. Long tables may scroll within labelled regions, not overflow the
whole page. Charts must have a tabular accessible alternative.

The owner explicitly opted out of Image Gen: design directly in native code.
The [web design specification](web-design-spec.md) defines the initial visual
system; browser screenshots, not generated images, will establish its reference.
No image/model call is authorized for concepting.

## Observed API and gaps

Existing: login/logout/me, instrument list/resolve/detail, owner-bound time series,
run create/list/detail/events/cancel, job detail, decisions/list/state/transitions,
and owner-checked artifact download. Run creation already accepts explicit
snapshot and portfolio/policy inputs; these must not be guessed in the browser.

Missing web discovery surfaces: owner portfolio snapshot list/detail, policy
list/detail, eligible snapshot selection, run artifact manifests and persisted
watchlist. There is no general data-ingestion or owner-onboarding web flow.
Keep owner bootstrap and data import operator-controlled, documented and explicit;
do not expose arbitrary URL fetch, filesystem upload or credentials in M4.
Do not assume that existing source adapters imply populated snapshots.

Browser integration issue discovered: the existing readable CSRF cookie has
Path=/api/v1, so a document served at / cannot read it for the mutation header.
Resolved by authenticated `GET /api/v1/auth/csrf`: the root-mounted client fetches
the existing session-bound token into memory. Cookies remain API-scoped; session
stays HTTP-only, with same-origin and mutation CSRF checks intact. No token
rotation, localStorage credential storage, or cross-origin read access is added.
Local API tests cover unauthenticated/expired sessions, missing/forged/other-session
CSRF cookies, no-store, cookie paths, no CORS headers and bootstrap-to-logout.
Browser integration remains UNVERIFIED until M4-SHELL acceptance.

## Local tickets and acceptance

### M4-FOUNDATION — inventory, UX and web architecture

Status: in-progress. Depends on merged M3.

- Record real API gaps, navigation, design tokens/components and state inventory.
- Establish visual specification before UI implementation, respecting owner choice.
- Choose local origin/serving strategy without weakening cookie/CSRF security.
- Define commands and test stack; no paid provider or Actions calls.
- Evidence: this plan plus design/architecture documentation; implementation remains pending.

### M4-API — owner-scoped workspace discovery

Status: in-progress (backend implemented; integrated browser acceptance pending). Depends on M4-FOUNDATION.

Discovery checkpoint: bounded owner portfolio/policy list/detail, run artifact
metadata without storage paths, and owner-readable snapshot discovery with shared
temporal/freshness metadata checks. Content integrity is explicitly still checked
at run creation. API/persistence/snapshot-analysis tests: 38 PASS, PostgreSQL gate
skipped (UNVERIFIED; no schema migration in this checkpoint). Browser consumers
remain pending. Persisted watchlist now uses migration `0010_owner_watchlist`
and owner-scoped idempotent PUT/DELETE. Watchlist/API/persistence SQLite gate:
32 PASS, one optional PostgreSQL skip. Separate disposable PostgreSQL gate:
6 PASS including schema parity, upgrade/rollback, concurrent watchlist PUT,
owner isolation and existing M3 ledger/approval checks. No owner data reset.

- Add only necessary typed list/detail endpoints for portfolio snapshots, policy,
  snapshot metadata/eligibility and run artifact manifests, with pagination/bounds.
- Owner identity comes exclusively from session; wrong-owner/missing ID fails closed.
- Do not expose arbitrary artifact bytes inline as HTML or provider configuration secrets.
- Reuse persistence and deterministic services; no UI-authored policy exceptions.
- Persist watchlist with owner scope and validated instrument IDs; test migration
  upgrade/schema parity/rollback if a table is added.
- Tests: auth, cross-owner, invalid filters, missing sources, temporal eligibility,
  reference-only classification and existing API regressions.

### M4-SHELL — local web shell and owner session

Status: in-progress. Depends on M4-FOUNDATION; may precede API discovery completion.

Built-server checkpoint: opt-in WEB_ROOT serves the built shell and allowlisted
assets through the loopback API process, no catch-all or source/private-file
mount. Exact Host/origin/port, CSP and existing auth/CSRF remain enforced.
43 static/API tests PASS; IAB built mode at 1280×720 verifies login, saved chart,
watchlist mutation, reload persistence and logout without console/CSP errors.
This supersedes the older static-serving UNVERIFIED checkpoint below, not the
remaining full browser/security/asset acceptance.

Full local regression on `6598a03` plus the built-server patch (Python 3.14.7):
ruff and installed dependency consistency PASS; 1,244 tests and 88 subtests PASS,
20 skips (PostgreSQL, optional Bedrock dependency, live DeepSeek) UNVERIFIED.
Command: `bash scripts/verify-local.sh`. This dirty-patch result is not clean
final-candidate or PostgreSQL acceptance; rerun at the final candidate.

Checkpoint: `web/` contains pinned React/Vite/TypeScript tooling, native dark
tokens, shell navigation and session/login/logout/API client. Local build/lint
and 10 synthetic unit/component tests PASS. IAB login/unavailable-API retry smoke
is verified at 1280×720. Authenticated browser flow, narrow viewport, static
serving and data workspaces remain UNVERIFIED/pending; not a completed web product.

- Reusable shell/components, route navigation, login/logout/session expiry.
- Same-origin credentials and authenticated CSRF bootstrap/header; no wildcard CORS bypass.
- Schema-aware errors without reflected secrets; untrusted report text never raw HTML.
- Local dev/build/start instructions and loopback-only defaults.
- Tests: session restore/logout/401, keyboard/focus, desktop/narrow shell and build.

### M4-MARKETS — provenance-first market workspace

Status: in-progress. Depends on M4-API and M4-SHELL.

Implemented: group/search/watchlist filters, owner watchlist mutation, saved
timeseries chart and paginated OHLCV table, backend return/volatility/drawdown,
source/vendor/as-of/hash and quality notices. NQ/ES remain reference only;
missing series has no synthetic production fallback. IAB real API/SQLite/artifact
integration verified with an explicitly labelled synthetic fixture, desktop
1280×720 and narrow 390×844 (no document overflow), login/save/reload/table/
reference-missing/logout. 13 frontend tests, build and lint PASS. Further work:
screening integration and broader
failure/accessibility acceptance. This is not live-provider evidence.

Updated checkpoint: analysis handoff and explicit saved-data cutoff/start/end
and benchmark controls implemented. API exposes benchmark provenance; frontend
withholds missing provenance or malformed prices. IAB built desktop: AAPL–SPY
25-point comparison/source hash, missing benchmark without fallback, six ETF/
crypto/futures-reference charts and NQ/BTC/SPY synthetic worker profiles PASS.
Reference risk-input control remains disabled. Narrow 390px crypto controls,
keyboard focus and no overflow PASS; console clean. Normalized synthetic series
do not prove real vendor, market calendar-session, or futures roll coverage.
API/time-series gate: 35 PASS, one PostgreSQL skip UNVERIFIED.
Frontend gate: 39 tests, lint/typecheck/build PASS. No paid provider calls.

Native-design comparison: rail/layout, exact neutral-dark palette, tabular metrics,
labelled source state, responsive stacked controls and table overflow inspected.
Source vendor label moved out of collapsed provenance into chart context so test
data cannot look like real quotes. No generated concept exists by owner choice.

- AAPL instrument selection, persisted watchlist, daily chart plus OHLCV table;
  current metrics come from backend, not duplicate financial calculations.
- Source/as-of/quality/currency/timezone and clear empty/stale/error states.
- Reuse group-specific calendars/profiles for ETF, BTC/ETH and NQ/ES; reference
  labels and no execution affordance on NQ/ES.
- Tests: selection/filtering/reload, missing bars, missing source, backend errors,
  snapshot cutoff and accessible chart alternative.

### M4-ANALYSIS — real durable analysis workflow

Status: in-progress. Depends on M4-MARKETS.

Checkpoint: backend analyst-profile endpoint, Markets handoff, snapshot selection,
explicit cost consent, idempotent enqueue, run history/SSE, cancel/new attempt and
artifact downloads. 16 frontend tests and 24 API tests PASS; build/lint PASS.
IAB real API/database fixture: enqueue → queued → cancel → terminal SSE verified.
No worker/model call made. Dataset-to-role suitability is now enforced by the
shared backend mapping and reflected in source choices. Risk input configuration
selects owner portfolio/policy, pins its timestamp and accepts only explicit owner
target weight; correlation inputs use owner snapshot discovery. Browser fixture
queue with these inputs PASS; 23 frontend and 43 scoped backend tests PASS.
Remaining: provider-readiness display, full negative/browser acceptance and
broader asset coverage. Inline report/evidence inspection is implemented using
the existing protected artifact endpoint, explicit on-demand load, 1 MB streaming
bound, context/shape/link validation and text-only rendering. Deep links target
the exact decision without silently selecting another history row. Built-mode
IAB desktop/narrow inspection, provenance, keyboard Enter/focus, linked REVIEW
decision and reload PASS; 34 frontend tests/build/lint PASS. Worker/result
integration checkpoint: explicit `--fixture-worker` runs durable jobs with a
labelled offline synthetic graph in a newly isolated QA database. Real API,
worker, immutable evidence, deterministic risk and approval services remain
unchanged. Browser AAPL target 0.2 → succeeded → eight risk checks PASS → owner
confirmation → approved → reload/audit PASS. No live provider or model call.
History status now follows fetched detail without reopening SSE; regression and
second browser run PASS. 24 frontend tests, six snapshot-worker tests, build/lint
PASS. This is synthetic integration evidence, not live analysis acceptance.

- Form selects permitted analysts and eligible immutable inputs; exact as-of and
  cost/provider readiness are visible before any invocation.
- Explicit enqueue action, idempotency key, resumable progress, run history,
  cancellation and retry semantics matching the existing queue contract.
- Report/evidence drill-down; REVIEW is first-class, never silently converted to buy/sell.
- Backend/worker/database integration with labelled offline fixtures for automated
  tests. Real provider evidence remains separate and requires authorized credentials.
- Tests: enqueue/reload/progress/cancel/retry, invalid narrative, invalid citation,
  failed provider, no worker, missing policy/snapshot and duplicate submission.

### M4-PORTFOLIO — owner valuation and policy view

Status: in-progress. Depends on M4-API and M4-SHELL.

Persisted snapshot selector, exact decimal balances, holdings/weights and read-only
policy versions implemented. IAB real API/ledger replay fixture values verified;
no frontend portfolio recomputation. Source-linked valuation drill-down and full
multi-asset/currency acceptance remain pending.

- Display immutable portfolio snapshot, holdings/cash/NAV/allocation and source clock.
- Explain deterministic policy observations, missing correlation/coverage and limits.
- No implicit policy creation, history rewriting or risk-limit change.
- Tests: owner isolation, no portfolio, unavailable price/valuation, precision and
  unit formatting, currency labels and repeated load consistency.

### M4-DECISIONS — human review and audit

Status: in-progress. Depends on M4-ANALYSIS and M4-PORTFOLIO.

Original/current state, narrative/evidence/checks, reasoned modal confirmation,
expected-status/idempotent event identity and audit timeline implemented. IAB
REVIEW approval-disabled → explicit rejection → reload persisted audit PASS.
22 frontend tests/build/lint PASS, including escaped narrative and backend
transition rejection. Successful approval and full worker/risk integration still
UNVERIFIED, not implied by rejection QA.

- Display original research separately from current state/event history.
- Approval/rejection requires explicit confirmation and reason, uses expected
  status/version and idempotent event identity; reload retrieves persisted state.
- Rejected backend policy/run/CSRF/conflict must remain rejected visibly; disabling
  a frontend button is never considered authorization enforcement.
- Tests: valid approval, REVIEW/failed-risk/cancelled-run denial, terminal conflict,
  repeated submission, expired session and event history after reload.

### M4-ACCEPTANCE — browser, security and delivery

Status: planned. Depends on all tickets above.

- Mandatory finance-first UX pass per `web-design-spec.md`: clean modern output
  for nontechnical investors; professional financial detail via progressive
  disclosure. Remove default-view technical clutter without hiding source quality,
  risk, synthetic labels or approval boundaries. Existing checkpoint screenshots
  are not final visual acceptance. Verify routine use needs no IDs/JSON/ISO input.

- Browser E2E over real local API/worker/database, fixture labels explicit;
  desktop and narrow screenshots, console/network/keyboard/state checks.
- Local lint/typecheck/build/component/E2E, full Python regression and disposable
  PostgreSQL gates; install smoke when packaging changes.
- Manual security review: XSS/report rendering, same-origin/CSRF/session handling,
  owner scope, secret exposure, local binding and new mutations.
- README/changelog/runbook/ticket evidence with exact SHA and explicit limitations.
- Commit per ticket, PR review, resolve findings, merge and verify tree/Actions off.
- Clean up only task-owned servers/containers; preserve user state and worktrees.

## Completion audit

The consolidated current evidence and remaining gates are tracked in
`milestone-4-verification.md`. Earlier ticket paragraphs are chronological
checkpoints, not claims about the final candidate. Final-candidate frontend,
Python and PostgreSQL full regression now pass; the PR/merge gate remains open.

Saved-screener checkpoint: owner-scoped read-only list/detail API and Markets
panel implemented. Saved ranking, exclusions, immutable policy/hashes/source IDs
and explicit analysis handoff are verified with isolated synthetic fixtures.
7 scoped backend tests and 45 frontend tests PASS; the scoped PostgreSQL case
remains UNVERIFIED. Built IAB desktop/narrow, keyboard, console and no-auto-enqueue
checks PASS. This does not change owner screening policy or prove live coverage.
Final candidate regression, readiness/job/valuation detail, security review and
PR/merge gates remain open; M4 is not complete at this checkpoint.

M4 is not done from a build or fixture-only screenshot. Prove the integrated
owner workflow and all required error states, record actual data/provider limits,
and verify PR merge. Missing live credentials must be reported accurately rather
than inventing charts or claims. No automatic provider-call spend is authorized.
