# Observability Baseline

Milestone 1 provides vendor-neutral, local observability. It does not transmit
logs, traces, metrics, portfolio data, or model output to an external service.

## Structured Logs

Platform logs are JSON and include UTC timestamp, level, logger, event message,
and request correlation ID. HTTP completion logs contain only method, registered
route template, status, and duration. Worker transition logs contain job ID,
run ID, coarse status, and attempt.

The formatter recursively redacts keys associated with credentials, sessions,
owners/accounts, holdings, and portfolios. It also removes bearer tokens,
session tokens, common API-key forms, and passwords embedded in URLs. Exception
types may be recorded; raw exception text and stack traces are excluded by the
formatter. Request/response bodies, query strings, cookies, raw symbols,
provider payloads, and LLM output are not logged.

The API accepts a safe `X-Request-ID` containing 8–64 letters, digits, dots,
underscores, or hyphens; otherwise it generates a UUID. The response always
returns the effective ID.

## Metrics

Authenticated owners can read Prometheus text at
`GET /api/v1/observability/metrics`. Metrics cover HTTP count/duration by method,
registered route template and status; durable job transitions by finite status;
and active SSE connections. User IDs, run IDs, job IDs, symbols, query strings,
and arbitrary error codes are never metric labels.

The registry is process-local. A multi-replica deployment must select and
approve a metrics collector/export path separately; these counters must not be
misrepresented as globally aggregated production telemetry.

## Runtime

`tradingagents-api` installs the JSON formatter for platform logs and disables
Uvicorn access logs, which otherwise risk recording raw request targets. Public
deployment still requires alert ownership, retention, sampling, protected
scrape configuration, incident runbooks, and a reviewed telemetry destination.
