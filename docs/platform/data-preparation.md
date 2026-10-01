# Current-data preparation in the web

The analysis form provides **Prepare latest prices** and an independent optional
**Add recent headlines** action before paid AI consent. Neither action needs a
Yahoo API key or AI call. They are current-vintage evidence workflows, not a
full fundamental, social, macro or historical replay.

## Flow and boundaries

1. Select an instrument and prepare prices. The authenticated, CSRF-protected
   `POST /api/v1/instruments/{id}/prepare-data` accepts no vendor URL or symbol.
2. Reuse a current owner-readable `yfinance.daily.v4` snapshot only after hash
   verification and complete five-year session coverage checks. Otherwise fetch
   five calendar years of daily OHLCV through the
   existing yfinance dependency, with adjusted close and no rounding.
3. Validate identity, currency, exchange timezone, finite OHLCV, duplicates,
   complete exchange-session coverage and latest completed session. Exclude
   unfinished sessions and allow one hour after close for publication.
   Owner-approved crypto research permits exactly one missing **trailing** daily
   session from Yahoo. Internal gaps, two or more missing trailing sessions,
   invalid prices and unfinished bars still fail. US assets remain strict.
   A delayed result is eligible only under this bounded latest-available contract,
   not a claim of current-market completeness: manifest metadata records the
   expected/actual close and missing-session count; the UI, analyst prompt and
   deterministic bilingual report notice disclose the limitation. The actual
   source end remains unchanged. Delayed snapshots are not reused as current;
   the next permitted preparation tries Yahoo again. No filling or fallback.
4. Append an immutable `ohlcv.daily` snapshot; never rewrite earlier evidence.
   `as_of` is acquisition completion, **not** the last bar date. Newly retrieved
   adjusted history is not a historical vintage and cannot serve earlier runs.
5. Update the form's research cutoff to server time, select the price source,
   clear AI consent, and rediscover eligibility. Owner freshness limits remain
   unchanged. Portfolio valuation timestamps are never moved by this action.
6. Separately authorize AI and submit the durable analysis job. A configured
   worker processes it; the API never runs the model inline or starts a worker.

## Alignment with the original research engine

The original `load_ohlcv` and web acquisition share `OHLCV_HISTORY_YEARS = 5`
from `dataflows/history_window.py`. Calendar years preserve leap-day semantics.
The earlier one-year web-only reduction has been removed. Existing v1 snapshots
and reports are retained unchanged; preparation appends a v2 snapshot instead
of reusing the shorter history. No prompt-side price truncation is introduced.
The v3 publication policy preserves earlier v1/v2 evidence without rewriting it.
More evidence can increase AI input tokens when the owner authorizes research;
free market-data acquisition does not mean free model processing.

This establishes price-history window parity, **not full CLI analysis parity**.
Both paths now use stockstats over the full supplied history. The web's tools
read only immutable snapshots, expose explicit indicator warmup, page any stored
candle/indicator window, and compute calendar returns with named endpoints.
The chart in a new report is pinned to that run's snapshot, never today's feed.
The v4 acquisition contract writes v1.1 bars with `session_date`; `timestamp`
remains the close instant. Old v1.0 payloads remain readable and labels remain
unknown rather than inferred for an unrecognized source. No historical bytes
are rewritten. Financials, social and macro still require eligible
snapshots; automatic acquisition of those feeds is not implemented here. Never describe a
price-only report as a full replication of the original multi-source pipeline.
Completeness must follow each source's original contract, not an arbitrary
uniform lookback or a speed/token-driven reduction. Preserve point-in-time and
quality checks when integrating the remaining capabilities.

## Supported identities

Exact existing bootstrap identities only: AAPL, SPY, QQQ, ^GSPC, ^NDX, BTC-USD,
ETH-USD. US assets use XNAS/XNYS session closes including early closes and DST;
crypto uses completed UTC days and 365-day annualization. Cash indices stay
reference-only. New catalog entries require an adapter contract update.

NQ/ES preparation is explicitly unsupported: continuous Yahoo symbols alone
do not provide the governed contract/roll evidence. No ETF/index substitution.
Fundamentals, sentiment and FRED evidence still require separately governed
ingestion. Missing research areas are not invented or auto-selected.

## Optional current headlines

The authenticated, CSRF-protected
`POST /api/v1/instruments/{id}/prepare-news` accepts only a catalog identity.
It uses the existing Yahoo/yfinance `Ticker.get_news` path in an isolated
subprocess with a 45-second total deadline and the same single-process
acquisition lock as price preparation. The collector requests a seven-day
publication window; `requested_at`, `retrieved_at`, each article publication
time, vendor, retrieval path and canonical instrument identity are persisted
with immutable content-addressed bytes. A recent owner-readable snapshot can
be reused for 15 minutes after full payload and manifest validation.

An article's publication time does **not** make today's revised article text
historically available. The snapshot `as_of` is retrieval time; it is withheld
from earlier analysis cutoffs. This recent feed is non-exhaustive, not a proof
of all events in the seven-day window. `NO_DATA`, `COVERAGE_GAP`,
`UNAVAILABLE` and `INVALID` batches remain auditable but ineligible for
research; no missing-news result is turned into neutral sentiment. Price and
news selections retain separate analyst roles and freshness checks. Adding
headlines clears paid-AI consent and updates the research cutoff to server
time. Portfolio valuation timestamps stay pinned, so the current-news action
is disabled during portfolio evaluation. NQ/ES automatic news preparation
remains unsupported; no alternate symbol is substituted.

The news action is a single owner click, not the three-check price retry loop.
A 60-second owner/instrument cooldown limits repeated requests. It does not
call a model, create a run or automatically include fundamentals/social/macro
sources. Source coverage must be reviewed before a separate paid-AI consent.

## Failure, concurrency and cost

The response distinguishes `ready`, `no_data`, `stale`, `coverage_gap`,
`invalid`, `unavailable`, `rate_limited` (Yahoo), `cooldown` (local), `busy`, and `unsupported`. Failed
requests publish no snapshot and submit no analysis. Ambiguous Yahoo
missing-price exceptions count as unavailable, not proof of no data.

Each acquisition runs in an isolated subprocess with a 45-second total deadline
and 10-second Yahoo request timeout, one instrument/request. The private API
allows one acquisition at a time and a 60-second owner/instrument retry delay.
The web performs at most three checks after one owner click, with visible
attempt progress and a countdown: 60 seconds before check 2, 120 before check 3,
or the server's longer bounded retry hint. A local cooldown or busy response
counts as a check, not a provider download. Transient source failures, missing
sessions and no-data responses are retried; unsupported instruments, invalid
data and authentication/authorization failures stop immediately. Only the
exhausted result is shown as a final failure, preserving the underlying source
reason across cooldown responses. No infinite polling or automatic AI call.

Cancel or unmount aborts the client request and clears retry timers. An already
received server acquisition may still publish a valid snapshot; cancellation
does not delete it or falsely promise a server-side stop. Each browser request
has a 60-second timeout. Closing/reloading the page stops the sequence; this
short, bounded preparation is not a durable background backfill.
There is no automatic scheduler, fallback provider or bulk backfill.
Disconnects may leave a successfully verified snapshot but never an AI job;
repeating the action reuses current evidence. Process-local concurrency is for
the local single-process deployment, not a multi-replica hosted rate limiter.

This bounded data read is separate from long-running analysis, which continues
to use the durable queue, cancellation and immutable evidence contracts.
If a job says **Waiting to start**, the worker has not claimed it. Start the
authorized local worker with the same env as the API; do not submit duplicates.
See [local startup](local-web-startup.md). Model access and bilingual report
quality require separate, explicitly authorized live verification.
