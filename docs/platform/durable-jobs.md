# Durable Analysis Jobs

Analysis execution uses a PostgreSQL-backed durable queue. The queue is part of
the platform database and does not require a second broker or silently select a
production service.

## Lifecycle

```text
queued -> running -> succeeded
                  -> retry_wait -> running
                  -> failed
                  -> cancel_requested -> cancelled
queued/retry_wait -> cancelled
```

- Enqueue uses an owner-scoped idempotency key and one job per run.
- Claim uses `FOR UPDATE SKIP LOCKED` on PostgreSQL so concurrent workers do not
  receive the same job.
- A claim has a bounded lease. Handlers heartbeat during long work.
- An expired lease returns to `retry_wait` while attempts remain; otherwise it
  fails with `LEASE_EXPIRED`.
- Owner cancellation is immediate before execution and cooperative while a
  handler owns the lease.
- Retriable failures use bounded attempts and exponential backoff in
  `JobWorker`.
- Claim commits before handler execution, so no database row lock is held for
  the duration of an LLM or data-provider call.

## Worker Boundary

`JobWorker` dispatches a registered handler by `JobKind`. It does not select an
LLM, market-data vendor, or deployment runtime. Handlers receive a context for
heartbeat and cancellation checks. Output artifact IDs may be attached only on
successful completion.

Raw exception messages are not persisted by the generic worker. It records a
stable `HANDLER_ERROR` code plus the exception class, reducing the chance that
provider credentials or private inputs enter durable job state.

## Current Scope

This ticket provides orchestration primitives and worker semantics. It does not
start a daemon, choose a hosting provider, expose a public queue, or execute a
broker action. Process supervision, deployment replicas, alerts, and disaster
recovery remain environment-specific release gates.
