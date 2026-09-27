# TradingAgents Development Rules

## Modes

Every task must be classified before changes begin.

| Mode | Allowed by default |
| --- | --- |
| Audit | Read-only inspection and report |
| Planning | Plans, estimates, issue drafts; no repository mutation |
| Execution | Changes within one approved issue/scope |
| PR/sync | Rebase, verification, push, PR, upstream synchronization |
| Release | Candidate verification and explicitly approved publication |

A user message such as “no action”, “check first”, or “audit only” selects
Audit mode. Do not reinterpret it as permission to fix findings.

## Scope Discipline

- Prefer the smallest change that satisfies the approved contract.
- Do not add speculative product capability.
- Preserve user changes and unrelated dirty files.
- Do not combine refactoring, dependency upgrades, provider changes, and
  product behavior in one patch unless inseparable and explicitly scoped.
- State assumptions that materially affect behavior or verification.
- When blocked by owner/provider/live-environment state, finish all safe local
  work, mark the exact remainder, and stop.

## Issue Contract

- Title: `[TA-<N>] <type>: <short description>`.
- Labels: one type, one area, and one priority.
- Acceptance criteria must be observable.
- Data/LLM/risk issues must state the relevant as-of, evidence, and failure
  behavior.
- Security or live-execution impact must be explicit, never inferred away.

See `docs/ops/issue-label-taxonomy.md` for the label contract.

Recommended areas:

```text
area:agents
area:data
area:llm
area:portfolio
area:backtest
area:web
area:security
area:infra
area:docs
```

## Branch And Worktree

- Product implementation starts from current `origin/main` in a separate
  worktree.
- Docs/rules-only work may use the root checkout when explicitly scoped.
- Confirm repository root, branch, HEAD, remotes, and dirty state before work.
- Do not delete or reset uncommitted user work.
- Do not force-push `main` or another shared branch.
- Upstream synchronization is its own branch and PR.

## Change Contracts

### Data Changes

Must document:

- Vendor and endpoint class.
- Timestamp semantics and point-in-time behavior.
- Coverage and staleness rules.
- Fallback order and failure state.
- Cache key/version and snapshot impact.
- Tests preventing future information leakage.

### LLM And Prompt Changes

Must document:

- Provider/model capabilities required.
- Tool/structured-output behavior.
- Retry, token, latency, and cost implications.
- Free-text fallback policy.
- Prompt-injection boundary and untrusted inputs.
- Evaluation fixture or regression evidence.

### Portfolio And Risk Changes

Must be deterministic, schema-backed, and tested with invariants. LLM text may
not bypass a failed risk rule. Any risk-limit change requires explicit approval.

### Platform Changes

Web/API/database/queue/auth work must preserve the current Python package API or
document a versioned migration. Long-running graph execution must not be tied to
an HTTP request lifecycle.

## Definition Of Done

A change is complete only when:

1. The requested behavior and acceptance criteria are satisfied.
2. Relevant contracts/docs are updated.
3. Scope-appropriate verification passes or is explicitly marked blocked.
4. Evidence identifies exact branch/SHA/runtime.
5. No untriaged security, data-integrity, or risk-policy failure remains.
6. Current capability and future proposal are not conflated.
7. External/owner gates are reported without fabricating completion.
