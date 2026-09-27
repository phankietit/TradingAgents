# TradingAgents Agent Routing Map

Entry point: `AGENTS.md`.

## Session Start

1. Read `AGENTS.md`.
2. Read this file.
3. Confirm repository root, branch, HEAD, remotes, and dirty state.
4. Classify the task as audit, planning, execution, PR/sync, or release.
5. Load only the matching rules below.
6. If `.codegraph/` exists, use CodeGraph before broad search or file reading.

## Intent Routing

| User intent | Mode | Required rules/docs |
| --- | --- | --- |
| Audit, review, “no action” | Audit | Relevant contract only; do not edit |
| Plan, estimate, create issue | Planning | `ticket-lifecycle`, Product Contract |
| Implement or fix | Execution | `sdlc`, `agent-coordination`, relevant domain rule |
| Data, market vendor, cache | Execution/data | `data-integrity`, Data Integrity Contract |
| Model, prompt, provider | Execution/LLM | `llm-provider`, Security Contract |
| Backtest, portfolio, risk | Execution/risk | `portfolio-risk`, Product Contract |
| Web, API, database, auth | Execution/platform | `security`, `sdlc` |
| PR, push, upstream sync | PR/sync | `agent-coordination`, `release-and-deploy` |
| Publish/deploy/paper/live | Release | `release-and-deploy`, Release Readiness |

## Always-Applicable Contracts

- `docs/governance/PRODUCT_CONTRACT.md`
- `docs/governance/DEVELOPMENT_RULES.md`
- `docs/ops/data-integrity.md`
- `docs/ops/evidence-contract.md`
- `docs/ops/verify-gates.md`

## Domain Rules

- `.cursor/rules/sdlc.mdc`
- `.cursor/rules/ticket-lifecycle.mdc`
- `.cursor/rules/agent-coordination.mdc`
- `.cursor/rules/data-integrity.mdc`
- `.cursor/rules/llm-provider.mdc`
- `.cursor/rules/portfolio-risk.mdc`
- `.cursor/rules/security.mdc`
- `.cursor/rules/release-and-deploy.mdc`

## Conflict Resolution

Higher-priority system/user instructions win. Within the repository, apply:

1. `AGENTS.md` hard stops and product guardrails.
2. Product, data, security, and release contracts.
3. Intent-specific `.cursor/rules`.
4. Existing implementation conventions.

If two repository rules conflict, stop and report both paths and clauses rather
than choosing the weaker guardrail.
