# Milestone 1 Platform Foundation Verification

Date: 2026-09-24

This receipt covers the sequential Milestone 1 implementation from PLAN-010
through PLAN-018. It verifies a private platform foundation only. It does not
claim that a Web UI, production deployment, live provider integration,
portfolio simulator, broker connection, or order execution exists.

## Candidate Identity

- Repository: `phankietit/TradingAgents`
- Worktree: `/Volumes/Data/Project/TradingAgents-TA-010-run-scoped-config`
- Branch: `feature/TA-018-observability-baseline`
- Verified implementation commit: `3043525af273c91bda8914e5fc805e3d0aa212ff`
- Base commit: `2d17df8da1536c121e4d7395ac5a5dcec9e96d6f`
  (`origin/main`)
- Runtime: macOS 26.5.2 arm64, Python 3.14.7, pip 26.2.1
- Dependency state: isolated ignored `.venv`; clean-install imports were also
  checked in a separate isolated environment.

The receipt itself is a documentation-only commit after the implementation
commit above. The final branch SHA must be recorded from `git rev-parse HEAD`
when handing off the candidate.

## Ticket Evidence

| Ticket | Commit | Observable acceptance evidence | Result |
| --- | --- | --- | --- |
| PLAN-010 run-scoped configuration | `50e1abe` | Thread and async task isolation, nested restoration after error, immutable graph-owned copies, and graph activation are covered by `tests/test_run_scoped_config.py`. | `PASS` |
| PLAN-011 versioned domain schemas | `691662b` | Strict immutable `1.0` contracts, exported JSON schemas, point-in-time validation, reference-only futures, UTC crypto, long-only portfolios, deterministic limits, and mandatory human approval are covered by `tests/test_platform_contracts.py`. | `PASS` |
| PLAN-012 PostgreSQL persistence | `b4b649f` | Explicit database URL, packaged migrations, JSONB on PostgreSQL, owner-scoped private records, immutable/idempotent records, lifecycle transitions, rollback, and provenance round trips are covered by `tests/test_platform_persistence.py`. | `PASS` |
| PLAN-013 immutable artifact/snapshot store | `abf7b5c` | SHA-256 addressing, atomic concurrent writes, immutable versions, canonical JSON, expected-hash validation, owner-scoped manifests, tamper detection, and symlink/path escape rejection are covered by `tests/test_artifact_store.py`. | `PASS` |
| PLAN-014 durable job orchestration | `4238ebd` | Owner-scoped idempotency, PostgreSQL `SKIP LOCKED`, bounded leases, heartbeat, exponential retry, attempt exhaustion, cooperative cancellation, stale recovery, and sanitized failures are covered by `tests/test_durable_jobs.py`. | `PASS` |
| PLAN-015 owner authentication | `e3b11ea` | Database-enforced single owner, normalized identity, scrypt verifier, generic login failure, hashed opaque sessions, expiry/revocation, password rotation, disable behavior, and concurrent bootstrap are covered by `tests/test_owner_auth.py`. | `PASS` |
| PLAN-016 FastAPI contract | `426e91a` | Authenticated `/api/v1` resources, server-derived owner identity, session-bound CSRF, exact-origin checks, secure defaults, validation, idempotent run creation, cancellation, private artifact download, security headers, and OpenAPI auth are covered by `tests/test_platform_api.py`. | `PASS` |
| PLAN-017 SSE run-event streaming | `40af2ec` | Append-only per-run ordering, concurrent PostgreSQL sequence allocation, owner isolation, `Last-Event-ID` replay, keepalive/terminal behavior, and worker lifecycle events are covered by `tests/test_run_events.py`, `tests/test_platform_api.py`, and `tests/test_durable_jobs.py`. | `PASS` |
| PLAN-018 observability baseline | `3043525` | Recursive log redaction, request correlation, route-template-only HTTP logs, bounded metric labels, authenticated Prometheus output, job counters, and SSE connection gauges are covered by `tests/test_observability.py`, `tests/test_platform_api.py`, and `tests/test_durable_jobs.py`. | `PASS` |

Each ticket was implemented and committed in the order above. Later commits
extend the earlier contract without squashing its evidence boundary.

## Verification Results

### Baseline Python Gate

| Command | Evidence | Result |
| --- | --- | --- |
| `TZ=UTC .venv/bin/python -m pytest -q` | 1009 passed, 6 skipped, 88 subtests passed, 22 warnings. The skipped cases were optional Bedrock, an absent live DeepSeek credential, and environment-gated PostgreSQL cases that were executed separately below. | `PASS` |
| `.venv/bin/python -m ruff check .` | No lint findings. | `PASS` |
| `git diff --check` | No whitespace errors. | `PASS` |
| `.venv/bin/python -m pip check` | No broken requirements. | `PASS` |

`TZ=UTC` is explicit because fixed-time OHLCV tests are timezone-sensitive on
the local Asia/Ho_Chi_Minh host. It does not bypass or skip product behavior.

### Clean Install Gate

An isolated environment under `.venv/clean-install` installed
`.[platform]`. Imports for the package, CLI, platform API, authentication,
events, and observability surfaces succeeded. The developer editable
environment was not used as clean-install evidence. Result: `PASS`.

### PostgreSQL And Migration Gate

A task-owned `postgres:16-alpine` container reported PostgreSQL `16.14`.
Against that live database:

- `TEST_POSTGRES_URL=... TZ=UTC .venv/bin/python -m pytest -q`
  over platform persistence, durable jobs, owner auth, run events, and API
  tests produced 39 passed.
- `upgrade_database(url)` applied revisions `0001` through `0006`.
- `alembic.command.check(migration_config(url))` reported no new upgrade
  operations.
- The migrated tables were `analysis_jobs`, `analysis_runs`, `artifacts`,
  `decisions`, `instruments`, `owner_accounts`, `owner_sessions`, `policies`,
  `portfolio_snapshots`, `run_events`, `snapshots`, and `alembic_version`.
- `downgrade_database(url)` removed all application tables; only Alembic's
  version table remained.
- The exact task-created container was removed and absence was verified.

Result: `PASS` for local PostgreSQL integration and migration rollback.
Production backup/restore is `NOT_IN_SCOPE` because no production database or
deployment is selected by this milestone.

### Local API Runtime Smoke

The packaged API entrypoint was launched against migrated local SQLite and an
explicit local artifact root on `127.0.0.1`. Readiness, login, authenticated
metrics, bounded route labels, zero inactive SSE connections, JSON structured
logs, request correlation, and the absence of request bodies, cookies, and
query strings in logs were verified. The process stopped normally and the
exact temporary directory was removed. Result: `PASS`.

### Scope And Safety Audit

- The API exposes analysis, job, decision, artifact, event, auth, health, and
  observability contracts; it has no broker, order, leverage, shorting,
  derivative, or autonomous execution endpoint. Result: `PASS`.
- LLM output remains analysis evidence. Deterministic policy fields and human
  approval requirements remain explicit in the versioned contracts. Result:
  `PASS`.
- The original governance checkout at `/Volumes/Data/Project/TradingAgents`
  remained on `chore/governance-bootstrap` at
  `2d17df8da1536c121e4d7395ac5a5dcec9e96d6f`; its pre-existing untracked
  governance files were not changed by implementation work. Result: `PASS`.
- The implementation worktree contained no uncommitted product changes before
  this receipt was added. Result: `PASS`.

## Explicit Limitations

| Gate | Result | Reason |
| --- | --- | --- |
| Browser E2E for analysis/review/approval | `NOT_IN_SCOPE` | Milestone 1 provides API and worker foundations, not the Web UI. Browser E2E becomes required with the UI milestone. |
| Live market-data or LLM provider validation | `NOT_IN_SCOPE` | No provider contract or provider behavior changed, and no live analysis claim is made. |
| Portfolio simulation or performance claims | `NOT_IN_SCOPE` | This milestone does not add cash, fills, fees, slippage, turnover, or position carry-forward. |
| Broker sandbox or live execution | `NOT_IN_SCOPE` | Broker connectivity and order execution are explicitly absent. |
| Production hosting, TLS, public exposure, object storage, telemetry export, and disaster recovery | `NOT_IN_SCOPE` | No production vendor or environment is selected. |
| Complete supported-Python CI matrix | `UNVERIFIED` | Local verification used Python 3.14.7; CI remains authoritative across the configured matrix. |
| `gitleaks`, `detect-secrets`, and `pip-audit` | `UNVERIFIED` | These specialized tools were unavailable locally. Scoped secret-pattern inspection and `pip check` passed, but those are not equivalent evidence. |

Milestone 1 is therefore a locally verified development foundation, not a
production-readiness or investment-performance claim.
