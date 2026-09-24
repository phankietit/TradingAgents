# Platform Domain Contracts

Milestone 1 introduces strict Pydantic contracts under
`tradingagents.contracts`. They define the wire boundary shared by future API,
worker, persistence, and Web UI layers without coupling those layers to a
database model.

## Versioning

- Root contracts contain `schema_version` and currently emit `1.0`.
- Unknown fields are rejected and instances are immutable.
- A breaking field or semantic change requires a new schema version and an
  explicit migration/compatibility path.
- Persistence models may add internal columns, but serialized platform payloads
  must validate against these contracts.

## Contract Roots

- `InstrumentContract`: canonical identity, asset class, venue, timezone,
  calendar, benchmark, and investable/reference-only boundary.
- `InstrumentAliasContract`: immutable namespaced alias and normalized lookup
  key linked to one canonical instrument.
- `NormalizedTimeSeries` and `TimeSeriesView`: ordered point-in-time OHLCV,
  adjusted-price basis, deterministic returns/risk metrics, and aligned
  benchmark comparison.
- `EquityETFSnapshotBundle`: filed-date equity evidence or fund-specific ETF
  evidence with per-dataset coverage and future-row exclusion counts.
- `FuturesReferenceSnapshot`: reference-only NQ/ES contract identity, explicit
  roll adjustment, CME overnight/RTH sessions, and non-fabricated gap handling.
- `CryptoSnapshot`: BTC/ETH-only UTC prices, multi-venue liquidity/freshness
  evidence, versioned quality thresholds, and exact-timestamp BTC comparison.
- `StockUniverseSnapshot`: deterministic point-in-time screening policy,
  ranked candidates, explicit exclusions, and stable input/universe hashes.
- `SnapshotManifest`: immutable dataset provenance, content hash, data window,
  retrieval time, and quality state.
- `RunManifest`: reproducible analysis lifecycle, model/config/prompt identity,
  and snapshot references.
- `EvidenceReference`: claim-to-source linkage.
- `DecisionCandidate`: structured LLM analysis combined with deterministic
  weights and policy results; human approval is mandatory.
- `PortfolioSnapshot`: owner-private, point-in-time cash and long-only holdings.
- `PolicyContract` and `PolicyCheck`: versioned deterministic policy input and
  result.

## Asset Boundaries

- Cash indices and NQ/ES futures references are `reference_only`.
- Crypto uses UTC.
- Negative portfolio quantities are rejected in the initial long-only product.
- An approval-ready decision requires `OK` data quality and passing blocking
  policy checks.

These contracts do not add a web API, database, worker, portfolio calculator,
broker, or execution path. Those remain separate tickets.
