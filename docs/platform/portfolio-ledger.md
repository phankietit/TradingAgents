# Portfolio ledger

The ledger stores immutable, owner-scoped cash and transaction events and
replays them deterministically into long-only positions, cash, NAV, realized
P&L, and unrealized P&L. Transactions are broker-neutral imported/manual facts;
this module has no order-generation or broker path.

Replay rejects duplicate events, owner/ledger mismatches, negative cash, short
positions, missing prices, and implicit FX conversion. Snapshot hashes bind the
transaction IDs and valuation prices used at the requested `as_of`.
