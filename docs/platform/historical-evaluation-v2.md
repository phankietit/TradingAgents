# Historical decision evaluation v2

Historical evaluation v2 scores independent, settled decision cells from
immutable outcome snapshots. The artifact records the universe, period,
benchmark, configuration hash, outcome snapshot IDs/hashes, and a canonical
input hash so the result can be reproduced.

`REVIEW` decisions are counted but never scored. Outcomes must become knowable
after the decision `as_of`, preventing look-ahead. The result reports directional
decision quality only. It has no cash ledger, fills, fees, slippage, turnover,
or position carry-forward and therefore explicitly cannot claim portfolio
return, Sharpe, drawdown, or portfolio backtest performance.
