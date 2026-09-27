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
- Responsive web workflow and report layout with technical details secondary.
- Yahoo recent-news collector with timestamp/provenance/failure contracts.
  Web still prepares prices only; non-price ingestion is unfinished.
- `NewsSnapshotService` is saved WIP, compiled/linted but not integration-tested
  or connected to API/UI. It must be reviewed before use.
- `HANDOFF.md`, `CLAUDE.md`, governance and QA source archives allow continuation
  from another machine without relying on chat history.

Base: `main` (`7dfec4d` at checkpoint). Head: `fix/TA-R01-research-quality`.
Includes prerequisites from open PRs #5/#6; do not duplicate their changes.
GitHub Issues are disabled; repository tickets are the backlog.

## Verification and remaining gates

- PASS on `50dd0df`: 1,482 backend tests + 88 subtests, Ruff; 20 classified skips.
  PostgreSQL (18), optional Bedrock and live DeepSeek were not verified there.
- WIP checkpoint: source compile, Ruff, staged diff check, handoff link check
  and staged credential scan. Earlier full-suite results do not certify WIP.
- Live BTC on `5bbbdee`: full 11-stage backend replay, 14 model calls, 480,325
  reported tokens. Automatic checks passed; manual semantic/editorial acceptance
  failed. It used market-only snapshots and was not registered as an owner decision.
- AAPL live full-graph and later component replay results are recorded in
  `docs/platform/research-acceptance-20260927.md`; manual acceptance remains FAIL.
- Current browser validation is unavailable due to admin-policy verification
  failure on the original machine. NQ reference identity still needs resolution;
  no NQ live acceptance is claimed. Current PostgreSQL verification is unavailable.

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
