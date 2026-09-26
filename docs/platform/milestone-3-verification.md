# Milestone 3 verification checkpoint

This is local backend-foundation evidence, not production readiness or milestone
completion. PLAN-030 through PLAN-037; no Web UI, paper simulator, broker or orders.

## Latest follow-up checkpoint

At `129696b5bdd667d4709aa392f83fe4a63078c27d`, snapshot asset guidance,
structured-call log redaction, Python 3.10-compatible UTC imports and immutable
research receipt tests are implemented. Full regression with a dedicated
PostgreSQL 16 container passes **1228 tests and 88 subtests**, 2 optional provider
skips and 22 warnings (26.07s). Command:
`TEST_POSTGRES_URL=<disposable-test-db> .venv/bin/python -m pytest -q --disable-warnings`.
Ruff and diff checks pass. The owned `ta-m3-pg-20260927-refresh` container was
stopped and removed after verifying its task label; its synthetic tmpfs data
is discarded. No user database was changed.

The existing isolated non-editable install was refreshed with
`python -m pip install --no-deps --force-reinstall '.[platform]'` and
`python -m pip check` passes. Installed imports outside the checkout and worker
help pass. This is an install refresh, not a newly created environment.
An initial smoke command used the wrong public import path; the verified class
path is `tradingagents.platform.evaluation.replay.PersistedEvaluationService`.
Python 3.10 container verification was BLOCKED by an unavailable Docker credential
helper; the UTC regression test is not cross-version runtime evidence.

GitHub OAuth was rechecked and still lacks `workflow`. Cross-version CI, PR,
merge and post-fix security review remain outstanding. Configuration audit
confirmed that receipt replay reuses recorded research, not full LLM configuration
or response replay; the evaluation contract now states this explicitly.

## Previous follow-up checkpoint

At `a96ff29becce19ae0d552f6b39f1195fe9260d49`, source-review follow-ups now
reject future-observed quotes/evidence at pure-library boundaries, require a
successful analysis run before approval, and contain lease-loss races during
cancellation acknowledgement. `.venv/bin/python -m pytest -q --disable-warnings`
passes 1200 tests and 88 subtests, with 19 skips and 22 warnings (18.25s).
Those skips include 17 PostgreSQL cases because the disposable database had
been removed, plus optional Bedrock/live DeepSeek. Lint and diff checks pass.
The PostgreSQL/install evidence below applies to the earlier SHA only and must
be refreshed after the follow-up changes.

Security scan `ba0bb730-304e-461b-99cb-9692520dd95f` completed source review of
all 49 changed runtime/build files in `f76c353..8364663`, plus supplemental tests
and docs. No plausible new security vulnerability was established. The sealed
scan nevertheless retains an older checkpoint's deferred coverage row and
reports `partial`; do not represent the canonical scan as complete coverage.
Its old-SHA result also does not cover the subsequent functional fixes. Keep
that sealed result intact and perform a new candidate review after remaining
fixes; do not overwrite or relabel it.

## Earlier candidate evidence

- Branch: `feature/TA-030-analysis-engine`.
- Tested SHA: `83646631ba9f2b0e697cc0370a8989ec2cda862f`.
- Base/current origin main: `f76c353ee912e6d6d16ff1ba660287a6a383a291`.
- Worktree: `/Volumes/Data/codex/worktrees/ta-030-analysis-risk/TradingAgents`.
- Runtime: macOS 26.5.2, Python 3.14.7, PostgreSQL 16.14 (postgres:16-alpine).
- Worktree was clean at verification. This receipt is a subsequent docs-only change.
- Date: 2026-09-27 Asia/Ho_Chi_Minh.

## Verification

| Gate | Status | Evidence |
| --- | --- | --- |
| Full suite with dedicated PostgreSQL | PASS | `TEST_POSTGRES_URL=<disposable-test-db> .venv/bin/python -m pytest -q --disable-warnings`: 1207 passed, 2 skipped, 22 warnings, 88 subtests; 23.87s |
| PostgreSQL M3 integration | PASS | `tests/test_milestone3_postgresql.py`: 5 tests; upgrade/schema parity/downgrade, concurrent identical and conflicting approvals, persisted owner ledger valuation and risk/evaluation replay |
| Lint | PASS | `.venv/bin/python -m ruff check .` |
| Diff whitespace | PASS | `git diff --check` |
| Clean non-editable install | PASS | Fresh `.clean-install-HCJEHG/venv`, `python -m pip install '.[platform]'`; imports from installed site-packages outside source root |
| Installed dependency consistency | PASS | Clean environment `python -m pip check`: no broken requirements |
| Installed worker entrypoint | PASS | `tradingagents-worker --help`; import of runtime and persisted evaluation service |
| Optional Bedrock test | UNVERIFIED | `langchain_aws` is not installed in regression environment |
| Live DeepSeek test | UNVERIFIED | No configured test credential; no live call made |
| Cross-version GitHub CI | BLOCKED | Push rejected because current OAuth grant lacks `workflow` scope for `.github/workflows/ci.yml` |
| Scoped security review | UNVERIFIED | Source review completed at old SHA, no candidate findings; canonical sealed coverage retains stale partial checkpoint; post-fix review still required |
| PR/review/merge | BLOCKED | Push rejected; PR creation failed because branch was not uploaded; no PR exists |
| Browser/deployment/broker | NOT_IN_SCOPE | No Web UI or deployment/order path in M3 |

The new CI configuration installs both dev and platform extras on Python
3.10–3.13 and adds a dedicated PostgreSQL integration job. Do not remove this
gate to bypass the GitHub permission failure.

## Remaining work

1. Owner authorizes the current GitHub credential for workflow updates, then
   retry the same branch push and create/attach the draft PR.
2. Functional review follow-ups are implemented at `129696b`; verify the
   supported Python matrix in CI. Full LLM invocation replay is not claimed;
   the documented receipt contract covers immutable recorded research only.
3. Run dependency/secret checks and a post-fix candidate security review with
   accurate coverage metadata. Preserve the sealed old-SHA scan unchanged.
4. Complete acceptance review, triage any findings, rerun gates after fixes,
   obtain cross-version CI evidence, refresh this receipt/tracker and merge only
   with passing in-scope gates.

Local tests use synthetic holdings, policies, sources and model responses.
They do not establish live-provider quality, historical model knowledge,
portfolio performance, private deployment readiness or financial suitability.
