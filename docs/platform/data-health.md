# Data Health Engine

PLAN-027 defines one deterministic classification engine for platform data. It
keeps six states distinct and uses the same worst-state precedence for
equity/ETF, NQ/ES reference, crypto, and aggregate health outputs.

## Status Semantics

Precedence from least to most severe is `OK`, `NO_DATA`, `STALE`,
`COVERAGE_GAP`, `UNAVAILABLE`, and `INVALID`.

- `OK`: eligible data passed identity, schema, coverage, and freshness checks.
- `NO_DATA`: the source was reachable and covered the request but returned no
  eligible records.
- `STALE`: eligible records exist, but the latest one exceeds the explicit
  freshness limit.
- `COVERAGE_GAP`: the source cannot cover the requested point-in-time window,
  or all returned rows were after `as_of`.
- `UNAVAILABLE`: vendor, authentication, network, or rate limiting prevented
  observation.
- `INVALID`: schema/identity failed, an eligible timestamp is in the future, an
  unavailable source claims records, or records lack required timestamps.

The engine never converts outage into empty data, future-only rows into valid
coverage, or missing timestamps into freshness. It preserves excluded-future
counts and source diagnostics in each check.

## Reports And Persistence

A report requires probes for one exact `as_of`, sorts and deduplicates their
dataset/vendor/instrument identities, classifies every probe, counts every
state, and exposes the worst status. Canonical inputs and outputs produce a
stable report hash and ID regardless of caller order. Reports may be persisted
as immutable content-addressed owner-scoped artifacts for later UI and audit
use.
