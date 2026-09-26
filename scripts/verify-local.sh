#!/usr/bin/env bash
# Local verification only: no hosted CI, dependency install, provider calls or deploy.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
mode="${1:-local}"
if [[ $# -gt 1 || ( "$mode" != local && "$mode" != --postgres ) ]]; then
  echo 'Usage: bash scripts/verify-local.sh [--postgres]' >&2
  exit 2
fi
python_bin="${PYTHON_BIN:-.venv/bin/python}"
if [[ "$mode" == --postgres ]]; then
  if [[ -z "${TEST_POSTGRES_URL:-}" || "${TA_ALLOW_TEST_DB_RESET:-}" != 1 ]]; then
    echo 'BLOCKED: --postgres requires a disposable TEST_POSTGRES_URL and TA_ALLOW_TEST_DB_RESET=1.' >&2
    echo 'Integration tests upgrade/downgrade schema. Never use a user or production database.' >&2
    exit 2
  fi
else
  # Do not accidentally run destructive integration fixtures from inherited env.
  unset TEST_POSTGRES_URL
fi
# Live provider verification is a separate explicitly authorized gate.
unset DEEPSEEK_API_KEY
echo "Branch: $(git branch --show-current)"
echo "SHA: $(git rev-parse HEAD)"
git status --short
"$python_bin" --version
"$python_bin" -m ruff check .
"$python_bin" -m pip check
"$python_bin" -m pytest -q --disable-warnings
git diff --check
echo 'PASS: local commands. Skipped tests remain UNVERIFIED; this is not release approval.'
