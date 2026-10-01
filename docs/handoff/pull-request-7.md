## Problem and current behavior

Research runs could finish while their financial narrative, quantitative
relationships or Vietnamese report were not usable. This branch retains the
original analysis/debate/risk graph, adds immutable data and quantitative
publication checks, and provides a private bilingual financial web workspace.
Manual live acceptance still fails on unsupported qualitative claims and
translation fidelity. The product is incomplete and this PR remains draft.

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
- Social/macro ingestion and other-asset fundamentals remain unfinished.
- `HANDOFF.md`, `CLAUDE.md`, governance and QA source archives allow continuation
  from another machine without relying on chat history.

Base: `main` (`7dfec4d` at checkpoint). Head: `fix/TA-R01-research-quality`.
Includes prerequisites from open PRs #5/#6; do not duplicate their changes.
GitHub Issues are disabled; repository tickets are the backlog.

## Verification and remaining gates

- PASS on code SHA `25476690deac0e6035c34d65759d660b4bc4f3a3`: 1,506 backend
  tests + 88 subtests, Ruff, diff check; 20 classified skips. Web: 122 tests,
  typecheck/lint/build PASS. PostgreSQL (18), optional Bedrock and live DeepSeek
  remain unverified.
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
- SEC live, BTC/AAPL live semantic/editorial acceptance, social/macro ingestion
  and PostgreSQL still require evidence. See the current dated receipt rather
  than promoting an older test result to HEAD.

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
