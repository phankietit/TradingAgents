# Milestone 2 Market Data Verification

Date: 2026-09-26

This receipt covers the sequential Milestone 2 implementation from PLAN-020
through PLAN-027. It verifies a local private-platform data foundation. It does
not claim a Web UI, production deployment, configured live data vendor,
portfolio simulator, broker connection, order execution, autonomous trading,
or investment performance.

## Candidate Identity

- Repository: `phankietit/TradingAgents`
- Worktree: `/Volumes/Data/Project/TradingAgents-TA-020-instrument-master`
- Branch: `feature/TA-027-data-health-engine`
- Verified implementation commit: `6b7c6a5df08e97f3c9ebb55c767e9fedd84383e6`
- Base commit: `af1ebeb672a5b36c2cc8a0f25fced07846abc61b`
  (`origin/main`, merged Milestone 1)
- Runtime: macOS 26.5.2 arm64, Python 3.14.7, pip 26.2.1
- Dependency state: ignored editable `.venv`; clean core and `platform` installs
  were independently checked in a task-owned managed environment.

The receipt and user-facing documentation are a documentation-only commit after
the implementation commit above. The final branch SHA is recorded by the PR
candidate after this receipt is committed.

## Ticket Evidence

| Ticket | Commit | Observable acceptance evidence | Result |
| --- | --- | --- | --- |
| PLAN-020 instrument master | `f342143` | Stable canonical IDs, immutable normalized aliases, ambiguity/collision failure, deterministic bootstrap scope, filters, authenticated lookup API, Alembic backfill, owner-independent identity, and PostgreSQL parity are covered by `tests/test_instrument_master.py` and `tests/test_platform_api.py`. | `PASS` |
| PLAN-021 normalized time-series API | `a3aeb47` | Sorted unique point-in-time OHLCV, complete adjusted-price basis, deterministic returns/volatility/drawdown, exact benchmark alignment, immutable owner-scoped snapshots, range validation, and authenticated HTTP reads are covered by `tests/test_normalized_time_series.py` and `tests/test_platform_api.py`. | `PASS` |
| PLAN-022 equity/ETF snapshot pipeline | `e9c50f5` | Filed/publication/holdings-date eligibility, future-row exclusion, restatement preservation, equity-versus-fund separation, explicit source states, provenance, immutable persistence, and PostgreSQL round trip are covered by `tests/test_equity_etf_pipeline.py`. | `PASS` |
| PLAN-023 NQ/ES reference pipeline | `ad63e9c` | NQ/ES-only reference identity, CME sessions, observed contract metadata, explicit rollover methods, expected/preserved/unavailable gaps, no price filling, immutable persistence, and PostgreSQL round trip are covered by `tests/test_futures_reference_pipeline.py`. | `PASS` |
| PLAN-024 crypto snapshot pipeline | `88a39e5` | BTC/ETH-only UTC/24x7 identity, distinct venue observations, future exclusion, volume/spread/freshness quality, BTC benchmark behavior, owner isolation, non-whitelist rejection, and PostgreSQL round trip are covered by `tests/test_crypto_snapshot_pipeline.py`. | `PASS` |
| PLAN-025 deterministic stock screener | `2192adb` | Explicit point-in-time inputs, investable US-equity filters, non-OK exclusion, deterministic rank/tie behavior, input-order independence, stable hashes, complete exclusion evidence, owner isolation, and PostgreSQL round trip are covered by `tests/test_stock_screener.py`. | `PASS` |
| PLAN-026 derived factor service | `b154842` | Configured momentum, trend, sample volatility, exact-alignment relative strength/correlation, breadth, insufficient-coverage failure, input-order independence, non-OK rejection, owner isolation, and PostgreSQL round trip are covered by `tests/test_derived_factors.py`. | `PASS` |
| PLAN-027 data-health engine | `6b7c6a5` | Distinct `OK`, `STALE`, `NO_DATA`, `UNAVAILABLE`, `COVERAGE_GAP`, and `INVALID` semantics; future-only/contradictory payload handling; deterministic aggregation; shared worst-state precedence; owner isolation; and PostgreSQL round trip are covered by `tests/test_data_health.py` plus the equity/ETF, futures-reference, and crypto suites. | `PASS` |

The ticket commits are ordered and unsquashed. Each ticket includes a matching
contract document under `docs/platform/`; later commits extend shared contracts
without changing the earlier ticket's market boundary.

## Verification Results

### Baseline Python Gate

| Command | Evidence | Result |
| --- | --- | --- |
| `TZ=UTC .venv/bin/python -m pytest -q` | 1053 passed, 14 skipped, 88 subtests passed, 22 warnings. Skips were optional Bedrock, absent live DeepSeek credentials, and environment-gated PostgreSQL cases executed separately below. | `PASS` |
| `.venv/bin/python -m ruff check .` | No lint findings. | `PASS` |
| `git diff --check` | No whitespace errors. | `PASS` |
| `.venv/bin/python -m pip check` | No broken requirements. | `PASS` |

`TZ=UTC` is explicit because fixed-time OHLCV fixtures are timezone-sensitive
on the Asia/Ho_Chi_Minh host. It does not bypass or skip product behavior. One
earlier full-suite attempt observed Yahoo as unreachable and correctly returned
`UNAVAILABLE`; the final complete rerun passed without changing code or tests.

### Clean Install Gate

A fresh Python 3.14.7 environment in a task-owned `codex-storage` run first
installed `.` and imported `tradingagents` plus `cli.main`. It then installed
`.[platform]` and imported the market-data pipelines, screening,
factor, and data-health services. `pip check` reported no broken requirements.
The managed run was finished and removed through ownership-safe cleanup.
Result: `PASS`.

### PostgreSQL And Migration Gate

A task-owned PostgreSQL 16.14 container ran the twelve environment-gated local
PostgreSQL tests for persistence, owner auth, durable jobs, run events,
instrument master, normalized series, equity/ETF, NQ/ES reference, crypto,
screening, factors, and data health: 12 passed.

An independent migration run then proved:

- Alembic upgraded through `0007_instrument_aliases`.
- `alembic.command.check` reported no new upgrade operations.
- The upgraded schema included `instrument_aliases` and all Milestone 1 tables.
- Downgrade to base removed all application tables; only `alembic_version`
  remained.
- Each exact task-created container was removed after its run.

Result: `PASS` for local PostgreSQL integration, upgrade parity, and migration
rollback. Production backup/restore remains outside this development milestone.

### API And Data-Integrity Gate

- Authenticated instrument list, exact filters, alias resolution, detail, and
  normalized time-series reads are covered by `tests/test_platform_api.py`.
- Future rows, future filings/publications/holdings, insufficient benchmark
  alignment, source outage versus empty data, stale data, unsupported historical
  coverage, symbol ambiguity, immutable artifacts, and owner isolation are
  exercised by the ticket suites. Result: `PASS` for local fixture and database
  evidence.
- No production vendor was added or changed. Live reachability, licensing, and
  current external coverage are therefore `NOT_IN_SCOPE`, not implied by these
  local tests.

### Scope And Safety Audit

- NQ and ES are accepted only as `reference_only` market context; no futures
  sizing, margin, leverage, derivative position, or order path was added.
  Result: `PASS`.
- Platform crypto snapshot scope rejects assets outside BTC and ETH; ETH uses
  BTC as its exact-timestamp benchmark and BTC cannot benchmark itself. Result:
  `PASS`.
- LLM output does not calculate screener inclusion, factor values, quality
  states, quantities, or weights. Screening, factors, and health are
  deterministic and testable. Result: `PASS`.
- No broker, execution, portfolio-weight, leverage, shorting, options, or
  autonomous approval endpoint exists in the changed platform surface. Result:
  `PASS`.
- `.env.example` contains names/placeholders only. No task secret or private
  portfolio artifact was added. Specialized `gitleaks`, `detect-secrets`, and
  `pip-audit` executables were unavailable locally; this scoped inspection is
  not equivalent to those tools.
- The governance checkout at `/Volumes/Data/Project/TradingAgents` remained on
  `chore/governance-bootstrap` at
  `2d17df8da1536c121e4d7395ac5a5dcec9e96d6f`; its pre-existing untracked
  governance files were not changed by product implementation. Result: `PASS`.

## Explicit Limitations

| Gate | Result | Reason |
| --- | --- | --- |
| Web UI and browser E2E | `NOT_IN_SCOPE` | Milestone 2 supplies data contracts/services and two read API surfaces; the modern quant-style Web UI is a later milestone. |
| Live market-data/provider validation | `NOT_IN_SCOPE` | No production vendor, credential, endpoint, licensing contract, or fallback chain was selected. |
| Portfolio simulation/performance | `NOT_IN_SCOPE` | There is still no cash ledger, fills, fees, slippage, turnover, corporate-action accounting, or position carry-forward. |
| Broker sandbox/live execution | `NOT_IN_SCOPE` | Broker connectivity and order execution remain explicitly absent. |
| Production deployment/backup/restore/DR | `NOT_IN_SCOPE` | No production environment or hosting/storage vendor is selected. |
| Complete supported-Python CI matrix | `UNVERIFIED` | Local verification used Python 3.14.7; CI remains authoritative for the configured matrix. |
| Specialized secret/dependency scanning | `UNVERIFIED` | `gitleaks`, `detect-secrets`, and `pip-audit` were not installed locally. |

Milestone 2 is therefore a locally verified private-platform data development
candidate, not a production-ready trading product or performance claim.
