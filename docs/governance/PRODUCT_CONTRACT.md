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
Independent authenticated StockTwits/Reddit preparation now uses the original
public endpoints, seven-day sample and immutable owner snapshots. Full eligible
returned text and source-bound counts enter the original Sentiment analyst;
unlabeled/absent feeds are not neutral sentiment or calibrated probabilities.
Collection is current-only, not historical backdating or exhaustive coverage.
No author profiles, inferred engagement, new source or AI call during preparation.
CLI routing and all graph/financial/translation/risk/approval gates are unchanged.
Live social/source-entailment acceptance and other-asset fundamentals remain
unfinished. Missing coverage stays explicit; analyst readers alone do not prove
source acquisition. Failed or malformed feeds cannot authorize research.

Macro ingestion may reuse the existing FRED adapter with explicit series and
original lookback, pinning metadata and observations to a fully elapsed Chicago
vintage day. Day-level vintage is not an exact release timestamp. Store full
structured observations, units/frequency and missing values with immutable
instrument/retrieval/window provenance, never the CLI's shortened display table.
Freshness must use the observation period as well as vintage/retrieval time;
missing, stale, malformed and inaccessible series cannot become valid coverage.
The separate authenticated current preparation path is implemented below;
historical snapshot backdating, new providers and decision authority are not enabled.
The snapshot-only macro path admits validated FRED collections to the
news analyst, never as headlines/social/company statements. Require full
collection/manifest parity before model construction, read-only full-history
paging, and source-bound native-unit/period/vintage facts. Application-owned
complete EN/VI statements must distinguish native levels, native-unit differences
and arithmetic percentage changes; missing/invalid operands stay unavailable.
Macro-only input must disclose absent headline coverage. Snapshot admission alone
does not prove live acquisition, exhaustive macro/news or semantic investment quality,
and changes no graph role, repair allowance, deterministic policy or human approval.
NQ=F is the owner-selected reference; live acceptance is BLOCKED until eligible
active-contract/roll data exists. No substitute source has been approved.

The draft current-macro preparation path reuses FRED's configured key/endpoints
for one explicit series/window. Bound both streamed response and child output;
supervise the entire acquisition, reap the child, and withhold late/invalid data.
Authenticated owner/CSRF preparation must preserve immutable history, distinct
failure states, explicit scope and existing headline selections. No new AI call,
provider, portfolio authority, historical backdating or NQ substitute is enabled.
Its implementation is not live FRED, economic/editorial or release acceptance;
dated receipts distinguish local transport/API/browser evidence from live proof.

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

Internal linked supervision may append a separate local-stop receipt after
child reaping and pipe-reader shutdown, even when cancellation/expiry prevents
normal publication. This is control-plane evidence only: the original private
lease identity, entry/dispatch and source/accounting bindings must still match.
It cannot publish a report/checkpoint/decision, rewrite terminal history, claim
remote provider termination/cost, replenish allowance or authorize continuation.
Missing or corrupt stop evidence stays unknown; default continuation stays off.
The browser progress step distinguishes a cancellation request from verified
shutdown: `cancel_requested` does not render processing as stopped. The current
API does not yet project the integrity-verified local-stop receipt to the UI;
after local shutdown its pending heading remains an unfinished operational UX
gate, not proof that the provider stopped or that retry is authorized.

Internal terminal preparation derives a trusted checkpoint codec from original
owner-readable inputs and bounded actual SDK initialization. Existing locked
owner/session/CSRF validation avoids session last-seen updates; DB locks do not
span SDK construction. Original inputs/accounting/authentication are rechecked
after preparation. It records no consent, entry, execution, model use or dispatch.
The internal linked factory requires the existing retained observer, original
terminal source binding, exact initialized fingerprint/nodes, private lease and
bound result publisher; changed configuration refuses. Its returned supervisor
still requires separate one-time durable dispatch/child verification/publication.
The candidate mounts authenticated preparation and reservation API endpoints.
They accept no caller codec/config: preparation returns an opaque observation
digest and original remaining allowance; reservation rederives identity and
requires literal consent and all three disclosure acknowledgments. Original
owner/session/CSRF checks close before SDK work and are rechecked at commit.
A process-local lock bounds simultaneous preparation, not distributed/public
deployment. Responses keep dispatch_enabled false (no direct HTTP model dispatch).
Ordinary startup remains ordinary-only; explicit operator `--continuations`
polling may consume a consented reservation. No browser control is enabled yet.
API/native/full and live/semantic acceptance
remain separately evidenced. No original-history rewrite or fresh allowance is granted.

Trusted reserved preparation rechecks durable consent, active owner, immutable
original job/run/input bindings and complete accounting, derives actual SDK
identity without an owner session token, then validates the entire observation
and checkpoint before a separate one-time claim. A single-execution worker
operation assembles retained publication context, original sources, exact
publisher/factory, heartbeat, original graph restore and separate completion.
Renewal uncertainty refuses callback/publication; ACK uncertainty cannot reset
the attempt. This is not default polling/browser dispatch, a fresh allowance,
rewritten terminal history, financial/translation acceptance or human approval.

Opt-in durable polling gives ordinary jobs priority. A separately hashed preclaim
preparation refusal excludes the reservation across restart and from claim; it
does not grant retry, lease, model entry or fresh budget. Claimed uncertainty is
never automatically requeued. Owner-authenticated status and CSRF/Origin-protected
cancel operate without SDK construction. Completion is reported only after the
full separate completion/report reader validates it; active cancellation is a
request, not proof of provider termination. Migration 0018 is explicit/additive;
rollback removes control receipts and must not authorize retry or alter history.
Professional browser controls, full current regression and live acceptance remain
separate unfinished gates.

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
