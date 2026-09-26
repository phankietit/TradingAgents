# Temporary local-only verification policy

Owner decision, 2026-09-27: do not use hosted CI for now due to budget.
GitHub Actions was disabled for `phankietit/TradingAgents` using repository
Actions permissions (`enabled=false`). No workflow runs are required for merge
during this temporary policy. Do not re-enable Actions without owner approval.
The repository's original workflow file is retained unchanged from the M3 base;
new M3 CI changes are withdrawn. No paid runner or replacement service is added.

The owner subsequently approved manual/local security review as the M3
acceptance gate instead of requiring a sealed plugin report. Retain plugin
failures unchanged and label them accurately; this is a change in evidence
format, not permission to skip security review or unresolved findings.

## Local gate

Use an existing isolated environment with `.[dev,platform]` installed:

```sh
bash scripts/verify-local.sh
```

The script records branch/SHA, dirty state and Python version, then runs lint,
installed dependency consistency, full pytest and whitespace checks. It does not
install packages, create containers, deploy, or upload results. Default mode
removes an inherited `TEST_POSTGRES_URL` to avoid running destructive database
fixtures by accident. Live DeepSeek credentials are withheld in both modes;
the optional live-provider test remains UNVERIFIED, not an implicit pass.

To include PostgreSQL, prepare a **dedicated disposable test database**, set
`TEST_POSTGRES_URL` locally without printing it, and explicitly acknowledge that
the integration fixtures upgrade/downgrade its schema:

```sh
TA_ALLOW_TEST_DB_RESET=1 bash scripts/verify-local.sh --postgres
```

Never use an existing application/owner/production database. Follow machine
storage rules before starting containers, and remove only the task-owned
disposable container after verification. The script does not manage its lifecycle.

## Evidence and remaining gates

- Record exact SHA, runtime, commands, test totals, skips and limitations in the
  milestone receipt. A dirty run must identify its patch, not claim clean-SHA proof.
- Packaging/import changes still need an isolated non-editable installation,
  outside-checkout imports and worker CLI smoke, as documented in the M3 receipt.
- Run dependency and tracked-file secret scans without exposing values; keep
  security source review and any findings explicit.
- One local Python version does not prove the whole supported matrix. Additional
  versions can use `PYTHON_BIN=/absolute/path/to/venv/bin/python`; otherwise mark
  those versions UNVERIFIED. Hosted matrix execution is DEFERRED by owner choice.
- Review the PR diff and local evidence before merge. Do not bypass an actual
  branch-protection rule, or change production/data/risk/human-approval controls.
- This supersedes only the hosted-CI requirement, not implementation acceptance,
  PostgreSQL gates, data-integrity gates, security review or approval requirements.
