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
the calendar itself. Owner-scoped persisted snapshot resolution and a verified
calendar integration remain required before the evaluation can claim full
historical reproducibility.

`REVIEW` decisions are counted but never scored. Outcomes must become knowable
after the decision `as_of` and no later than the evaluation clock. Duplicate
decisions/outcome cells and non-finite returns are rejected. The result reports directional
decision quality only. It has no cash ledger, fills, fees, slippage, turnover,
or position carry-forward and therefore explicitly cannot claim portfolio
return, Sharpe, drawdown, or portfolio backtest performance.
