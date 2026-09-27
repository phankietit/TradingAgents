# TradingAgents Issue Label Taxonomy

Each implementation issue should have exactly one label from each required
group. Labels must exist in GitHub before templates can apply them reliably.

## Type — Required

- `type:feature`
- `type:bug`
- `type:refactor`
- `type:test`
- `type:docs`
- `type:chore`
- `type:security`

## Area — Required

- `area:agents`
- `area:data`
- `area:llm`
- `area:portfolio`
- `area:backtest`
- `area:cli`
- `area:web`
- `area:security`
- `area:infra`
- `area:docs`

## Priority — Required

- `priority:P0`: release/security/data-integrity/risk hard stop.
- `priority:P1`: required for the current approved milestone.
- `priority:P2`: important follow-up with a safe workaround.
- `priority:P3`: optional improvement or future exploration.

## Status — Optional When Project Status Is Unavailable

- `status:planned`
- `status:in-progress`
- `status:blocked`
- `status:ready-for-pr`
- `status:deferred`

Prefer a GitHub Project status field over duplicate status labels when a project
board is configured.

## Evidence — Optional

- `evidence:local`
- `evidence:live-provider`
- `evidence:paper`
- `evidence:deployed`
- `evidence:unverified`

Evidence labels summarize class only. The issue or PR must still record exact
commands, SHA, runtime, result status, and limitations.
