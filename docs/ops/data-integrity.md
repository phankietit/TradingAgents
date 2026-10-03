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

### Structured FRED prerequisite (draft candidate)

`dataflows/platform_fred.py` reuses the existing FRED key/endpoints; no CLI
default or new provider changes. One explicit series and
requested window use the original 365-day lookback unless explicitly supplied.
Both metadata and observations pin `realtime_start == realtime_end` to the last
fully elapsed Chicago day before the analysis cutoff. The next Chicago midnight
is conservative availability, not an exact release/revision timestamp. A period
date is never substituted for that availability. FRED's API date semantics:
[real-time periods](https://fred.stlouisfed.org/docs/api/fred/realtime_period.html),
[observations](https://fred.stlouisfed.org/docs/api/fred/series_observations.html).

All returned observations survive structured storage, including explicit `.`
missing values as null; no inference, unit conversion or CLI 40-row display cap.
Transformed values, wrong vintage/identity, unordered/duplicate/future rows,
nonfinite values and incomplete pagination are `INVALID`, never truncated into
valid evidence. Explicit resource ceilings (100,000 rows, 2 MB parsed response,
100-year maximum request) reject rather than silently shorten the window.
The legacy/CLI `_request` still buffers JSON before parser limits. The separate
current preparation wrapper instead streams uncompressed HTTP with no redirects,
rejects advertised/actual bodies over 2 MB and bounds child output to 2 MB. Fixed
child invocation, bounded input, reader/writer shutdown and kill/reap supervise
the 75-second acquisition deadline including import, network and child parsing.
Parent bounded parsing/validation checks that same deadline and withholds late
results; termination/reaping takes cleanup time, not a remote provider-stop claim.
No abandoned provider thread remains. HTTP/read timeout is 30 seconds per request;
whole supervision handles slow trickle or multiple requests beyond that bound.

Observation-period freshness limits are daily14, weekly28, biweekly42,
monthly100, quarterly210, semiannual400, annual800 calendar days. A fresh
vintage does not make an old observation fresh. These declared ingestion limits
are not portfolio risk limits, evidence of exhaustive history or a promise of
an expected publication date. Unsupported frequency is `INVALID`.
Reachable validated empty metadata is `NO_DATA`; empty requested observation
window is `COVERAGE_GAP`; actual all-missing rows are `NO_DATA`; old periods are
`STALE`. Missing key/network/HTTP failures are `UNAVAILABLE` with fixed reasons.
The legacy boundary's untyped 400 is conservatively `UNAVAILABLE`, not guessed
as an unknown series by parsing vendor prose. Raw exceptions/credential URLs
are never stored. Failed collection rows cannot become usable coverage.

`platform/market_data/macro.py` binds full payload hash, series/window/vintage,
retrieval and instrument identity in immutable owner-readable storage. Retrieval
sets snapshot `as_of`; no historical backdating or previous snapshot rewrite.
Load revalidates full collection and complete reconstructed manifest parity,
owner access, hash, artifact kind/media and cutoff/freshness. Artifact write
failure rolls back metadata; corrupt bytes refuse. No new DB schema is needed.
Validated stored macro snapshots are admitted only to the news analyst. The
owner loader rechecks the repository's full instrument identity and immutable
storage provenance; the engine compares full request identity before constructing
a graph/client. Collection/manifest parity and hash checks alone do not authenticate
a vendor or establish identity from an instrument UUID.
Two read-only tools page all observations and compare explicit period labels.
Facts bind series, native units/frequency/seasonal adjustment, operands and vintage;
missing operands, nonpositive percentage-change denominators and nonfinite results
stay unavailable. No interpolation, literal operands or inferred economic rates.
Latest-only prompt/catalog projections do not truncate retained/tool-accessible
history. Application-owned full EN/VI statements distinguish native levels,
native-unit differences (percentage points for Percent) and arithmetic percent
changes with an explicit denominator. Existing bounded financial/translation
repair and publication/risk/approval gates remain unchanged. Coverage warnings
distinguish macro from headlines, and observation labels from release times.
Authenticated owner/CSRF `POST /api/v1/instruments/{id}/prepare-macro` accepts only
an explicit series and 1–36,525-day window (default365), no client analysis cutoff.
The server pins current time/vintage and rechecks full identity/window before
append-only persistence. Matching owner snapshots can be reused only within
15 minutes, the same current complete Chicago vintage and exact series/window;
quality/content checks still apply. One acquisition at a time and a 60-second
owner/instrument/series/window cooldown bound repetition; these process-local
controls are not multi-process/public deployment guarantees. NQ/ES stay unsupported.
Failed valid collections are audited but cannot be selected; driver errors return
fixed unavailable/invalid states without raw vendor prose. No AI job is created.
The web replaces only the same dataset/series, retains other selected sources,
requires explicit review at 16 sources and resets paid consent. Coverage separates
macro from headlines; original native units, observation dates and vintage remain
inspectable. Synthetic fixtures refuse live acquisition by default.
Local transport/SQLite/PostgreSQL and browser fixtures are not live FRED or
financial/editorial proof; dated receipts state which gates actually ran.

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
