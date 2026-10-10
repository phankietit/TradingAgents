# TradingAgents Security Development Contract

This contract applies to provider credentials, portfolio/account data, external
feeds, tool calls, web/API work, persistence, deployment, and any future broker
integration.

## Secrets

- Never commit API keys, bearer tokens, cloud credentials, broker credentials,
  cookies, certificates, private keys, or populated environment files.
- Client/frontend code must never receive server-side provider or broker keys.
- Check presence and configuration shape without printing secret values.
- Redact URLs, headers, exception text, and vendor payloads that may contain
  credentials.
- Example environment files contain names and safe placeholders only.

## Portfolio And Account Privacy

Treat holdings, cash, cost basis, decisions, reports, watchlists, tax lots,
broker IDs, and strategy settings as private financial data.

- Do not place raw portfolio data in analytics or public logs.
- Logs should use run IDs, coarse statuses, and redacted instrument metadata.
- Export/share operations require explicit user action and a reviewed payload.
- Future multi-user storage must enforce owner isolation at the database and API
  layers, not only in UI code.

## Untrusted Data And Prompt Injection

News, social posts, filings, vendor text, model responses, and imported files are
untrusted data.

- Delimit external content and tell models to treat it as evidence, not
  instructions.
- External text must not change tools, policies, system prompts, credentials,
  destinations, or approval state.
- Tool names and arguments are allowlisted and schema-validated.
- A model cannot authorize new network destinations, shell commands, file paths,
  provider changes, or broker actions.
- Preserve source attribution so suspicious evidence can be excluded and
  reviewed.

## Network And Tool Boundaries

- Use fixed vendor base URLs or explicit operator configuration.
- Validate custom endpoints and prevent credentials from being sent to an
  unintended host.
- Apply timeouts, response-size limits, retries with bounds, and rate-limit
  handling.
- Sanitize symbols and path components before filesystem use.
- Do not disable TLS verification to make a provider work.

## LLM Output Boundary

- Validate structured output before persistence or downstream computation.
- Treat free text as narrative only.
- Invalid/missing required fields produce `REVIEW`, never an executable default.
- Model confidence is untrusted input until evaluated/calibrated.
- LLM output cannot waive a data-quality or risk-policy failure.

## Platform And Deployment

- Use authentication and owner authorization before exposing private portfolio
  data over HTTP.
- Long-running jobs use durable job IDs and workers; do not rely on an HTTP
  process surviving.
- Apply least privilege to database, object storage, queue, and vendor accounts.
- Encrypt traffic and backups; document restore and credential-rotation paths.
- Container images should run non-root and use pinned/reviewed dependencies for
  deployments.
- Public deployment requires abuse controls, rate limits, audit logs, and a
  threat-model review.

## Future Broker Boundary

Broker work is prohibited without a separately approved contract. At minimum it
would require:

- Paper environment before live.
- Read-only account integration before trading permission.
- Deterministic order validation and risk checks.
- Explicit human approval for each order.
- Idempotency keys, reconciliation, audit logs, kill switch, and safe retry
  semantics.
- Separate credentials and environments for paper and live.

## Required Security Evidence

Security-sensitive changes must include applicable evidence for:

- Secret scanning and dependency review.
- Authentication and owner-authorization tests.
- Prompt-injection/tool-argument tests.
- Log and analytics redaction.
- Path/symbol/URL validation.
- Failure behavior for invalid structured output.
- No live-order path without approval.

Unavailable tooling must be recorded as a limitation and the gate remains
`UNVERIFIED` or `BLOCKED`.
