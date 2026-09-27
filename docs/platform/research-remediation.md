# Research quality and product delivery

Approved scope: R01–R14, 2026-09-27. Release class: local private research
platform, with human decision review. No broker or public deployment.

## Baseline

- Base: origin/main `7dfec4d20709a702b130f3ba5813f097a930ffe6`.
- Prerequisite: PRs #5/#6, through `0a81d479b1b150573a8854a94ee5d2900f0c0550`.
- Branch: `fix/TA-R01-research-quality`; existing managed worktree reused.
- GitHub Issues are disabled. This file records the approved tickets locally.
- CI remains disabled by owner preference. Verification runs locally.
- Existing run/snapshot artifacts are immutable; fixes produce new runs.

## Tickets and acceptance

Every ticket carries one type, area and priority below. `planned` does not mean
implemented. Live provider results are recorded separately from local tests.

| ID | Type / area / priority | Dependencies | Acceptance | Status |
| --- | --- | --- | --- | --- |
| R01 | docs / docs / P1 | — | Baseline, flow parity and regression cases recorded | PASS |
| R02 | bug / data / P0 | R01 | Explicit session dates, closes, cutoff; legacy snapshots readable | in-progress; unit PASS |
| R03 | feature / data / P0 | R02 | Deterministic indicators, returns and window-high with provenance | in-progress; unit PASS |
| R04 | feature / agents / P1 | R03 | Snapshot-bound tools and asset-specific coverage; no silent role loss | planned |
| R05 | bug / llm / P0 | R01 | Compatible strict schemas, bounded repair, safe diagnostics; invalid stays REVIEW | planned |
| R06 | bug / agents / P0 | R05 | All graph roles preserve authority and product scope | planned |
| R07 | feature / data / P0 | R03–R06 | Claims trace to source and calculations; invalid claims block readiness | planned |
| R08 | bug / infra / P1 | R05 | Real stage events, usage, cancel/retry lifecycle and bounded execution | planned |
| R09 | bug / portfolio / P0 | R07–R08 | Separate source/research/approval status; deterministic risk remains authoritative | planned |
| R10 | feature / web / P1 | R01,R09 | Complete design specification based on approved Linkpolish reference | planned |
| R11 | feature / web / P1 | R08–R10,R12 | Responsive workspace, real snapshot chart, working research flow | planned |
| R12 | feature / web / P1 | R05,R07,R10 | Safe readable bilingual report, identical evidence/numbers across views | planned |
| R13 | test / agents / P0 | R02–R12 | Local regression, representative asset fixtures and live MiniMax evidence | planned |
| R14 | docs / docs / P1 | R13 | Exact-SHA receipt, local scripts, limitations and migration/recovery instructions | planned |

## Flow parity contract

Both paths retain Market / applicable News / Social / Fundamentals analysts,
Bull, Bear, Research Manager, Trader, Aggressive / Conservative / Neutral Risk,
and Portfolio Manager. Analyst selection follows the asset profile and explicit
source coverage. The web must never label a market-only run comprehensive.

CLI uses the existing live tool boundary. Web uses immutable per-run sources:
price queries and indicators must replay those sources rather than fetch live
data during a historical research run. Provider failure is not missing data.
Snapshots are not compressed by truncating history. Deterministic calculations
provide grounded facts and tools retain access to full underlying history.

The graph output is research. Only validated structured narrative and cited
evidence can form a decision candidate. Portfolio evaluation additionally
requires owner inputs and deterministic policy checks. Free-text fallback is
retained for inspection and cannot authorize readiness.

## Regression cases

- BTC daily timestamps represent closes, not Yahoo session labels.
- Alternating highs/lows must not be called consecutive lower highs/lows.
- 365-calendar-day and 90-calendar-day returns must use explicit endpoints.
- Five-year highest price is not asserted to be an all-time high.
- Missing schema fields, absent tool calls, unsupported capabilities and
  malformed output must remain distinguishable.
- A cancelled job must not leave its run displayed as active.
- A valid source with invalid LLM output must not be called inaccessible.
- No portfolio input is different from an empty portfolio.

## Design contract

Reference: owner's Linkpolish desktop capture, 2026-09-27. Use its restrained
charcoal surfaces, strong typography, generous spacing and clear primary action
within a financial workspace (not the landing-page layout). No Image Gen.

Keep four routes: Markets, Research, Portfolio, Decisions. Desktop uses a compact
navigation rail and spacious content; mobile uses accessible navigation and a
single content column. Use a shared type/space/color system: near-black canvas,
neutral raised surfaces, warm-white primary action, semantic green/red only for
financial meaning, visible keyboard focus. Controls use deliberate typography.

Research anatomy: asset/cutoff/coverage, snapshot price chart and deterministic
metrics, concise thesis, supporting and opposing evidence, invalidation,
limitations, optional portfolio impact. IDs, model details and diagnostic events
live in expandable audit sections. Source lag and invalid results remain visible.

Read-only reports never invoke AI. Language switching changes presentation of
saved content. No fake prices, fabricated progress percentages or mock charts in
the shipped runtime. Approval state must agree with the backend.
