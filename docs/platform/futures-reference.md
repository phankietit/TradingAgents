# NQ And ES Reference Pipeline

PLAN-023 adds reference-only NQ/ES context. It does not add futures trading,
contract sizing, margin, leverage, liquidation, broker credentials, or order
submission.

The pipeline requires `NQ=F` or `ES=F` instruments marked `reference_only`,
`America/Chicago`, and `CME_Equity`. It links an immutable continuous price
snapshot to observed active/next contract identity, expiry and last-trade
metadata, explicit roll events, and CME overnight/RTH windows.

Continuous-series adjustment is never implicit. Each roll states unadjusted,
backward difference, or backward ratio semantics and its observed/effective
times. Contract and calendar metadata must have been observable by analysis
`as_of`; future schedules may be retained only when already published.

Gaps are explicit evidence:

- the daily maintenance break is `session_break/expected`;
- an unadjusted roll discontinuity may be `roll_transition/preserved`;
- a missing vendor bar is `missing_bar/unavailable` and degrades the snapshot
  to `COVERAGE_GAP`.

The pipeline never forward-fills or invents a futures price. Payloads are
content-addressed, owner-scoped, and linked to the source continuous-series
snapshot. NQ/ES remain market-regime references for the MVP; QQQ/SPY are the
investable proxies.
