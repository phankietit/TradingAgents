# TradingAgents Evidence Contract

Evidence exists so another engineer can reproduce a claim without trusting the
author's narrative.

## Required Fields

Every implementation, QA, release, data, or evaluation handoff should identify:

- Repository and worktree path.
- Branch and full commit SHA.
- Dirty/clean status and relevant diff scope.
- Exact command or procedure.
- Runtime: OS, Python, package/dependency state.
- Provider/model/vendor names without secret values.
- Instrument, asset type, analysis date, and data window.
- Result status and concise output.
- Skipped gates, limitations, and owner/external blockers.
- Artifact paths or immutable identifiers.

## Status Vocabulary

Use exactly one status per gate:

| Status | Meaning |
| --- | --- |
| `PASS` | Current evidence proves the acceptance criterion |
| `FAIL` | A reproducible failure contradicts the criterion |
| `BLOCKED` | External/owner state is required before verification |
| `DEFERRED` | Product owner explicitly moved the gate later |
| `NOT_IN_SCOPE` | The candidate contract excludes the gate |
| `UNVERIFIED` | Evidence was not collected or is insufficient |

Do not convert `BLOCKED` or `UNVERIFIED` into `PASS` to improve a completion
ratio.

## Evidence Classes

Keep these distinct:

- Static/source inspection.
- Unit tests with mocks/fakes.
- Local integration tests.
- Live third-party provider checks.
- Historical snapshot/replay checks.
- Paper portfolio simulation.
- Deployed private platform checks.
- Broker sandbox checks.
- Live broker checks.

Passing a lower class does not prove a higher one.

## Data And Decision Evidence

A reproducible decision/evaluation should retain:

- Run manifest.
- Input snapshot hashes.
- Source timestamps and point-in-time eligibility.
- Prompt and schema version.
- Provider/model/configuration.
- Structured decision and data-quality state.
- Deterministic policy results.
- Human approval/rejection state.

Do not store secret values or raw private portfolio data in public issue/PR
evidence.

## Performance Evidence

Any performance claim must state:

- Universe and selection method.
- Date range and market regimes represented.
- Benchmark.
- Sample size.
- Holding/execution rules.
- Fees, slippage, corporate actions, and missing-data treatment.
- Model/prompt/data versions.
- Whether results are backtest, paper, or live.
- Known reproducibility limits.

One run, one ticker, one model sample, or an unarchived text feed is not enough
for a strategy-performance claim.

## Candidate Readiness

Readiness is determined by hard gates, not percentage complete. One unresolved
P0 data-integrity, privacy, risk, approval, or deployment blocker prevents a
production-ready verdict even if every local unit test passes.
