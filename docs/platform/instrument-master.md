# Instrument Master

PLAN-020 adds the canonical identity layer used by later market-data pipelines.
It is a registry and lookup service, not a live security-master vendor and not
an investment recommendation universe.

## Identity Contract

Every instrument retains a stable UUID plus canonical symbol, asset class,
tradability, venue, quote currency, timezone, session calendar, and benchmark.
Bootstrap UUIDs are deterministic from asset class, venue, and canonical
symbol. A change to any of those identity fields creates a reviewable identity
change rather than silently retargeting an existing instrument.

Aliases are immutable, namespaced records. Lookup normalization applies Unicode
NFKC, surrounding-whitespace removal, and case folding. A namespace and
normalized alias can identify only one instrument. An unqualified alias that
maps to different instruments across namespaces fails as ambiguous; it never
selects one by insertion order. An alias cannot shadow another instrument's
canonical symbol.

## Initial Catalog

The idempotent bootstrap catalog covers each initial product boundary:

- AAPL as a representative US large-cap equity.
- SPY and QQQ as investable index proxies.
- S&P 500 and Nasdaq-100 cash indices as reference-only benchmarks.
- NQ and ES futures symbols as reference-only market context.
- BTC and ETH as the initial crypto whitelist, using UTC and a 24/7 calendar.

This small bootstrap set is not the final 20–50 stock universe. PLAN-025 owns
the deterministic screened universe; LLM memory must not add candidates.
Instrument bootstrap is an explicit operator action and never runs implicitly
during API startup or database migration.

## Persistence And API

Migration `0007_instrument_aliases` creates the alias registry and backfills a
canonical alias for every existing instrument. Upgrade fails on normalized
canonical collisions instead of dropping or choosing a record.

Authenticated read endpoints are:

- `GET /api/v1/instruments` with optional `asset_class`, `tradability`, and
  exact `venue` filters.
- `GET /api/v1/instruments/resolve?alias=...&namespace=...` for fail-closed
  resolution and alias provenance.
- `GET /api/v1/instruments/{instrument_id}` for canonical identity and aliases.

No endpoint mutates the catalog. There is no market-data call, fallback vendor,
broker, order, futures sizing, or crypto expansion in this ticket.
