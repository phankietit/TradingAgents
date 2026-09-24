# Equity And ETF Snapshot Pipeline

PLAN-022 composes approved source batches into immutable, point-in-time equity
or ETF evidence. The pipeline is vendor-neutral and performs no network call;
selecting or changing a production vendor remains a separate product decision.

## Point-In-Time Selection

- Price evidence must already exist as a normalized immutable snapshot eligible
  at the requested `as_of`.
- SEC filings and fundamentals are eligible by `filed_at`, never period end.
- News is eligible by `published_at`.
- ETF holdings and fund metadata are eligible by `holdings_as_of`.
- Records after `as_of` are excluded and counted in dataset coverage; they are
  never rewritten to the analysis date.
- Restatements remain distinct source facts through filing timestamp and source
  ID instead of overwriting what was knowable earlier.

Every source batch declares a vendor, quality status, and reason. A non-OK
batch cannot carry apparently valid records. Empty reachable data becomes
`NO_DATA`; rows that exist but are all future-ineligible become `COVERAGE_GAP`;
vendor failure remains `UNAVAILABLE`.

## Asset Separation

Equity bundles may contain SEC filings and filed-date fundamentals, but cannot
contain ETF fund metadata. ETF bundles contain holdings vintage, issuer,
expense ratio, benchmark, and weights; company fundamentals are rejected.
An `OK` ETF bundle requires eligible fund metadata.

The bootstrap AAPL/QQQ examples are identity coverage, not recommendations or
a claim that the final stock universe has been selected.

## Storage And Provenance

The canonical bundle is serialized deterministically and stored as an immutable
content-addressed artifact. Its snapshot manifest records the composite
pipeline ID, source time window, overall quality, price snapshot ID, and
per-dataset vendors, eligible counts, future exclusions, status, and reason.
Payload reads remain owner-scoped and verify artifact integrity.

Live provider reachability, licensing, freshness thresholds, and fallback
routing are not implied by local fixture tests. PLAN-027 owns cross-dataset
health policy; PLAN-025 owns screened universe selection.
