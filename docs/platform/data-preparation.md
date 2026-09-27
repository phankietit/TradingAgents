# Current-price preparation in the web

The analysis form now provides **Prepare latest prices** before paid AI consent.
No Yahoo API key or AI call is needed. This is a current price/trend workflow,
not full fundamental, news, macro or historical-vintage research.

## Flow and boundaries

1. Select an instrument and prepare prices. The authenticated, CSRF-protected
   `POST /api/v1/instruments/{id}/prepare-data` accepts no vendor URL or symbol.
2. Reuse a current owner-readable `yfinance.daily.v1` snapshot only after hash
   verification. Otherwise fetch the last year of daily OHLCV through the
   existing yfinance dependency, with adjusted close and no rounding.
3. Validate identity, currency, exchange timezone, finite OHLCV, duplicates,
   complete exchange-session coverage and latest completed session. Exclude
   unfinished sessions and allow one hour after close for publication.
4. Append an immutable `ohlcv.daily` snapshot; never rewrite earlier evidence.
   `as_of` is acquisition completion, **not** the last bar date. Newly retrieved
   adjusted history is not a historical vintage and cannot serve earlier runs.
5. Update the form's research cutoff to server time, select the price source,
   clear AI consent, and rediscover eligibility. Owner freshness limits remain
   unchanged. Portfolio valuation timestamps are never moved by this action.
6. Separately authorize AI and submit the durable analysis job. A configured
   worker processes it; the API never runs the model inline or starts a worker.

## Supported identities

Exact existing bootstrap identities only: AAPL, SPY, QQQ, ^GSPC, ^NDX, BTC-USD,
ETH-USD. US assets use XNAS/XNYS session closes including early closes and DST;
crypto uses completed UTC days and 365-day annualization. Cash indices stay
reference-only. New catalog entries require an adapter contract update.

NQ/ES preparation is explicitly unsupported: continuous Yahoo symbols alone
do not provide the governed contract/roll evidence. No ETF/index substitution.
News, fundamentals, sentiment and FRED evidence still require separately
approved ingestion. Missing research areas are not invented or auto-selected.

## Failure, concurrency and cost

The response distinguishes `ready`, `no_data`, `stale`, `coverage_gap`,
`invalid`, `unavailable`, `rate_limited`, `busy`, and `unsupported`. Failed
requests publish no snapshot and submit no analysis. Ambiguous Yahoo
missing-price exceptions count as unavailable, not proof of no data.

Each acquisition runs in an isolated subprocess with a 45-second total deadline
and 10-second Yahoo request timeout, one instrument/request. The private API
allows one acquisition at a time and a 60-second owner/instrument retry delay.
There is no automatic scheduler, retry loop, fallback provider or bulk backfill.
Disconnects may leave a successfully verified snapshot but never an AI job;
repeating the action reuses current evidence. Process-local concurrency is for
the local single-process deployment, not a multi-replica hosted rate limiter.

This bounded data read is separate from long-running analysis, which continues
to use the durable queue, cancellation and immutable evidence contracts.
If a job says **Waiting to start**, the worker has not claimed it. Start the
authorized local worker with the same env as the API; do not submit duplicates.
See [local startup](local-web-startup.md). Model access and bilingual report
quality require separate, explicitly authorized live verification.
