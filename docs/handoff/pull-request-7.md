## Problem and current behavior

Research runs could finish while their financial narrative, quantitative
relationships or Vietnamese report were not usable. This branch retains the
original analysis/debate/risk graph, adds immutable data and quantitative
publication checks, and provides a private bilingual financial web workspace.
Manual live acceptance still fails on unsupported qualitative claims and
translation fidelity; the latest market+news BTC job also exhausted its stage-
boundary time budget before publication. The product is incomplete and this
PR remains draft.

## Scope

- Approved R01–R14 backlog in `docs/platform/research-remediation.md`.
- Full-history session-aware snapshots, deterministic indicators/returns and
  paged analyst tools; canonical research and bounded EN/VI presentation.
- MiniMax whole-message JSON/schema validation, bounded repair, usage and
  real stage progress; research separated from deterministic portfolio approval.
- Responsive web workflow, with completed reports displayed first and processing
  preserved in an expandable section. Saved bilingual summaries, charts,
  research and verification are readable without another model call.
- Yahoo recent-news collection, immutable owner-scoped storage, authenticated
  preparation API and EN/VI controls. Feed coverage remains non-exhaustive.
- Owner-approved existing SEC EDGAR ingestion for AAPL web, preserving filing
  dates and exact fact IDs; no CLI-default or provider substitution.
- Application-owned SEC metric/period/unit sentences and structural protection
  against translated negation or unit changes; qualitative review is still required.
- Immutable owner/source/config-bound stage working notes, published behind
  cancellation/lease fences. They are always unvalidated and ineligible for
  approval; dedicated bounded web reading is implemented, graph resume remains unfinished.
- Durable execution-entry marker and queue/lease guards prevent blind paid
  replay after uncertain execution; committed-output, model-free finalization
  remains idempotent. No SDK timeout/retry or execution allowance change.
- Social/macro ingestion and other-asset fundamentals remain unfinished.
- `HANDOFF.md`, `CLAUDE.md`, governance and QA source archives allow continuation
  from another machine without relying on chat history.

Base: `main` (`7dfec4d` at checkpoint). Head: `fix/TA-R01-research-quality`.
Includes prerequisites from open PRs #5/#6; do not duplicate their changes.
GitHub Issues are disabled; repository tickets are the backlog.

## Verification and remaining gates

- PASS on runtime source `93e797576b9179e088f6ff809761bddd34cc3df6`: 1,608
  Python tests + 88 subtests, 20 classified skips, 50.14 s; Ruff/diff/templates.
  Focused lifecycle/recovery proof: 55 passed, 2 PostgreSQL skips. The preceding
  9fdbdb0 regression failed committed-output recovery; this was corrected, not
  waived. SQLite/fake-model proof is not live or PostgreSQL acceptance.
  Web refresh: 134 tests/22 files, typecheck/lint/build PASS on the same source.

- PASS on web reader source `1a01f21455fa351017319ad6283bb8307defe0ee`:
  134 Web tests, typecheck/lint/build; actual built app with synthetic API fixtures
  at 1280×900/390×900, no console/page errors or overflow, one on-demand note GET
  and zero mutations. Locale switching preserves original text; no approval
  link. Not live model/source/financial acceptance. See receipt 2026-10-02.

- PASS on code SHA `ecbb7d3f25ac0d64defdc9231afabe8dea59edb0`: 1,600 backend
  tests + 88 subtests, Ruff, diff check; 20 classified skips. Web: 122 tests,
  typecheck/lint/build PASS. PostgreSQL (18), optional Bedrock and live DeepSeek
  remain unverified.
- Local lifecycle tests prove returned notes survive failure/deadline without
  publishing a decision, and cancellation/lease loss prevent stale publication.
  Original native LangGraph fake-model checks retain all 14 roles. These are
  not provider, financial, translation or resumability acceptance.
- Built-web browser synthetic verification PASS at 1280×900 and 390×844:
  compiler/worker/API → saved bilingual report; tab/language switching retains
  quantities, zero new run POSTs, linked decision preserves approval gates,
  no pageerror or overflow. This is not live model/translation acceptance.
- Live BTC on `5bbbdee`: full 11-stage backend replay, 14 model calls, 480,325
  reported tokens. Automatic checks passed; manual semantic/editorial acceptance
  failed. It used market-only snapshots and was not registered as an owner decision.
- AAPL live full-graph and later component replay results are recorded in
  `docs/platform/research-acceptance-20260927.md`; manual acceptance remains FAIL.
- NQ identity is owner-selected `NQ=F`, reference-only. Owner chose BLOCKED until
  a valid contract/roll source exists; no substitute provider or index is added.
- Live SEC/API source PASS: AAPL has 1,159 selected filed facts, zero invalid;
  BTC real API prepared and bound price/recent-news snapshots. Source success
  is not a validated final research report.
- Latest BTC on `f73d1a9`: FAIL `RESEARCH_BUDGET_EXHAUSTED`, about 37m38s,
  13 calls / 539,339 tokens, attempt 1/1. Nine stages completed; Portfolio Manager
  started; validation/presentation did not start; zero published outputs.
  Existing observer checks the 30-minute budget at boundaries, not mid-request.
- Live BTC/AAPL semantic/editorial acceptance after the newest fix, operational
  allowance/recovery, social/macro ingestion and PostgreSQL still require
  evidence. No extra paid replay occurred on the new code SHA. See the dated
  receipt rather than promoting an older test result to HEAD.

Use `HANDOFF.md` as the continuation entry point and the dated acceptance ledger
for exact SHA/usage/evidence. No hosted CI is used: workflow was explicitly
disabled at checkpoint per owner preference. Local checks remain required.

## Data and operational boundaries

Private local research candidate. No broker/execution, provider replacement,
risk-limit change, public deployment or historical rewrite. Numeric checks do
not establish qualitative entailment or translation accuracy. Empty/missing
source coverage is explicit, never fabricated as neutral or comprehensive.

API and worker must use consistent configuration. The public Git repository
contains no populated env, owner database, raw private reports or artifact store.
Restoring an existing private workspace requires a separate secure transfer of
secrets and a consistent database/artifact backup as explained in `HANDOFF.md`.
This checkpoint does not authorize merging or claiming release readiness.
