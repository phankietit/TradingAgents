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

Alternatively, the repository-owned helper creates a labelled disposable
PostgreSQL container, overrides any inherited database URL with its own URL,
and removes only that container when the gate exits:

```sh
TA_ALLOW_TEST_DB_RESET=1 bash scripts/verify-postgres-local.sh
```

It requires an existing Docker runtime and cached `postgres:16-alpine` image;
it does not install/start a runtime or accept an existing application database.
On the designated Mac, check `codex-storage status` first and put per-command
`TMPDIR` under the current managed external run. Do not inspect/print the generated
database password or connection URL.

### Focused diagnostics (not full regression)

Both helpers optionally forward an explicit selection to pytest after the same
Ruff/dependency checks. Omission of `--focused` retains the full suite:

```sh
bash scripts/verify-local.sh local --focused tests/test_local_verification_cli.py
TA_ALLOW_TEST_DB_RESET=1 bash scripts/verify-postgres-local.sh --focused \
  tests/test_native_recorder_spawn.py -k native_postgresql --tb=short -x
```

Missing selection or unmarked extra arguments fail before runtime/database
allocation. Focused output is labelled separately; retain the exact selection,
totals, skips, exit status, SHA and dirty state in the receipt. A focused PASS
does not replace the baseline/full regression or release gates. Keep source
unchanged while native checkpoint tests run: their real runtime fingerprint
includes package source and installed dependency versions.

The native PostgreSQL matrix reuses the original spawned graph/portfolio/API
assertions for valid EN/VI/bilingual output, invalid VI and deterministic policy
failures. It still uses synthetic SDK responses with HTTP refused. It proves
local PostgreSQL persistence and authenticated approval mechanics, not live
market/model reachability, investment quality, browser UX or recovery across
every stop/cancel/expiry boundary. Outside an explicitly acknowledged disposable
PostgreSQL environment these cases skip and remain UNVERIFIED.

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
