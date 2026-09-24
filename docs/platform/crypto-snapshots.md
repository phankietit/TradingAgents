# BTC And ETH Snapshot Pipeline

PLAN-024 adds a UTC, 24/7 snapshot path for the initial BTC/ETH whitelist. It
does not apply company fundamentals, SEC filing logic, custody execution, or
exchange trading APIs to crypto.

The pipeline links an immutable normalized price series to observations from
distinct named venues. Each observation records base/quote identity, UTC
observation time, bid, ask, last price, 24-hour quote volume, and vendor.
Future observations are excluded and counted rather than shifted backward.

Versioned quality thresholds state the minimum venue count, aggregate quote
volume, maximum median spread, and maximum observation age. The resulting
snapshot reports venue coverage, excluded future observations, liquidity,
spread, staleness, and deterministic price volatility. Insufficient coverage
or liquidity remains `COVERAGE_GAP`; stale venue data remains explicitly
reported.

ETH is compared against an immutable BTC series on exact UTC timestamps. BTC is
the baseline and cannot benchmark itself. The pipeline does not forward-fill
benchmark rows across missing dates.

Snapshot payloads are content-addressed and owner-scoped. These data-quality
metrics do not set portfolio weights or waive the separately capped crypto risk
policy. Expanding beyond BTC/ETH requires an explicit whitelist/product change.
