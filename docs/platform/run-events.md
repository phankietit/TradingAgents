# Resumable Run Events

Run progress is an append-only, owner-scoped event log. Each event receives a
strictly increasing sequence within its run. PostgreSQL appenders lock the run
row while allocating the next sequence, so concurrent workers cannot publish
the same position.

Initial event types cover queueing, execution start, stage progress, artifact
creation, decision readiness, retry, cancellation, failure, and success. Event
payloads are structured JSON and must contain only UI-safe identifiers, coarse
status, stage, attempt, and stable error codes. Raw model output, vendor
responses, credentials, portfolio data, and exception messages do not belong
in run events.

`model.usage` additionally records provider-reported token counters, failed-call
count and completeness, cumulative within one worker attempt. Use only the
latest receipt per attempt when aggregating; summing every receipt double-counts
usage. Missing usage and subscription price are unknown, not zero. API and worker
must be upgraded together to recognize this additive event type. No SQL migration
is needed because event types/payloads are stored as text/JSON.

## SSE Contract

`GET /api/v1/runs/{run_id}/events` uses the authenticated owner from the
HTTP-only session. A run owned by anyone else returns `404` before a stream is
opened.

Each SSE item contains:

```text
id: <run-local sequence>
event: <run event type>
data: <versioned RunEvent JSON>
```

Browsers reconnect with `Last-Event-ID`; the server returns only events after
that sequence. It emits keep-alive comments while a non-terminal run is idle
and closes after `run.succeeded`, `run.failed`, or `run.cancelled` has been
delivered. Polls use short independent transactions offloaded from the async
event loop; the stream does not keep an authentication or database transaction
open for its lifetime.

SSE is progress transport, not an audit substitute. The PostgreSQL event table
is the durable replay source, while immutable artifacts and decision contracts
remain the evidence source of truth.
