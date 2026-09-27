# Research workspace design specification

Owner chose direct code design, no Image Gen. This is the implementation brief,
not by itself evidence of rendered or functional UI. Reference screenshots are captured
from the actual browser as each complete surface is implemented.

## Owner acceptance requirement: finance-first, not developer-first

The owner requires a clean, modern, professional product usable without technical
knowledge, while retaining financial depth for experienced investors. This is a
mandatory M4 acceptance gate, not an optional cosmetic pass. Existing technical
checkpoint screens are implementation evidence, not the final UX standard.

- Primary hierarchy: what changed, over which period, what it means for the
  portfolio, key risks and the next permitted research/review action. Show a
  concise overview first, then financial detail, then optional technical audit.
- Keep financially meaningful terms (NAV, allocation, drawdown, volatility,
  benchmark, liquidity), with short definitions and explicit units/periods.
  Never replace precise finance concepts with vague scores or unsupported advice.
- Default screens must not lead with UUIDs, hashes, schema versions, JSON,
  internal dataset names, raw enum codes, endpoint names or infrastructure terms.
  Put these in collapsed audit/advanced details, still reachable and copyable.
  Sources, freshness, material warnings and synthetic-data labels stay visible.
- Translate system states into plain language: “Waiting to start”, “Analysis in
  progress”, “Needs review”, “Data unavailable”. Explain consequence and recovery
  action. Preserve distinctions between missing, stale, partial and failed data;
  do not turn an outage into an empty result or promise a completion time.
- Routine setup uses instrument names, readable source choices, date/time controls
  with timezone, and sensible existing defaults. ISO strings, source-age seconds,
  IDs and worker configuration belong in advanced/operator settings. No silent
  changes to financial policy, eligibility, data cutoff or cost authorization.
- Screening presents financial eligibility and readable exclusion reasons;
  ranking is explicitly not forecast return. Technical policy identity and raw
  codes belong in details; effective criteria remain inspectable. Synthetic
  policies must still be prominently identified as examples, not owner settings.
- Use restrained color, clear typography, whitespace and consistent formatting;
  compact financial tables where useful, no badge clutter or developer-console
  aesthetic. Red/green must not substitute for text or imply buy/sell instructions.
- Each main screen has a clear primary task. Secondary diagnostics do not compete
  with price/period performance, research conclusions, holdings or review actions.
- Verify that a nontechnical user can find a stock, understand the period/source,
  read the research and risks, inspect portfolio impact and record a review
  without reading JSON or typing internal IDs. Verify expert drilldowns retain
  provenance, precise financial definitions and deterministic risk checks.

Final browser review must cover all four workspaces at desktop and narrow widths,
including loading/empty/error/stale states. A passing build or functional flow
alone does not satisfy this presentation requirement. Direct code design only;
no Image Gen, paid service, new provider or public deployment is authorized.

## Layout and visual system (R10–R12, 2026-09-27)

- Reference: owner's Linkpolish, adapted to a financial workspace, not copied
  as a landing page. No image generation or remote font dependency.
- Theme: charcoal canvas `#111211`, rail `#141614`, raised surface
  `#181a18`, dividers `#2c2e2b`, primary text `#ecece8`, secondary `#989c96`.
- Accent: warm-white `#e4e8d9`, muted sage for charts; positive `#6bd7af`, warning `#efc16d`, negative
  `#ff8f99`. Never convey quality, rating or policy result by color alone.
- Typography: system sans UI, system monospace for IDs and tabular numeric values.
  Base 15px/1.6, table 13px, labels 13px, section 18px, page title 30–42px. Controls
  explicitly sized; no web-font network request. Minimum readable narrow UI 14px.
- Spacing: 4/8/12/16/24/32px. Borders 1px, controls radius 6px, major regions
  mostly square/open with dividers. Avoid nested panels and decorative gradients.
- Desktop: 216px navigation rail, spacious main header and 44px gutters; Markets uses
  instrument list 280px plus flexible chart/detail. Analysis and Decisions use
  list/detail; Portfolio uses full-width positions table and valuation summary.
- At <=900px, rail becomes top navigation; instrument/run lists collapse above
  detail. At <=600px, controls wrap and forms become one column. Tables stay in
  labelled horizontal scroll regions. No document-wide horizontal overflow.
- Focus ring: 2px warm-white, offset 3px. Reduced motion supported; no animated prices,
  pulse indicators, fake connection status or decorative loaders.

## Information architecture and native component inventory

Shell: text wordmark TradingAgents, Markets/Analysis/Portfolio/Decisions links,
owner account/logout control, page heading and contextual action. A restrained
workspace eyebrow is not a marketing hero.
Secondary text states “Local research workspace” and “Decision support · No order
execution” where scope is useful, not as marketing badges.

Shared primitives: Button (primary/secondary/danger), FormField, Select, StatusText,
Notice, EmptyState, LoadingState, DataTable, Timestamp, Money/Percent display,
ProvenanceDetails, ConfirmationDialog, ErrorBoundary and session boundary.
StatusText includes a word and optional icon, not color alone. Icons if needed
use one consistent outline family, decorative icons hidden from accessibility.

| Surface | Primary content/action | Failure/empty semantics |
| --- | --- | --- |
| Login | Owner email/password, Sign in | Invalid credentials without echo; offline retry; no public signup |
| Markets | Group filters/search, watchlist, symbol identity, price chart/table, source details, Analyze | Empty instrument master vs unavailable series distinct; stale/partial warning beside chart; no synthetic fallback |
| Analysis | Run list, input form, progress, cancel, report/evidence inspector | Queued/no worker visible; failure reason sanitized; REVIEW never relabelled complete investment advice |
| Portfolio | Snapshot selector, NAV/cash/as-of, allocation, holdings, quality/policy context | No portfolio gives operator setup guidance; missing valuation never becomes zero |
| Decisions | Candidate/current status, thesis/risks/evidence, risk checks, Approve/Reject, audit timeline | Permission/run/policy errors remain denied; refresh on conflict; unreviewable candidate explains why |

Market group labels: Stocks, ETFs, Crypto, Index references. Initial examples
are only labels/identities, not seeded live quotes. NQ/ES include “Reference only”.
Default analysis selects no provider call until the owner explicitly submits.
Dates are ISO with visible timezone; prices show currency and numeric precision.
Snapshot source and retrieval/source timestamps are available from every chart.

Confirmation dialog: exact decision identity/current status, selected action,
required reason and reminder “This records a decision; it does not place an
order.” Display backend policy checks before approval. Backend alone authorizes.
Do not visually suggest that an owner can override a failed risk check.

## Interaction and data boundaries

Route navigation has real history/deep links; restore session from /auth/me before
showing owner data. Cancel stale fetches on selection/navigation. Clear private
in-memory results on logout/session expiry; never persist reports/passwords/tokens
to localStorage. Persist watchlist server-side. Independent reads may run in
parallel; run creation and approval are explicit mutation events, never effects.

Reports render plain text or a strictly safe Markdown renderer with no raw HTML;
arbitrary source URLs do not execute or embed remote content. Evidence IDs/hashes
are details, not information users must type to navigate routine workflows.
Saved reports include the exact snapshot history (1M/3M/1Y/all with keyboard
inspection), source lag, research validity and a readable saved-language view.
Invalid JSON responses stay in an explicitly unvalidated disclosure, not the
main report body. Original analyst/debate sections are inspectable; they remain
intermediate arguments, not approved conclusions. Portfolio controls collapse
when reading research; absent holdings never display fabricated zero weights.

Dev origin: http://127.0.0.1:5173; Vite proxy to local API with the browser Origin
preserved for backend validation. Bind both servers to loopback, exact origin,
strict port rather than silently selecting another origin. Local insecure cookie
mode must be explicit for HTTP; HTTPS defaults remain untouched. Built web assets
need an explicit local static-serving entrypoint and tested SPA/API separation.

## Verification references

Capture login, populated market, missing/stale source, active/failed analysis,
portfolio, decision review/confirmation/history at desktop and narrow sizes.
Keep a fidelity ledger for layout, type, palette, spacing, state labels and focus.
No screenshot can substitute for browser workflow tests against the real API.
Fixtures must be labelled and isolated from normal owner data; do not ship fixture
fallbacks. Reconcile visible values with backend responses, not invented metrics.

Implementation references: [Vite guide](https://vite.dev/guide/) and
[local server configuration](https://vite.dev/config/server-options). These guide
tooling, not permission to expose a server or replace application authentication.
