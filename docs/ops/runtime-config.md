# TradingAgents Runtime Configuration Contract

## Supported Development Baseline

- Python: a version supported by `pyproject.toml` and CI; Python 3.12 is the
  recommended local baseline.
- Installation: an isolated virtual environment with `pip install -e ".[dev]"`.
- Runtime config: ignored local `.env` or process environment.
- At least one configured LLM provider and model pair.

## Configuration Precedence

Precedence must remain explicit and tested:

1. Programmatic configuration supplied by the caller.
2. `TRADINGAGENTS_*` environment overrides.
3. Repository defaults.

A future web worker must construct an immutable per-run configuration. It must
not depend on mutable process-global configuration shared between jobs.

## Credential Classes

- Exactly one LLM provider credential is normally required for hosted models.
- `SEC_EDGAR_USER_AGENT` is contact identification, not a secret.
- FRED and Alpha Vantage keys are optional unless the configured vendor path
  requires them.
- Local Ollama/OpenAI-compatible endpoints may not require a key, but endpoint
  ownership and model availability must be verified.

Do not document or persist live values. Refer to `.env.example` for supported
names.

## Runtime Artifacts

The following must remain untracked and owner-private:

- Results and generated reports.
- Market-data cache and immutable snapshots.
- Decision/reflection memory.
- Checkpoint databases.
- Portfolio files and exports.
- Provider/model caches.
- Logs containing run metadata.

Paths should be configurable and must not escape their approved root through a
symbol, run ID, or user-supplied path component.

## Run Manifest

Platform-grade runs should record non-secret metadata:

- Run ID, start/end time, status, branch and commit SHA.
- Python/package version.
- Provider and model IDs.
- Prompt/schema/config versions.
- Selected analysts and debate/risk depth.
- Asset type, canonical symbol, analysis date, and portfolio fingerprint.
- Data vendors, snapshot hashes, warnings, retries, latency, and token usage.
- Explicit limitations and approval state.

## Fail-Closed Behavior

- Missing required credentials: setup/configuration error before graph work.
- Missing optional enrichment: explicit unavailable state.
- Invalid endpoint/model/config: reject before the run.
- No fallback to demo/mock investment data in normal runtime.
- Never claim a run succeeded if the final rating is unreadable or evidence is
  ineligible; use `REVIEW` or a failed state.
