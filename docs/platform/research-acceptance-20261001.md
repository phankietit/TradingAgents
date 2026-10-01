# R04 current-news checkpoint — 2026-10-01

Class: local private decision-support candidate, **not release approval**.
Code candidate: `a0bfaae6a1efa5266517a84e4d2f37dc68a56a2f` on
`fix/TA-R01-research-quality`, Draft PR #7 against `main`. This receipt
describes that exact code SHA; later documentation-only commits do not
retroactively change what was tested. No CI, broker, risk-limit, provider or
historical-record change.

## Implemented scope

- Existing Yahoo/yfinance `Ticker.get_news` current-vintage collector now has
  a 45-second subprocess deadline; no fallback vendor.
- `NewsSnapshotService` validates canonical identity, publication/retrieval
  cutoffs, owner access, content hash, artifact and manifest consistency,
  immutable retry and transaction rollback. Invalid/no-data/outage batches may
  be retained for audit but cannot be bound as usable research evidence.
- Authenticated/CSRF-protected `prepare-news` exposes a separate, optional
  current-news step. The web keeps price and news coverage distinct, resets
  paid-model consent and never submits an AI job during preparation. Bilingual
  copy discloses that the seven-day feed is not exhaustive or historical.
- The synthetic local browser fixture explicitly refuses news as well as
  price vendor reads.

## Verification

| Gate | Result | Evidence |
| --- | --- | --- |
| Python full suite at code SHA | PASS | `.venv/bin/python -m pytest -q --disable-warnings`: 1,495 passed, 20 skipped, 88 subtests, 48.48 s; Python 3.14.7 |
| Ruff and diff | PASS | `.venv/bin/python -m ruff check .`, `git diff --check` |
| Web tests | PASS | `npm test`: 117 tests/21 files; Node 26.8.1, npm 11.19.0 |
| Web type/lint/build | PASS | `npm run typecheck`, `npm run lint`, `npm run build` |
| API/source unit integration | PASS | 30 focused tests for collector, snapshot and API; no provider/model call in tests |
| Browser synthetic desktop/mobile | PASS | Built web at loopback 127.0.0.1:8000; Playwright because Browser plugin was unavailable; login → AAPL Analyze → optional news → expected unavailable state; no AI job, no pageerror, no 390 px horizontal overflow; Vietnamese label/status checked. Initial unauthenticated 401 is expected auth bootstrap. |
| AAPL Yahoo direct source smoke | PASS | One current Yahoo news read on 2026-10-01 UTC: `OK`, 100 recent articles, 2.68 s. No article text or private credentials persisted in this receipt. |
| PostgreSQL integration | UNVERIFIED | 18 PostgreSQL skips; existing local container was not restarted for this checkpoint |
| Live API → snapshot → run with Yahoo news | UNVERIFIED | Direct source smoke is not end-to-end live API proof |
| Paid MiniMax full graph BTC/AAPL/NQ | UNVERIFIED | No paid model runs in this checkpoint; historical manual failures remain open |
| Overall R01–R14 acceptance | FAIL | Fundamentals/social/macro, semantic finance/translation, operational UI and live asset acceptance remain unfinished |

No private database, artifact payload, market article text, account data,
provider key or populated environment file is committed. UI screenshots were
local synthetic QA artifacts outside Git and are not production evidence.

## Required continuation

1. Make asset-specific fundamentals/social/macro ingestion and evidence
   contracts explicit without introducing an unapproved vendor. Preserve
   point-in-time rules; current-only feeds cannot backfill historical runs.
2. Resolve previous live BTC/AAPL financial-meaning and Vietnamese-translation
   failures, then verify the full original graph with human editorial review.
3. Polish and browser-test prepare → research → validation → decision review
   for desktop/mobile. Do not treat processing completion as usable research.
4. Run representative live BTC, AAPL and an explicitly chosen NQ reference
   instrument, recording SHA, coverage, provider usage and manual result.
   `NQ=F` is futures reference-only; `^NDX` is the cash index. Neither
   permits a futures position or broker action.
5. Keep PR #7 draft and the goal active until every required acceptance gate
   is actually met. Skipped external gates stay UNVERIFIED, not PASS.

## Follow-up candidate: deterministic news disclosure

Code commit `cd033ddfd1ef04f424c6c7cc867c58138a0f3a51` adds a bilingual,
application-owned report notice when an eligible Yahoo news snapshot is marked
`recent_feed_not_exhaustive`. The model cannot omit this notice from the saved
report; it does not assert that missing news means a neutral market. Local
regression at this code SHA: **1,496 passed, 20 skipped, 88 subtests passed**
in 37.49 s; focused Ruff and `git diff --check` PASS. The skips include 18
PostgreSQL environment tests and two optional-provider tests. No paid model or
live API-to-report run occurred at this candidate.

The owner selected **NQ=F** for reference-only acceptance, not `^NDX` or an
ETF substitute. Live NQ acceptance remains **BLOCKED**: the existing Yahoo
continuous symbol lacks the active/next-contract and roll metadata required by
`FuturesReferencePipeline`. No futures position, order, or substitute source
is permitted by this selection. A source and its data/licensing contract must
be explicitly resolved before claiming a valid live NQ report.
