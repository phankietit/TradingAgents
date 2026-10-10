#!/usr/bin/env bash
# Local verification only: no hosted CI, dependency install, provider calls or deploy.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
mode="${1:-local}"
if [[ "$mode" != local && "$mode" != --postgres ]]; then
  echo 'Usage: bash scripts/verify-local.sh [local|--postgres] [--focused <pytest arguments...>]' >&2
  exit 2
fi
[[ $# == 0 ]] || shift
focused=0
if [[ $# -gt 0 ]]; then
  if [[ "$1" != --focused || $# -lt 2 ]]; then
    echo 'Focused verification requires --focused followed by pytest arguments.' >&2
    exit 2
  fi
  focused=1
  shift
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
if [[ "$focused" == 1 ]]; then
  echo 'Focused local gate only; not the full regression gate.'
  "$python_bin" -m pytest -q --disable-warnings "$@"
else
  "$python_bin" -m pytest -q --disable-warnings
fi
git diff --check
if [[ "$focused" == 1 ]]; then
  echo 'PASS: focused local commands only. Skips remain UNVERIFIED; no full-regression or release claim.'
else
  echo 'PASS: local commands. Skipped tests remain UNVERIFIED; this is not release approval.'
fi
