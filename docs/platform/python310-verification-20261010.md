# Python 3.10 local verification — 2026-10-10

Release class: private-platform candidate evidence, not release approval.
Source: clean `fix/TA-R01-research-quality`, fixed
`c0268c70f6c67ea79ed6c7c848e54bbda94a7827`. Source remained frozen until the full
gate and task-owned cleanup reached terminal. This receipt is a later docs-only
change, not part of the tested SHA. No CI was enabled or executed.

## Runtime and fresh installation

Python 3.10.22, macOS arm64, from the official
[Astral standalone20261003 release](https://github.com/astral-sh/python-build-standalone/releases/tag/20261003),
asset `cpython-3.10.22+20261003-aarch64-apple-darwin-install_only.tar.gz`.
GitHub API asset digest checked before bounded data-filter extraction:
`bb4a37d6f96251e6b384d6d0a2510fd9f54c7aabc6c9b21718b00eb3f155cd25`.
Runtime and venv live under the existing managed external build run, not a
system/Homebrew replacement or internal default cache.

QA root:
`/Volumes/Data/codex-builds/TradingAgents/fix-TA-R01-research-quality/20261007T052328Z-89163/current-python310-lSY98j`.
This directory contains only source/runtime/QA material, not an owner investment
database or populated `.env`. Git archive from exact c0268c7 was installed using
`venv/bin/python -m pip install --index-url https://pypi.org/simple 'source.tar.gz[dev,platform]'`
with `env -i`, explicit noncredential PATH, PIP_CONFIG_FILE=/dev/null and managed
external PIP_CACHE_DIR/TMPDIR. Session87023 terminal0 PASS. Generated wheel:
538832 bytes, SHA256
`3c62621317e737af69823f18af1065546ca90fe9f3f52190acf4126bd714cc4e`.

Outside-checkout, isolated `-I` import-origin/noneditable-distribution/migration
resource assertions, pip check and installed API/worker/CLI help all PASS,
session72078 terminal0. No server or worker loop started by these help commands.
Representative fresh dependencies: pandas2.3.3, LangGraph1.2.14,
langchain-core1.6.9, Pydantic2.14.0, SQLAlchemy2.0.54, FastAPI0.143.0,
pytest9.1.1/Ruff0.17.0. Owner's existing environment was not modified.

## Full source-checkout gate

The QA root retains `run-full-gate.py` and `full-gate.redacted.log`. The wrapper
asserts the fixed clean source, clears inherited credentials, points Python and
caches/temp/results into the managed external run, then executes original
`TA_ALLOW_TEST_DB_RESET=1 bash scripts/verify-postgres-local.sh` from the primary
checkout. Its PYTHON_BIN is the fresh310 venv above; no focused test selection,
timeout increase, source edit, test reduction or rerun.

Session65550 terminal0:

- Ruff, pip dependency check, full pytest and whitespace gate: PASS.
- 3306 tests and88 subtests PASS;2 optional skips UNVERIFIED;502 warnings.
- Pytest duration1762.85s (29m22s), not an estimate of product analysis latency.
- Missing optional `langchain_aws`; live DeepSeek test skipped with no real key.
  No optional vendor installation or paid request was made to erase these skips.
- Original helper created one labelled disposable PostgreSQL16 instance using
  cached postgres:16-alpine; generated URLs were redacted from retained output.
- Only task-owned `ta-research-qa-1791618692-14425` removed by original helper;
  container absence and helper14421/14425/14438, pytest14457 and tracker14528
  absence independently checked after terminal. No unrelated runtime stopped.

This is full local source-checkout regression using a fresh installed dependency
environment, not a full installed-wheel test run or live market/model audit.
Native graph fixtures and PostgreSQL persistence retain their synthetic-response
boundary. No owner storage/history mutation, API/worker restart, AI consumption,
provider/model/risk change, broker action or public deployment occurred.

## Remaining requirements

Later2026-10-10: the [matrix receipt](python-matrix-verification-20261010.md)
adds full local3.11/3.13 at6b49320. The following paragraph records the earlier
minimum-version checkpoint, not the latest matrix state.

The original inactive workflow records Python3.10–3.13. Current local full
receipts cover3.10 and3.12;3.11/3.13 remain UNVERIFIED. Additional3.14 evidence
does not silently replace a required version. Hosted CI remains owner-disabled.

Financial/VI live FAIL, general semantic/operational/UX UNVERIFIED and NQ owner-
BLOCKED receipts remain unchanged. Approved one BTC plus one AAPL paid execution
still await separate owner-workspace runtime restart approval; no new paid runs
are authorized by this gate. Full R01–R14 goal remains ACTIVE and incomplete.
