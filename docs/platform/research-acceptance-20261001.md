# R04 current-news checkpoint — 2026-10-01

Latest code/evidence: see **SEC statement boundaries and live BTC deadline**
at the end. Earlier sections remain exact-SHA historical receipts.

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

## Follow-up candidate: AAPL SEC and report reading

Code commit `f69e3293e74ee0f1f32b7daec38a99a64c585942` adds the
owner-approved existing SEC EDGAR path for AAPL only, leaving CLI defaults and
all other asset groups unchanged. Current-vintage facts retain accession,
filing date, period, tag and unit; missing/malformed/outage remain distinct.
The web has a separate optional SEC action and one-year latest-filing freshness
check. The analyst can page the complete immutable fact history, while final
quantities resolve exact fact IDs. An application-owned bilingual notice says
US GAAP tags are not a complete company profile or historical vintage.

The saved bilingual report's application-owned headings can now render a
scannable executive summary, thesis, risks, invalidation and horizon; unknown
layouts fall back to the unmodified full Markdown. Missing analyst roles stay
visible. No finding is hidden and no model conclusion is changed by this UI.

| Gate | Result | Evidence |
| --- | --- | --- |
| Python regression at code SHA | PASS | 1,505 passed, 20 skipped, 88 subtests, 46.86 s |
| Python Ruff/diff | PASS | `.venv/bin/ruff check .`, `git diff --check` |
| Web tests/type/lint/build | PASS | 121 tests/22 files; `npm run typecheck`, `npm run lint`, `npm run build` |
| SEC collector/API/quantity fixtures | PASS | Mocked filed-vintage/restatement, owner API preparation/reuse, run binding and fact-ID compilation; no SEC request |
| Browser synthetic desktop/mobile | PASS | Built web, fixture-only API/worker: AAPL SEC action returns expected unavailable without AI job; EN/VI, no pageerror, no 1280/390 px overflow. Synthetic processing remains visibly Needs validation. |
| Live SEC companyfacts | UNVERIFIED | A real `SEC_EDGAR_USER_AGENT` contact has not yet been configured in this worktree; no live SEC request |
| Valid bilingual report browser reading | UNVERIFIED | Component parser/render tests PASS; synthetic graph does not publish a financially validated localized report |
| Paid BTC/AAPL/NQ finance/translation acceptance | UNVERIFIED | No paid run at this code SHA; NQ=F remains blocked on source contract/roll metadata |

The fixture server was stopped after browser checks. Its labelled synthetic
database is private, ignored local test state, not investment evidence. No
secrets, provider payloads or populated `.env` were committed.

## Follow-up candidate: completed report first and bilingual browser proof

Code commit `25476690deac0e6035c34d65759d660b4bc4f3a3` fixes a rendered
workflow issue: completed processing occupied the first viewport and evidence
downloads appeared before the report. Completed research now presents the saved
report first, with processing retained in a collapsed disclosure. Active and
failed runs keep their processing/error information visible. Validation findings
and missing coverage remain in the report's primary view.

The explicit `--graph-result bilingual` synthetic fixture uses the real quantity
compiler, canonical publication checks, durable worker, artifact/evidence
persistence and authenticated API. It substitutes graph/model output solely for
UI QA; its labelled generated prices and fixed translations do not establish
live reasoning, translation accuracy or graph-role parity.

| Gate | Result | Evidence |
| --- | --- | --- |
| Python full regression | PASS | `.venv/bin/python -m pytest -q --disable-warnings`: 1,506 passed, 20 skipped, 88 subtests, 38.78 s; Python 3.14.7 |
| Ruff and diff | PASS | `.venv/bin/ruff check .`, `git diff --check` |
| Web test/type/lint/build | PASS | 122 tests/22 files, typecheck/lint; production build PASS; Node 26.8.1/npm 11.19.0 |
| Bilingual durable publication integration | PASS | Synthetic immutable daily-price binding → compiler → validation → worker → report/evidence; exact close fact retained in both languages |
| Desktop/mobile saved-report reading | PASS | Playwright at loopback 127.0.0.1:8000, 1280×900 and 390×844; Summary, Price history, Research detail, Verification; EN/VI switches retain `$198.02`; completed processing collapsed; no pageerror or horizontal overflow |
| Read-only behavior and linked decision | PASS | Saved-report language/tab switches made zero run POSTs; linked decision displays Vietnamese saved content; absent portfolio/risk evaluation keeps approval disabled; zero decision mutations |
| Invalid report visibility | PASS | Regression preserves missing-format explanation in report-first layout; processing can be opened without another fetch |
| SEC live / BTC–AAPL semantic finance / live translation | UNVERIFIED | No provider/model request in this slice; prior rejected live acceptance remains unresolved |
| PostgreSQL | UNVERIFIED | 18 environment-dependent PostgreSQL skips, plus optional Bedrock and live DeepSeek skips |

Local screenshots are under `/Volumes/Data/TradingAgents-runtime/qa-reader-ObuWOH/`
outside Git. Browser plugin was absent, so existing bundled Playwright was used.
The synthetic server was stopped after verification. NQ=F remains **BLOCKED**
by the owner's source decision; no provider was added. Goal/PR remain unfinished.

### Live source/API follow-up at the same code candidate

- **PASS** AAPL SEC: authenticated `prepare-fundamentals` against live existing
  EDGAR adapter returned `ready`/`OK`, persisted 1,159 selected facts with zero
  invalid records, latest filing 2026-07-31. A real contact is already present
  in the root checkout's ignored `.env`; no contact value was printed or copied
  to the public receipt. This proves source/API persistence, not a full AAPL
  research report.
- **PASS** BTC source/API binding: five-year Yahoo price preparation returned
  `ready`/`OK` through 2026-09-30T00:00Z, explicitly marked delayed by one
  completed daily candle. News preparation returned `ready`/`OK`, 99 eligible
  recent articles, `recent_feed_not_exhaustive`. Two snapshots passed the real
  API run-input loader. No model call occurred during preparation.
- The initial isolated QA process did not load the root model env and queued
  a run with default OpenAI configuration. It was cancelled before any worker
  invocation. This is not MiniMax acceptance. Subsequent paid verification must
  explicitly load the existing root config and assert MiniMax-M3 before running.
- All source checks used fresh, task-created QA databases/artifact stores under
  `/Volumes/Data/TradingAgents-runtime/`; existing owner history was untouched.

## SEC statement boundaries and live BTC deadline

### Paid live candidate: FAIL, not a completed report

Runtime code SHA: `f73d1a946c19be9a0a94bcceb41b6c3e198edd63` on
`fix/TA-R01-research-quality`, clean at launch. Existing production Python
modules were unchanged until this job became terminal; independent new modules,
tests and docs were prepared while waiting. Provider/model remained MiniMax /
MiniMax-M3 for both roles; original graph/debate settings were not reduced.

Procedure: load the root ignored model env explicitly before importing config;
assert MiniMax-M3; create an isolated task QA database/artifact store; use the
real authenticated/CSRF API to prepare BTC prices and recent news; create one
`en-vi` market+news run bound to both immutable snapshots; execute exactly one
`JobWorker.run_once()` with the real `AnalysisEngine`/`AnalysisJobHandler`.
Job maximum attempts was one. Existing bounded per-stage format repairs remain.

- Run: `3bd8ef30-8b8c-41f5-afda-90c7d11ef922`.
- Private QA state: `/Volumes/Data/TradingAgents-runtime/qa-live-btc-final-uwsqvq8t/`.
- UTC: 2026-10-01 01:35:08.354612 → 02:12:45.946781; **2,257.592 seconds**.
- **FAIL**: run/job terminal `failed`, `RESEARCH_BUDGET_EXHAUSTED`; attempt 1/1,
  zero output artifacts and no published decision. No automatic full-run retry.
- Completed: Market Analyst, News Analyst, Bull, Bear, Research Manager, Trader,
  Aggressive, Conservative, Neutral. Portfolio Manager started but was not
  marked completed. Financial validation and Report presentation did not start.
- Usage: **13 model calls**, input **363,700**, output **175,639**, total
  **539,339** tokens; 13 calls reported usage, zero provider-call failures
  recorded. Trader and Portfolio Manager each used an existing bounded format
  repair. Token usage is not a USD invoice; provider did not report cost.
- The observer's 1,800-second budget is checked at stage/model boundaries.
  An already-running SDK request can overrun that time. The final model usage
  was retained even though publication subsequently failed.
- Five-year daily prices stop at the disclosed 2026-09-30 completed UTC candle;
  recent news has 99 eligible articles and is not exhaustive. Social/macro are
  absent. This is not a comprehensive crypto report or translation acceptance.

No completed report exists to review; do not infer financial quality from stage
progress or repair completion. The older manual semantic/translation failures
remain unresolved. R08 requires an explicit operator-visible allowance and
durable recovery/read-only completed-stage research; do not silently raise the
budget, skip roles, publish partial results as a decision or spend on retries.

### Code follow-up: bounded accounting and presentation contracts

Code SHA: `af5349dc81b01f24529a013c6b914e4003f613a7`, clean candidate.
Reproduced six local acceptance holes before fixing them: four SEC scalar
bindings could change the unit, metric or reporting period; two translations
could wrap a protected fact sentence in a negation or a different unit while
retaining every digit. These reproductions failed before the fix.

SEC quantities now render complete application-owned EN/VI observations with
the exact metric, annual/quarterly period and USD-million/per-share unit. Balance
sheet instants are distinguished from accounting flows. Unsupported identities
fail closed; source facts and existing reports are not rewritten. The translator
must keep complete fact anchors in standalone sentences; one bounded repair
remains, and an invalid result is withheld. These structural checks do not
establish qualitative entailment or comprehensive translation accuracy.

| Gate | Result | Evidence at code SHA |
| --- | --- | --- |
| Python full regression | PASS | `.venv/bin/python -m pytest -q --disable-warnings`: 1,567 passed, 20 skipped, 88 subtests, 47.56 s; Python 3.14.7 |
| Ruff/diff | PASS | `.venv/bin/ruff check .`, `git diff --check` |
| Focused compiler/SEC/presentation checks | PASS | 154 focused tests before the final prompt-only clarification; full regression above covers the committed version |
| Web tests/type/lint/build | PASS | 122 tests/22 files; `npm run typecheck`, `npm run lint`, `npm test`, `npm run build`; Node 26.8.1/npm 11.19.0 |
| Live finance/translation after code fix | UNVERIFIED | No paid request on this code candidate; f73d1a9's failed job is not acceptance for newer code |
| PostgreSQL/optional provider checks | UNVERIFIED | 18 PostgreSQL skips; optional Bedrock missing dependency and live DeepSeek key absent |
| NQ=F live | BLOCKED | Owner holds contract/roll-source selection; no new provider or substitute |
| Overall R01–R14 | FAIL | Runtime recovery, remaining sources, semantic/editorial quality and representative live reports remain unfinished |

No raw report, article text, owner database, credential, contact value or runtime
artifact is included in Git. No CI, broker, risk-limit, provider or deployment
change. Existing QA and owner history remain intact; PR #7 stays Draft.
