# Portfolio ledger

The ledger stores immutable, owner-scoped cash and transaction events and
replays them deterministically into long-only positions, cash, NAV, realized
P&L, and unrealized P&L. Transactions are broker-neutral imported/manual facts;
this module has no order-generation or broker path.

Replay rejects duplicate events, owner/ledger mismatches, negative cash, short
positions, missing prices, and implicit FX conversion. Snapshot hashes bind the
full transaction payloads and valuation quotes used at the requested `as_of`.

Each `ValuationQuote` carries instrument/currency, source and retrieval times,
snapshot ID, content hash and quality status. Open holdings require an explicit
`max_price_age`; stale, future, non-OK or mismatched prices are rejected. Events
sharing a timestamp require a distinct `sequence` to establish accounting
order. Standalone fee events reduce realized P&L. Deterministic snapshot IDs and
hashes make identical replay idempotent; future events do not affect historical
snapshots. SQLite tests cover immutable persistence and owner isolation;
PostgreSQL and valuation-service integration remain milestone gates.
