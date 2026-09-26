# Portfolio ledger

The ledger stores immutable, owner-scoped cash and transaction events and
replays them deterministically into long-only positions, cash, NAV, realized
P&L, and unrealized P&L. Transactions are broker-neutral imported/manual facts;
this module has no order-generation or broker path.

Replay rejects duplicate events, owner/ledger mismatches, negative cash, short
positions, missing prices, and implicit FX conversion. Snapshot hashes bind the
full transaction payloads and valuation quotes used at the requested `as_of`.
The pure replay engine, not only the persisted service, rejects quotes observed
after `as_of`; an old source date does not establish historical availability.

Each `ValuationQuote` carries instrument/currency, source and retrieval times,
snapshot ID, content hash and quality status. Open holdings require an explicit
`max_price_age`; stale, future, non-OK or mismatched prices are rejected. Events
sharing a timestamp require a distinct `sequence` to establish accounting
order. Standalone fee events reduce realized P&L. Deterministic snapshot IDs and
hashes make identical replay idempotent; future events do not affect historical
snapshots. SQLite tests cover immutable persistence and owner isolation.

`PortfolioLedgerService` resolves quotes by explicit snapshot IDs from the same
owner's immutable artifact store, verifies hashes/provenance/currency and the
evaluation cutoff, and uses reported close (not adjusted close) to value actual
held units. Snapshot coverage must exactly match open holdings; missing owner
history is not silently treated as a flat book. Only supported investable
instruments may appear in imported ledger history. The resulting snapshot is
persisted idempotently for use by the risk pipeline. These are accounting
snapshots, not simulated fills or portfolio backtest performance. PostgreSQL
evidence remains a milestone gate.
