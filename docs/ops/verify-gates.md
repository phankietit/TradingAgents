# TradingAgents Verification Gates

Run the smallest gate set that fully covers the change. Commands must be run
from the repository root in a supported Python environment.

## Documentation And Rules

Required for docs/rules/templates-only changes:

```bash
git diff --check
ruby -e 'require "yaml"; ARGV.each { |f| YAML.load_file(f) }' .github/ISSUE_TEMPLATE/*.yml
```

Also verify that repository-relative paths referenced by `AGENTS.md`, Markdown,
and `.cursor/rules` resolve. A repository-owned link checker may be added later
as a separately scoped tooling change.

## Baseline Python Gate

Required for Python behavior changes:

```bash
python -m ruff check .
python -m pytest -q
git diff --check
```

CI remains authoritative across the complete supported Python matrix. A local
pass on one version is not proof for every CI version.

## Clean Install Gate

Required for packaging, dependency, CLI entrypoint, optional-extra, or import
surface changes:

```bash
python -m pip install .
python -c "import tradingagents, cli.main; print('clean-install import OK')"
```

Use a fresh isolated environment. Do not treat an editable developer
environment as clean-install proof.

## Data And Vendor Gate

In addition to the baseline gate, verify applicable cases:

- Analysis-date boundary and future-row exclusion.
- Filing/publication-date eligibility.
- No-data versus outage/rate-limit classification.
- Stale OHLCV behavior.
- Symbol normalization and safe path components.
- Explicit fallback chain and vendor attribution.
- Historical coverage gaps for news/social/live-only sources.
- Cache freshness and immutable snapshot behavior.

Live-provider checks must be separately labeled and may not expose credentials.
Mocked unit tests do not prove a provider is currently reachable.

## Agent, Prompt, And LLM Gate

Verify:

- Prompt integrity and correct instrument/date context.
- Tool allowlist and injected-state fields.
- Structured-output schema and rendering.
- Invalid structured output ends in `REVIEW` for decision-critical paths.
- Provider capability/model validation.
- Retry/token/temperature/reasoning configuration.
- No unsupported tool call or untrusted-data instruction escalation.

Provider-specific live checks require explicit local credentials and must be
reported separately from unit tests.

## Portfolio, Risk, And Backtest Gate

Verify deterministic invariants:

- Position, cash, currency, and portfolio identity.
- Target and maximum weight constraints.
- Concentration, turnover, loss, and exposure limits.
- A failed policy cannot be overridden by model prose.
- Fees, slippage, fills, corporate actions, and carry-forward if a portfolio
  simulator exists.
- No look-ahead across decisions, outcomes, reflections, or data snapshots.
- Benchmark and asset-specific calendar correctness.

The current independent-cell backtest remains outside portfolio-performance
claims until the missing execution/accounting model is implemented and tested.

## Platform Gate

Future web/API/worker/database work must add:

- API schema and authorization tests.
- Database migration and rollback/restore evidence.
- Owner isolation for private portfolio data.
- Durable job retry, cancellation, resume, and idempotency tests.
- Browser E2E for analysis, decision review, and approval.
- Log/analytics redaction checks.

## Container And Deployment Gate

For container/release changes:

- Build from a clean checkout.
- Run non-root import/CLI smoke.
- Verify no secret or local runtime artifact enters the image.
- Record image digest, source SHA, runtime config names, and health result.
- Scan dependencies/image when tooling is available.

## Evidence Result

Each gate ends in exactly one state:

- `PASS`: current evidence proves it.
- `FAIL`: a reproducible product/regression failure exists.
- `BLOCKED`: required external state prevents verification.
- `DEFERRED`: explicitly approved for later work.
- `NOT_IN_SCOPE`: contract shows the gate does not apply.
- `UNVERIFIED`: not run or evidence is insufficient.
