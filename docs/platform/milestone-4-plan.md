# Milestone 4 — local quant research web

Base: `e45e079b718c29f5fef8de399ed3ce002bcf1f97` (M3 PR #3 merged).
Branch: `feature/TA-M4-local-web-ui`; reuse the clean managed M3 checkout.
Owner: this Codex task only. Root checkout and other worktrees remain untouched.

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

No frontend framework currently exists. Proposed stack: React + TypeScript +
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

Status: in-progress (CSRF and workspace discovery implemented; watchlist pending). Depends on M4-FOUNDATION.

Discovery checkpoint: bounded owner portfolio/policy list/detail, run artifact
metadata without storage paths, and owner-readable snapshot discovery with shared
temporal/freshness metadata checks. Content integrity is explicitly still checked
at run creation. API/persistence/snapshot-analysis tests: 38 PASS, PostgreSQL gate
skipped (UNVERIFIED; no schema migration in this checkpoint). Browser consumers
and persisted watchlist remain pending.

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

Status: planned. Depends on M4-API and M4-SHELL.

- AAPL instrument selection, persisted watchlist, daily chart plus OHLCV table;
  current metrics come from backend, not duplicate financial calculations.
- Source/as-of/quality/currency/timezone and clear empty/stale/error states.
- Reuse group-specific calendars/profiles for ETF, BTC/ETH and NQ/ES; reference
  labels and no execution affordance on NQ/ES.
- Tests: selection/filtering/reload, missing bars, missing source, backend errors,
  snapshot cutoff and accessible chart alternative.

### M4-ANALYSIS — real durable analysis workflow

Status: planned. Depends on M4-MARKETS.

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

Status: planned. Depends on M4-API and M4-SHELL.

- Display immutable portfolio snapshot, holdings/cash/NAV/allocation and source clock.
- Explain deterministic policy observations, missing correlation/coverage and limits.
- No implicit policy creation, history rewriting or risk-limit change.
- Tests: owner isolation, no portfolio, unavailable price/valuation, precision and
  unit formatting, currency labels and repeated load consistency.

### M4-DECISIONS — human review and audit

Status: planned. Depends on M4-ANALYSIS and M4-PORTFOLIO.

- Display original research separately from current state/event history.
- Approval/rejection requires explicit confirmation and reason, uses expected
  status/version and idempotent event identity; reload retrieves persisted state.
- Rejected backend policy/run/CSRF/conflict must remain rejected visibly; disabling
  a frontend button is never considered authorization enforcement.
- Tests: valid approval, REVIEW/failed-risk/cancelled-run denial, terminal conflict,
  repeated submission, expired session and event history after reload.

### M4-ACCEPTANCE — browser, security and delivery

Status: planned. Depends on all tickets above.

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

M4 is not done from a build or fixture-only screenshot. Prove the integrated
owner workflow and all required error states, record actual data/provider limits,
and verify PR merge. Missing live credentials must be reported accurately rather
than inventing charts or claims. No automatic provider-call spend is authorized.
