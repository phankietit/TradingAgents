# Derived Factor Service

PLAN-026 derives transparent price factors from immutable normalized time
series. It does not ask an LLM to calculate risk or ranking signals and does not
create portfolio weights, investment recommendations, or orders.

## Formula Contract

- Momentum is `latest / price[n periods ago] - 1` on the series' declared close
  or adjusted-close basis.
- Trend exposes fast-average versus slow-average and latest-price versus
  slow-average ratios.
- Volatility is sample standard deviation of simple returns multiplied by the
  square root of the source series' annualization periods.
- Relative strength is asset cumulative return minus benchmark cumulative
  return over exact aligned timestamps.
- Correlation is the sample correlation of asset and benchmark simple returns
  over exact aligned timestamps. It is `null` when either return series is
  constant.
- Breadth is the deterministic share of members with positive momentum and the
  share above their slow trend.

All window lengths are versioned configuration. Missing history or insufficient
asset/benchmark timestamp overlap fails closed; the service does not pad,
forward-fill, interpolate, or shorten a configured window. Every input must
have `OK` quality and carry its immutable snapshot ID and content hash.

## Reproducibility And Persistence

Inputs are sorted by canonical symbol before calculation. The factor snapshot
stores the complete window configuration, source IDs, benchmark identity,
explicit timestamps, a canonical input hash, per-instrument factors, and
breadth. Identical inputs are independent of caller order and produce the same
snapshot ID. Optional persistence uses an immutable content-addressed,
owner-scoped artifact.
