# Historical decision evaluation v2

Historical evaluation v2 scores independent, settled decision cells. The artifact records the universe, period,
benchmark, configuration hash, outcome snapshot IDs/hashes, and a canonical
input hash. Caller-supplied returns remain `reproducible=False`: IDs and a
claimed hash alone are not source replay evidence. Canonical input order and
content-derived evaluation IDs make identical inputs deterministic.

`snapshot_outcome` derives returns from hash-verified daily asset and benchmark
series with matching currency/price basis. It rejects invalid source windows,
future retrieval, non-OK quality, missing expected closes and identity mismatch.
Entry must be strictly after the decision. Explicit ordered session closes must
come from the applicable exchange/24x7 calendar; this helper does not validate
the calendar itself. `calendar_snapshot_outcome` constructs the expected window
with pinned `exchange-calendars==4.12`, verifies matching asset/benchmark session
closes, and binds both exact calendar-window hashes into the outcome hash.
XNYS/XNAS, UTC 24/7 and reference-only CME_Equity (CMES) are supported;
unsupported calendar identities fail closed. Entry is the first settled close
strictly after the decision, followed by the configured holding sessions.
No missing bar is padded and no date-only bar is silently relabeled as an
exchange close. Tests cover holidays, early closes, DST and crypto weekends.
See the [calendar library documentation](https://github.com/gerrymanoim/exchange_calendars/blob/master/README.md).

Owner-scoped persisted snapshot/calendar receipt replay remains required before
the evaluation can claim full historical reproducibility.

`REVIEW` decisions are counted but never scored. Outcomes must become knowable
after the decision `as_of` and no later than the evaluation clock. Duplicate
decisions/outcome cells and non-finite returns are rejected. The result reports directional
decision quality only. It has no cash ledger, fills, fees, slippage, turnover,
or position carry-forward and therefore explicitly cannot claim portfolio
return, Sharpe, drawdown, or portfolio backtest performance.
