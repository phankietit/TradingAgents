# Milestone 3 verification checkpoint

This is local backend-foundation evidence, not production readiness or milestone
completion. PLAN-030 through PLAN-037; no Web UI, paper simulator, broker or orders.

## Owner-approved policy change: local gates instead of hosted CI

On 2026-09-27 the owner explicitly deferred hosted CI for budget reasons.
Actions is disabled on `phankietit/TradingAgents` (`enabled=false`, read back
after update). The new M3 workflow edits are withdrawn; the workflow file now
matches `origin/main`. Use [local verification](local-verification.md) and
`bash scripts/verify-local.sh` instead. Historical CI/workflow-scope blockers
below describe the earlier policy, not a current requirement to purchase CI.
The supported multi-version matrix is UNVERIFIED locally, hosted execution is
DEFERRED by owner choice. Security report finalization remains separate.

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
merge and security report finalization remain outstanding. Configuration audit
confirmed that receipt replay reuses recorded research, not full LLM configuration
or response replay; the evaluation contract now states this explicitly.

## Previous follow-up checkpoint

### Dependency and secret-check follow-up at `b87190c`

- PASS: `pip-audit==2.10.1` in the isolated installed-package environment,
  `python -m pip_audit --progress-spinner off`: no known vulnerabilities found.
  This audits resolved packages in that environment, not every permitted future
  dependency resolution or every supported Python version. No packages were
  automatically upgraded and no vulnerability fix option was used.
- PASS (scoped): `detect-secrets==1.5.0`,
  `detect-secrets scan --no-verify` scanned the Git-tracked working tree.
  Twenty detections were limited to test fixture values and synthetic CI
  PostgreSQL credentials. Context inspection found no production credential
  reference among them. Values were not printed or network-verified. This is
  not a Git-history scan and does not inspect ignored environment files.
- PASS: `python -m pip check` after installing audit tooling. Tooling exists
  only in the ignored isolated environment; project requirements are unchanged.
- Post-fix source review scan: `d7d39786-dbad-4ed6-ae6f-1fbb232c66a4`, fixed
  range `8364663..b87190c`, 21 runtime files plus changed tests/docs. Discovery
  evidence is retained, but final canonical report is BLOCKED. The initial
  draft calls were rejected for host-owned coverage fields; completion then
  failed with `scan-manifest.json: expected a file inside the scan directory`.
  A subsequent continuation saved the semantic checkpoint and final unsealed
  draft using only accepted fields. No completion retry, replacement scan,
  manual canonical-file edit or completed-scan conclusion was made.

## Requirement-to-evidence handoff

These rows describe local implementation evidence, not release/merge approval.
The current code is identical to tested `129696b`; subsequent commits are docs.

| Requirement | Local evidence | Status |
| --- | --- | --- |
| PLAN-030 engine adapter and CLI compatibility | `8705d5d`; `test_analysis_engine.py`, `test_analysis_job_handler.py`, `test_worker_runtime.py` | PASS |
| PLAN-031 stock/ETF/reference/BTC/ETH profiles | `8bcc6e5`; `test_asset_analysis_profiles.py`, snapshot context regression | PASS |
| PLAN-032 strict narrative; invalid output REVIEW | `1a99164`; `test_strict_decision_factory.py`, `test_snapshot_decision_worker.py` | PASS |
| PLAN-033 immutable claim/source/hash/time evidence | `70caaea`; `test_evidence_graph.py`, owner-bound snapshot worker tests | PASS |
| PLAN-034 deterministic owner-scoped immutable ledger | `dd84942`; `test_portfolio_ledger.py`, `test_portfolio_valuation_service.py`, PostgreSQL replay | PASS |
| PLAN-035 deterministic weights, concentration, exposure, correlation, turnover and data quality | `fa3a8a0`; `test_risk_engine.py`, `test_risk_provenance.py`, PostgreSQL replay | PASS |
| PLAN-036 human approval and audit lifecycle | `ebc2e39`; `test_decision_lifecycle.py`, `test_decision_event_persistence.py`, `test_decision_api.py`, PostgreSQL concurrent events | PASS |
| PLAN-037 recorded-source historical replay, not portfolio backtest | `8e4bea1` plus `1137a55`/`1313253`; calendar/outcome/persisted-evaluation tests, PostgreSQL replay | PASS |
| Separate sequential ticket commits and documentation | Eight initial commits above, subsequent integration/fix commits, corresponding platform docs | PASS |
| Full local regression, PostgreSQL migrations and rollback | 1228 tests + 88 subtests at `129696b`; dedicated synthetic DB removed | PASS |
| Supported Python 3.10–3.13 CI | Workflow present; cannot upload branch with current OAuth grant | BLOCKED |
| Final security report | Semantic evidence recovered; finalization previously errored, no sealed post-fix report | BLOCKED |
| Fork PR, review and merge | No remote feature branch or PR; `origin/main` remains `f76c353` | BLOCKED |

Resume on this same worktree/branch. Obtain GitHub `workflow` authorization,
push without removing the CI change, create and attach the fork PR, inspect its
actual matrix results and address failures. Resolve the security finalization
error through the existing scan's supported recovery path. Only then can the
remaining review/merge gate be considered. Do not recreate implemented tickets,
rewrite old sealed evidence, or call this milestone complete.

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
3. Dependency/secret checks and post-fix source review are recorded above.
   Resolve the failed canonical security finalization; preserve the existing
   scan and the sealed old-SHA scan unchanged.
4. Complete acceptance review, triage any findings, rerun gates after fixes,
   obtain cross-version CI evidence, refresh this receipt/tracker and merge only
   with passing in-scope gates.

Local tests use synthetic holdings, policies, sources and model responses.
They do not establish live-provider quality, historical model knowledge,
portfolio performance, private deployment readiness or financial suitability.
