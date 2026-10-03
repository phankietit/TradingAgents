# TradingAgents Product Contract

## 1. Current Product

The supported package baseline is a Python research framework. It provides:

- A Typer/Rich interactive CLI.
- A programmatic `TradingAgentsGraph` API.
- A LangGraph workflow of market, sentiment, news, fundamentals, research,
  trader, risk, and portfolio-manager agents.
- Multiple LLM and market-data providers.
- Markdown reports, a local decision/reflection log, optional checkpoints, and
  an independent-cell backtest.

The draft `fix/TA-R01-research-quality` candidate additionally implements a
private FastAPI/worker/React workspace with owner authorization, immutable
snapshots/artifacts, bilingual saved reports, portfolio records, deterministic
risk checks and human review. Its R01–R14 acceptance is incomplete; see
`HANDOFF.md` and the dated research acceptance receipts for exact-SHA evidence.
Implemented web controls do not establish live financial/editorial quality or
release readiness.

Current candidate acquisition covers Yahoo daily prices and non-exhaustive
recent news, plus the owner-approved existing SEC EDGAR adapter for AAPL web.
Social/macro ingestion and other-asset fundamentals remain unfinished. Missing
coverage stays explicit; analyst readers alone do not prove source acquisition.
NQ=F is the owner-selected reference; live acceptance is BLOCKED until eligible
active-contract/roll data exists. No substitute source has been approved.

Neither the baseline nor this candidate provides a portfolio simulator, paper
or live broker, order execution, or autonomous trading system. The web candidate
is for a private owner; public hosting and multi-user deployment are unverified.

## 2. Intended Direction

The intended product is a private portfolio decision-support platform for one
owner. Its first supported universe is:

- Liquid US large-cap equities.
- Broad and sector ETFs used as investable index proxies.
- Candidate equities selected by deterministic screening.
- A small, separately governed set of large-cap crypto assets.

The default operating horizon is weekly and medium-term. Intraday/HFT,
microcaps, derivatives, leverage, shorting, and fully autonomous trading are
outside the initial product boundary.

## 3. Decision Authority

The decision path must remain:

```text
versioned data snapshot
  -> LLM analysis and evidence synthesis
  -> structured decision candidate
  -> deterministic portfolio and risk policy
  -> human approval
  -> optional paper execution in a later phase
```

LLMs may propose:

- Directional rating and confidence.
- Investment thesis and counter-thesis.
- Evidence summaries.
- Risks, catalysts, and invalidation conditions.

Deterministic code must own:

- Data-quality and point-in-time eligibility.
- Portfolio valuation and exposure.
- Target/max weights and order quantity.
- Cash, concentration, correlation, turnover, and loss limits.
- Policy pass/fail results.
- Whether an order proposal may be shown for approval.

Only the human owner may approve an order. An LLM response is never an order.

For the draft candidate, research completion means an ordinary succeeded run or
a fully integrity-verified linked completion receipt. The latter preserves the
original failed/cancelled run and its history; it is not a policy exception or
human approval. Existing authenticated owner transitions still revalidate source
bytes/evidence, deterministic risk, exact policy and append-only lifecycle before
approval. A stage note, dispatched child, missing/corrupt receipt or model prose
cannot provide completion authority. Default continuation dispatch remains off,
and operational/live acceptance is still incomplete.
Review/reject/expire timestamps must also be at or after linked completion;
reject invalid timing before appending history, rather than commit an event that
the integrity reader cannot subsequently validate. This grants no new approval
or execution authority and does not change ordinary successful-run behavior.

## 4. Asset-Specific Contracts

### Equities

Use market, news, sentiment, fundamentals, and filing evidence. US historical
fundamentals should prefer filed-date-aware SEC data. A company identity
resolved from a current profile must be labeled as current when used in a
historical run.

### ETFs And Index Exposure

Prefer an investable ETF over a non-tradable raw index when the output may lead
to a portfolio proposal. ETF analysis should use holdings, concentration,
sector exposure, flows, tracking characteristics, market breadth, and macro
regime. Do not apply company-specific balance-sheet reasoning to an ETF.

### Candidate Equities

Candidate discovery must be deterministic and reproducible before LLM analysis.
The screener must record universe, filters, data timestamp, exclusions, and
ranking inputs. The LLM must not invent a market-wide candidate list from model
memory.

### Crypto

Crypto uses a separate 24/7 UTC data and risk path. Company fundamentals and SEC
filings do not apply. The path must account for liquidity, volatility,
custody/exchange risk, benchmark choice, and missing historical text feeds.
Crypto risk limits must be separate from equity limits.

## 5. Required Decision Output

A platform-grade decision must be schema-valid and include at least:

```text
decision_id
run_id
symbol
asset_type
as_of
rating
confidence
thesis
evidence[] { claim, source, observed_at, data_hash }
risks[]
invalidation_conditions[]
data_quality
current_weight
target_weight
max_allowed_weight
policy_checks[]
requires_human_approval
```

If the rating or required evidence cannot be validated, the result is `REVIEW`.
Free text must not be coerced into an executable proposal.

## 6. Performance And Safety Claims

- No guaranteed-return language.
- No performance claim without versioned inputs, exact configuration, costs,
  benchmark, sample size, date range, and limitations.
- Backtest, paper, and live results must always be labeled separately.
- A model-generated confidence value is not a calibrated probability unless a
  documented evaluation proves calibration.
- Research completeness is not production readiness.

## 7. Product Change Gate

Any change to asset scope, decision authority, data provenance, risk policy,
human approval, broker access, or performance reporting requires an explicit
product decision and updates to this contract before implementation.
