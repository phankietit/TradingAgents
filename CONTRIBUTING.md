# Contributing To This TradingAgents Fork

This fork preserves the upstream research framework while developing stricter
data, risk, and human-approval boundaries for a private decision platform.

## Before Contributing

Read:

1. `AGENTS.md`.
2. `docs/governance/PRODUCT_CONTRACT.md`.
3. `docs/governance/DEVELOPMENT_RULES.md`.
4. The domain contract relevant to the change.

## Workflow

1. Open or select a scoped `TA` issue.
2. Start a feature/fix branch from current `origin/main`, preferably in a
   separate worktree.
3. Make the smallest contract-complete change.
4. Update tests and documentation with behavior.
5. Run the scope-appropriate gates in `docs/ops/verify-gates.md`.
6. Open a PR to `main` using the repository template.

Use Conventional Commit style:

```text
feat(scope): description
fix(scope): description
test(scope): description
docs(scope): description
refactor(scope): description
chore(scope): description
```

## Upstream Synchronization

Do not mix upstream changes with product work. Use a dedicated
`chore/sync-upstream-YYYYMMDD` branch and record upstream/resulting SHAs,
conflicts, resolutions, and full regression evidence.

## Financial And Data Safety

- Do not add guaranteed-return or unattended-trading claims.
- Preserve point-in-time and source provenance.
- Keep LLM analysis separate from deterministic portfolio/risk policy.
- Never include credentials or private portfolio data in issues, commits, test
  fixtures, logs, screenshots, or PRs.
- Live broker execution is out of scope without a separately approved contract.

## Reporting Results

Use the evidence statuses defined in `docs/ops/evidence-contract.md`. State
skipped or blocked gates explicitly; do not report them as passing.
