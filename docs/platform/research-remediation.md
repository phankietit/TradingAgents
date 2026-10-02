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

Every ticket carries one type, area and priority below. Statuses distinguish
implemented local evidence from live acceptance; see the verification receipt.

| ID | Type / area / priority | Dependencies | Acceptance | Status |
| --- | --- | --- | --- | --- |
| R01 | docs / docs / P1 | — | Baseline, flow parity and regression cases recorded | PASS |
| R02 | bug / data / P0 | R01 | Explicit session dates, closes, cutoff; legacy snapshots readable | PASS local + new Yahoo snapshot |
| R03 | feature / data / P0 | R02 | Deterministic indicators, returns and window-high with provenance | PASS local |
| R04 | feature / agents / P1 | R03 | Snapshot-bound tools and asset-specific coverage; no silent role loss | PASS full-graph fixtures plus local current-news and AAPL SEC ingestion; social/macro, other-asset fundamentals and non-price live UNVERIFIED |
| R05 | bug / llm / P0 | R01 | Compatible strict schemas, bounded repair, safe diagnostics; invalid stays REVIEW | PASS local/fail-closed; live valid-report acceptance FAIL |
| R06 | bug / agents / P0 | R05 | All graph roles preserve authority and product scope | PASS deterministic authority boundary; live narrative quality FAIL |
| R07 | feature / data / P0 | R03–R06 | Claims trace to source and calculations; invalid claims block readiness | PASS local numeric/provenance gates; semantic entailment UNVERIFIED |
| R08 | bug / infra / P1 | R05 | Real stage events, usage, cancel/retry lifecycle and bounded execution | PASS local lifecycle/immutable working-note retention and synthetic web reader; latest live full-flow FAIL at wall budget; operator allowance and actual resume UNVERIFIED |
| R09 | bug / portfolio / P0 | R07–R08 | Separate source/research/approval status; deterministic risk remains authoritative | PASS local + live invalid-report display |
| R10 | feature / web / P1 | R01,R09 | Complete design specification based on approved Linkpolish reference | PASS |
| R11 | feature / web / P1 | R08–R10,R12 | Responsive workspace, real snapshot chart, working research flow | PASS UI and real processing flow; valid final report FAIL |
| R12 | feature / web / P1 | R05,R07,R10 | Safe readable bilingual report, identical evidence/numbers across views | PASS local/saved switching; live bilingual quality FAIL |
| R13 | test / agents / P0 | R02–R12 | Local regression, representative asset fixtures and live MiniMax evidence | PASS local; live valid-report acceptance FAIL |
| R14 | docs / docs / P1 | R13 | Exact-SHA receipt, local scripts, limitations and migration/recovery instructions | PASS receipt and Draft PR #7; overall release DEFERRED |

Overall goal is not complete. The previous extra BTC execution failed report
acceptance; its immutable failure receipt remains valid. On 2026-09-27 the owner
renewed implementation and live-test authorization for BTC, AAPL and NQ, including
the operational research journey and final decision-report presentation.

### Current operational finding · 2026-10-01

The authenticated live BTC market+news job at `f73d1a9` ended in
`RESEARCH_BUDGET_EXHAUSTED` after about 37m38s / 539,339 reported tokens.
All nine preceding stages completed; Portfolio Manager started and its bounded
repair consumed the remaining time. Financial validation/presentation did not
start. No final report or decision was published; this is FAIL, not finance or
translation acceptance. The 30-minute observer deadline is checked between
stages/calls and cannot interrupt an already-running SDK request.

R08 still needs an explicit operator-visible execution allowance consistent
with request timeouts, and durable recovery/read-only completed-stage research
so a failure does not force blind paid recomputation. These must preserve all
roles, immutable source/config bindings, lease/owner fencing, and final
publication/approval gates. Do not simply increase budgets silently, skip
roles, publish partial work as a decision, or retry whole paid jobs automatically.

The next code slice adds `research_stage` immutable artifacts for returned
allowlisted reader text, fenced by the existing job lease/cancellation boundary.
These remain unvalidated/non-approvable even after Financial validation returns;
only the separate final pipeline can publish a decision. No raw prompts,
messages, reasoning metadata or executable state is serialized. Returned text
can survive a boundary deadline without claiming stage/run completion.

This is working-note retention, **not graph resume**. The existing CLI SQLite
checkpoint signature lacks web owner/source/model/prompt binding, so it is not
enabled for this path. The original failed BTC has no saved notes to backfill.
The web groups these notes separately from final reports, loads contents only
on demand and always displays nonapproval/unvalidated warnings. Interface
language switching preserves original text without AI translation. Local DOM
and built-web synthetic desktop/mobile checks cover this reader, not provider
or financial acceptance. Notes above the preview byte limit remain download-only.
Next: explicit allowance/request-timeout behavior and properly fingerprinted/
fenced recovery without repeating completed paid work.

### Renewed acceptance scope

- Validate canonical financial content before a separate, bounded localization
  stage. Protect quantitative tokens in translation; never weaken publication
  validation to make a model response pass. Preserve every research/debate role.
- Present a clear prepare → research → validation → review journey using real
  events. Keep diagnostic details secondary and distinguish processing success
  from a financially usable report.
- Make summaries, evidence, opposing views, risks, invalidation and coverage easy
  to navigate on desktop/mobile in both languages; retain original agent reports.
- Run live BTC, Apple and NQ using the existing MiniMax configuration. NQ remains
  reference-only. Record exact inputs, coverage, usage, output checks and limits;
  do not imply that a price-only run includes fundamentals, news or macro data.
- Verify locally without CI, update Draft PR #7 and its exact-SHA receipt. No
  broker, new provider, risk-limit change, historical rewrite or public deployment.

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
