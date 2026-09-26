# Deterministic Stock Screener

PLAN-025 creates a reproducible candidate universe for liquid US large-cap
equities. It is a deterministic selection service, not an LLM recommendation,
portfolio allocation, performance claim, or autonomous trading feature.

## Inputs And Point-In-Time Boundary

Every input carries canonical instrument identity, an observation timestamp,
an immutable source snapshot ID and content hash, market cap, 20-day average
dollar volume, last price, history length, annualized volatility, and an
explicit data-quality state. Inputs observed after `as_of` are rejected rather
than silently excluded. Duplicate instrument IDs or canonical symbols also fail
closed.

The initial policy admits only investable equities on an explicit sorted venue
allowlist and in USD. Thresholds cover market cap, liquidity, price, history,
and maximum volatility. Any non-`OK` source quality is excluded with its exact
status; missing or unavailable data is never converted into a neutral value.

## Ranking And Reproducibility

Eligible equities receive deterministic market-cap and liquidity ranks. The
configured integer rank weights produce a rank-sum score; ties resolve by
market cap, liquidity, then canonical symbol. Candidates beyond the configured
limit are retained as explicit `outside_limit` exclusions.

The output contains every selected or excluded input, its `as_of` and explicit
generation timestamp, the full versioned policy, an input hash, and a universe
hash. Canonical JSON and stable sorting make a rerun with identical inputs,
policy, and timestamps byte-reproducible regardless of caller input order.

## Persistence Boundary

Screening snapshots can be stored as immutable, content-addressed,
owner-scoped artifacts and loaded only by the owning user. The screener does
not call a data vendor, alter the instrument master, create positions, set
target weights, or send orders. PLAN-026 owns reusable derived factors;
PLAN-027 owns cross-pipeline health summaries.
