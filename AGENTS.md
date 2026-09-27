# TradingAgents — Agent Instructions

> Read this file before every task, then read `docs/ops/agent-map.md` to load
> only the rules relevant to the user's intent.

## Repository Identity

- Product today: a Python research framework and interactive CLI for
  multi-agent market analysis.
- Intended direction: a private, human-approved portfolio decision-support
  platform.
- GitHub fork: `phankietit/TradingAgents` (`origin`).
- Upstream: `TauricResearch/TradingAgents` (`upstream`).
- Issue prefix: `TA`.
- Current integration and release line: `main`.

Do not describe proposed web, portfolio-simulation, broker, or execution
features as existing functionality. The current runtime is the Python package,
Typer/Rich CLI, LangGraph workflow, Markdown reports, decision log, and
independent-cell research backtest documented in the repository.

## Product Sources Of Truth

- Current user-facing behavior: `README.md`.
- Package/runtime contract: `pyproject.toml` and `tradingagents/default_config.py`.
- Release history: `CHANGELOG.md`.
- Product boundary: `docs/governance/PRODUCT_CONTRACT.md`.
- Development lifecycle: `docs/governance/DEVELOPMENT_RULES.md`.
- Verification: `docs/ops/verify-gates.md`.
- Data correctness: `docs/ops/data-integrity.md`.
- Security: `docs/ops/security-development.md`.

When behavior changes, update the matching source-of-truth document in the same
change. Documentation must distinguish current capability from proposed work.

## Non-Negotiable Product Guardrails

- TradingAgents is decision support, not a promise of returns or financial
  advice.
- LLMs may produce analysis, thesis, rating, risks, and evidence summaries.
- LLM output must not directly determine executable quantity, target weight,
  risk-limit exceptions, or broker actions.
- Portfolio math and policy checks must be deterministic and testable.
- Every future order proposal must require explicit human approval.
- Live trading, broker credentials, leverage, shorting, and derivatives are out
  of scope unless the user explicitly approves a separately governed project.
- Never turn missing, stale, future-leaking, or failed vendor data into an
  apparently valid investment conclusion.
- Historical runs must remain point-in-time safe. If a source has no historical
  vintage, withhold it or mark the result unavailable rather than use current
  data.
- Do not call the current `backtest.py` a portfolio simulator. It evaluates
  independent ticker/date decisions and has no cash ledger, fills, fees,
  slippage, turnover, or position carry-forward.

## Supported Product Scope

Default planning scope:

- Liquid US large-cap equities.
- Broad and sector ETFs as investable index proxies.
- Deterministically screened candidate equities with sufficient liquidity and
  data coverage.
- A separately capped set of large-cap crypto assets, initially BTC and ETH.
- Weekly or medium-term decision support, not intraday/HFT.

Microcaps, penny stocks, options, futures, forex, leveraged products, shorting,
and autonomous execution require a new product decision and dedicated data,
risk, and verification contracts.

## Required Intent Routing

| Intent | Read first |
| --- | --- |
| Any task | `docs/ops/agent-map.md` |
| Audit/report only | Relevant contract only; do not edit |
| Plan or estimate | `.cursor/rules/ticket-lifecycle.mdc`, `docs/governance/PRODUCT_CONTRACT.md` |
| Implement issue | `.cursor/rules/sdlc.mdc`, `.cursor/rules/agent-coordination.mdc` |
| Data/vendor change | `.cursor/rules/data-integrity.mdc`, `docs/ops/data-integrity.md` |
| LLM/provider/prompt change | `.cursor/rules/llm-provider.mdc` |
| Portfolio/risk/backtest | `.cursor/rules/portfolio-risk.mdc` |
| Security/secrets/web/API | `.cursor/rules/security.mdc`, `docs/ops/security-development.md` |
| PR, upstream sync, release | `.cursor/rules/release-and-deploy.mdc`, `docs/ops/release-readiness.md` |

## Branch, Worktree, Commit, And PR

```text
Feature : feature/TA-<issue>-<slug>
Fix     : fix/TA-<issue>-<slug>
Docs    : docs/TA-<issue>-<slug>
Chore   : chore/<slug>
Commit  : <type>(<scope>): <description>
Types   : feat | fix | refactor | test | docs | chore
PR base : main
```

- Do not implement product work directly on `main`.
- Use a separate worktree from current `origin/main` for product code.
- Docs/rules-only work may occur in the root checkout when the user explicitly
  scopes the task that way.
- Never mix an upstream synchronization with a product feature or remediation.
- Synchronize upstream through a dedicated `chore/sync-upstream-YYYYMMDD`
  branch, document conflicts, and run the full regression gate.
- Do not force-push shared branches. A rebased personal feature branch may use
  `--force-with-lease` only when no other owner is using it.

## Verification And Evidence

- Run the scope-appropriate gates in `docs/ops/verify-gates.md`.
- Record exact branch, commit SHA, commands, runtime, and limitations.
- Use only: `PASS`, `FAIL`, `BLOCKED`, `DEFERRED`, `NOT_IN_SCOPE`, or
  `UNVERIFIED`.
- Local/static/mocked evidence must not be promoted to live-provider,
  historical-data, paper-trading, deployment, or broker evidence.
- A skipped gate remains `UNVERIFIED` or `BLOCKED`; it is never an implicit pass.
- Do not claim completion merely because unit tests pass when owner/external
  gates remain.

## Runtime And Secrets

- Keep credentials in ignored local environment files or a secret manager.
- Never print, commit, copy into reports, or persist provider keys, broker
  tokens, account identifiers, or private portfolio details in logs.
- Check only whether a secret is present unless the user explicitly requests a
  narrowly scoped diagnostic.
- Treat `.env.example` as names/documentation only; it must contain no live
  value.
- Runtime directories, caches, reports, decision logs, and model artifacts must
  stay untracked.
- On the designated macOS development machine, follow the machine-level
  storage and container rules supplied by the environment.

## Hard Stops

Stop and request explicit user direction before:

- Sending any paper or live broker order.
- Adding broker connectivity or storing broker credentials.
- Enabling leverage, margin, shorting, options, futures, or other derivatives.
- Changing portfolio risk limits or bypassing a policy failure.
- Adding or replacing a production LLM, market-data, auth, analytics, database,
  payment, or hosting provider.
- Changing production endpoints, credentials, public network exposure, or
  deployment environments.
- Deleting or rewriting portfolio history, decision evidence, checkpoints,
  snapshots, or user data.
- Backfilling or mutating historical data in a way that changes prior results.
- Weakening point-in-time, provenance, privacy, schema, or human-approval gates.
- Publishing performance claims or calling a candidate production-ready without
  current evidence from the exact candidate SHA and environment.

## CodeGraph

<!-- CODEGRAPH_START -->
When a `.codegraph/` directory exists at the repository root, use CodeGraph
before grep/find or broad file reading to locate and understand code. If it does
not exist, skip CodeGraph; indexing is the user's decision.
<!-- CODEGRAPH_END -->
