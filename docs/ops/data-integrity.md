# TradingAgents Data Integrity Contract

This contract applies to market prices, indicators, filings, fundamentals,
news, social feeds, macro data, prediction markets, instrument identity,
portfolio inputs, backtests, and evaluation artifacts.

## Required Metadata

Every platform-grade data artifact must be attributable to:

- Instrument and canonical symbol.
- Asset type, venue, quote currency, and timezone when relevant.
- Vendor and retrieval path.
- Requested window and analysis `as_of`.
- Observed/retrieved timestamp.
- Source timestamp or filing/publication date.
- Cache/snapshot version or content hash.
- Coverage, freshness, and quality status.

Generated reports must preserve enough provenance to trace material claims back
to their source artifact.

## Point-In-Time Rules

- A historical run may use only information public on or before its analysis
  date.
- Financial statements are eligible by filing/publication date, not fiscal
  period end alone.
- Restatements must not replace the value knowable at the historical date.
- Current company profiles used for historical identity must be labeled as
  current-vintage metadata.
- Live-only prediction-market odds must be withheld from historical runs.
- Recent-only news/social endpoints do not prove historical coverage. If their
  window cannot reach the requested period, return coverage unavailable.
- A future date is invalid input.

## Failure Semantics

Keep these states distinct:

| State | Meaning |
| --- | --- |
| `OK` | Eligible data is available and passed quality checks |
| `NO_DATA` | Vendor was reachable but has no eligible data |
| `STALE` | Data exists but is too old for the contract |
| `UNAVAILABLE` | Vendor/auth/network/rate limit prevented observation |
| `COVERAGE_GAP` | Source cannot cover the requested historical window |
| `INVALID` | Input or response violates schema/identity constraints |

Do not reinterpret `UNAVAILABLE` as `NO_DATA`, or empty source coverage as a
neutral market signal. Agents must not estimate or fabricate missing values.

## Vendor Routing

- Explicit configuration defines the allowed fallback chain.
- Never silently call an unconfigured vendor.
- Record which vendor actually served each artifact.
- A fallback success does not erase a primary-vendor failure; retain it in
  diagnostics and evidence.
- Adding or changing a production vendor requires explicit approval, documented
  data/licensing implications, and contract tests.

## Snapshots And Reproducibility

- Historical evaluation should read immutable snapshots rather than mutable live
  feeds.
- Snapshot keys must include symbol, asset type, source, query/window, retrieval
  timestamp, and schema version.
- Do not overwrite a snapshot used by a recorded decision; create a new version.
- Record model, prompt, config, and data hashes together in the run manifest.
- If inputs cannot be reconstructed, label the result indicative and
  non-reproducible.

## Asset-Specific Rules

### Equities

- Respect exchange calendars and corporate actions.
- Use filed-date-aware fundamentals where available.
- Avoid microcap/penny-stock coverage in the initial product scope.

### ETFs

- Treat an ETF as a fund, not a company.
- Track investable symbol, holdings vintage, concentration, expense/tracking
  characteristics, and benchmark.

### Crypto

- Use UTC and explicit 24/7 bar boundaries.
- Record exchange/aggregator coverage and custody/liquidity limitations.
- Do not inject company financial statements into crypto analysis.

## Test Expectations

Data changes require tests for applicable cases:

- Boundary dates and future-row exclusion.
- Filing/publication date behavior.
- Stale and empty responses.
- Vendor outage versus no-data classification.
- Symbol normalization and path safety.
- Cache freshness and immutable snapshot versioning.
- Cross-vendor fallback order.
- Historical coverage gaps for news/social/live-only sources.
