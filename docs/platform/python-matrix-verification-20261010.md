# Local Python matrix verification — 2026-10-10

Release class: private-platform candidate evidence, not release approval.
CI remains disabled. These are macOS arm64 local results, not Ubuntu/hosted-CI,
cross-platform, live-provider or production evidence.

## Exact full-regression receipts

| Python | Frozen clean source | Session / terminal | Result | Pytest duration |
| --- | --- | --- | --- | --- |
| 3.10.22 | `c0268c70f6c67ea79ed6c7c848e54bbda94a7827` | 65550 / 0 | 3306 tests +88 subtests PASS;2 skips UNVERIFIED;502 warnings | 1762.85s |
| 3.11.17 | `6b4932084140c568eb01543b746cb8d62f2f8f60` | 59766 / 0 | 3306 tests +88 subtests PASS;2 skips UNVERIFIED;502 warnings | 1164.80s |
| 3.12.14 | `796c4178c3c710fba32eb20651c5ace7d46e71a7` | 41168 / 0 | 3306 tests +88 subtests PASS;2 skips UNVERIFIED;502 warnings | 2068.46s |
| 3.13.16 | `6b4932084140c568eb01543b746cb8d62f2f8f60` | 34183 / 0 | 3306 tests +88 subtests PASS;2 skips UNVERIFIED;502 warnings | 1220.84s |

Every row used the original default/full `scripts/verify-postgres-local.sh`,
including Ruff, pip check, full pytest and git diff check. No focused selection,
timeout increase, skipped role, weakened assertion or retry was introduced.
The two optional skips are missing `langchain_aws` and the separately gated live
DeepSeek key/test; no provider or real key was added to turn skips green.

At clean6b49320, source comparisons from both c0268c7 and796c417 over
`tradingagents tests scripts pyproject.toml uv.lock` PASS. They establish unchanged
scoped source, not new executions of the older rows. Additional3.14 and web
receipts remain separately pinned in [HANDOFF](../../HANDOFF.md).

## Fresh 3.11 and 3.13 installation

Branch: `fix/TA-R01-research-quality`, primary managed worktree
`/Volumes/Data/codex/worktrees/ta-030-analysis-risk/TradingAgents`.
Official [Astral20261003 release](https://github.com/astral-sh/python-build-standalone/releases/tag/20261003)
assets, GitHub API SHA256 verified before bounded `tarfile` data-filter extraction:

| Asset | Bytes | SHA256 |
| --- | --- | --- |
| `cpython-3.11.17+20261003-aarch64-apple-darwin-install_only.tar.gz` | 27099994 | `3663b71c18364eccfbad74c4f21f9f6149e40b07329cd776287410cc1da5d612` |
| `cpython-3.13.16+20261003-aarch64-apple-darwin-install_only.tar.gz` | 25365830 | `d8975d7df4f08f7b1c7aafcdfacbddcec3d366415f2c1a72b2466b6850815933` |

Both runtimes/venvs/caches/temp files stay under the existing managed external
run `20261007T052328Z-89163`, respective QA directories
`current-python311-31BDVV` and `current-python313-PwM7Ov`. No system Python,
Homebrew, owner environment or local secret file was changed/copied.

Exact6b49320 `git archive --format=tar.gz --prefix=source/` installed noneditably
with `venv/bin/python -m pip install --index-url https://pypi.org/simple 'source.tar.gz[dev,platform]'`.
Environment cleared with explicit PATH, PIP_CONFIG_FILE=/dev/null and managed
external PIP_CACHE_DIR/TMPDIR. Sessions42244 and31811 terminal0 PASS, pip check
PASS. Both reported wheel538832 bytes, SHA256
`79e777781b732da3f1bd21fe2c6fefd5e3c5a128b1cf0b56dffc628fdc63ee4b`.

Outside-checkout session72863 terminal0 PASS for both runtimes: isolated `-I`
imports of tradingagents/cli.main originate inside the venv; distribution is
noneditable and includes migration env.py; installed API/worker/CLI help PASS.
Help commands did not start an API or worker loop. Fresh resolution retained
pandas3.0.6, SQLAlchemy2.1.4, FastAPI0.143.0, LangGraph1.2.14 and pytest9.1.1;
NumPy2.4.6 on3.11 and2.5.3 on3.13. No dependency downgrade/pin was used to pass.

## Execution and cleanup boundary

External `run-matrix-gate.py` asserted clean6b49320, constructed a fresh
credential-cleared environment and ran from the primary checkout:

```bash
PYTHON_BIN=<QA-root>/venv/bin/python TA_ALLOW_TEST_DB_RESET=1 bash scripts/verify-postgres-local.sh
```

It additionally set managed TMPDIR/cache/results/memory-log paths and synthetic
SEC user agent; real provider credentials were not inherited. Each QA root
retains its own `full-gate.redacted.log`. Generated test DB URLs were redacted.
The actual full tests used the source checkout with fresh installed dependencies,
NOT the entire installed-wheel test suite. Native SDK responses remain fixtures.

Sequential execution:3.11 terminal and owned cleanup confirmed before3.13
started; source stayed fixed throughout both full runs. Original helper removed
only its labelled disposable PostgreSQL16 container. Independently verified:
3.11 helper34001/34005/34026, pytest34048/tracker34152 absent and no container
matching owned suffix `-34005`;3.13 helper40351/40355/40370,
pytest40383/tracker40479 absent and no container matching suffix `-40355`.
No unrelated runtime was stopped.

## Still incomplete

This closes the missing3.11/3.13 local matrix entries, not R13 or the full goal.
Historical live financial/bilingual FAIL and general semantic, recovery, final
report/UX, fresh-target restore/session-fencing gates remain unresolved.
NQ=F remains owner-BLOCKED. The two approved fresh BTC/AAPL paid executions remain
unsubmitted; separate real-workspace API/worker restart approval is pending.
No model request, owner-data mutation, risk/provider change, broker action,
public deployment or release approval occurred. Full R01–R14 remains ACTIVE.
