# Normalized Time-Series API

PLAN-021 defines a vendor-neutral, point-in-time-safe price contract. It
normalizes data already supplied by an approved pipeline; it does not select or
call a market-data vendor.

## Contract

`NormalizedTimeSeries` contains an instrument ID, dataset, interval, timezone,
quote currency, analysis `as_of`, explicit annualization periods, and ordered
OHLCV bars. Bars require timezone-aware timestamps, positive finite prices,
valid high/low envelopes, non-negative finite volume, unique timestamps, and no
row after `as_of`.

Adjusted close must be present for every bar or none. Returns, volatility, and
drawdown use adjusted close when complete and raw close otherwise; the selected
price basis is explicit in the response. Input order may vary, but duplicate
timestamps are rejected instead of being overwritten. UTC instruments require
UTC bar timestamps.

Deterministic output includes:

- per-bar simple return and drawdown;
- total return, annualized volatility, and maximum drawdown;
- exact-timestamp benchmark alignment, asset and benchmark return, excess
  return, correlation when defined, and annualized tracking error.

Benchmark comparison rejects interval or quote-currency mismatches and fewer
than two aligned observations. It never forward-fills one market onto another.

## Immutable Storage

Normalized JSON is stored as a content-addressed snapshot artifact. The
`SnapshotManifest` retains vendor, retrieval time, source window, content hash,
quality status, interval, timezone, currency, observation count, and price
basis. Reads select the latest snapshot whose `as_of` does not exceed the
requested time and then verify the owner-scoped artifact hash.

`GET /api/v1/instruments/{instrument_id}/timeseries` supports dataset, `as_of`,
inclusive start/end, and optional benchmark instrument ID. Future `as_of`,
future range end, unavailable owner payload, empty range, or insufficient
benchmark coverage fails explicitly.

Freshness thresholds and non-OK quality-state synthesis belong to PLAN-027.
Equity/ETF, NQ/ES, and crypto ingestion belong to PLAN-022 through PLAN-024.
