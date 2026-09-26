# Analysis engine adapter

`AnalysisEngine` is the stable platform boundary around the existing
`TradingAgentsGraph`. It validates an instrument/date/analyst request, creates a
run-scoped graph configuration, and returns the raw research state plus the
narrative rating.

The Typer CLI and public `TradingAgentsGraph.propagate()` API are unchanged.
The adapter does not calculate target weights, waive policies, approve a
decision, or submit an order. Those remain deterministic and human-approved
stages outside the LLM graph.
