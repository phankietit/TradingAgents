# Deterministic risk engine

`RiskEngine` evaluates a proposed target against an explicit, versioned
`PolicyContract`. It checks data quality, tradability, position and asset-class
concentration, gross exposure, turnover, pairwise correlation, and remaining
cash. Every check is blocking and auditable.

There are intentionally no built-in owner risk limits: limits must be supplied
through an approved policy version. LLM narrative is not an input and therefore
cannot waive a failure. Reference indices/futures always fail tradability for a
portfolio proposal.
