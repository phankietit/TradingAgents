# Milestone 3 verification checkpoint

This is local backend-foundation evidence, not production readiness or milestone
completion. PLAN-030 through PLAN-037; no Web UI, paper simulator, broker or orders.

## Candidate

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
| Scoped security review | UNVERIFIED | Durable scan created for tested range; capability preflight READY, source review not yet complete |
| PR/review/merge | BLOCKED | Push rejected; PR creation failed because branch was not uploaded; no PR exists |
| Browser/deployment/broker | NOT_IN_SCOPE | No Web UI or deployment/order path in M3 |

The new CI configuration installs both dev and platform extras on Python
3.10–3.13 and adds a dedicated PostgreSQL integration job. Do not remove this
gate to bypass the GitHub permission failure.

## Remaining work

1. Owner authorizes the current GitHub credential for workflow updates, then
   retry the same branch push and create/attach the draft PR.
2. Continue existing security scan `ba0bb730-304e-461b-99cb-9692520dd95f`, range
   `f76c353..8364663`; do not create a replacement scan. Preflight has passed;
   threat-model/source review and finalization remain.
3. Complete acceptance review, triage any findings, rerun gates after fixes,
   obtain cross-version CI evidence, refresh this receipt/tracker and merge only
   with passing in-scope gates.

Local tests use synthetic holdings, policies, sources and model responses.
They do not establish live-provider quality, historical model knowledge,
portfolio performance, private deployment readiness or financial suitability.
