# Analysis engine adapter

`AnalysisEngine` is the stable platform boundary around the existing
`TradingAgentsGraph`. It validates an instrument/date/analyst request, creates a
run-scoped graph configuration, and returns the raw research state plus the
narrative rating. The Portfolio Manager also retains its validated structured
payload separately from Markdown. Free-text fallback explicitly clears that
payload; JSON-looking prose is never reparsed as a decision.

The adapter exposes `decision_payload` only when the structured result contains
a valid rating, thesis, confidence, non-empty risks and invalidation conditions.
Legacy outputs missing these additive fields remain readable Markdown but have
no platform decision payload. Confidence is model-reported, not calibrated.
No additional model call is introduced; the existing one-call structured path
and single free-text retry remain. Provider cost/latency are not live-verified.

The Typer CLI and public `TradingAgentsGraph.propagate()` API are unchanged.
The adapter does not calculate target weights, waive policies, approve a
decision, or submit an order. Those remain deterministic and human-approved
stages outside the LLM graph.

Asset profiles are deterministic. Equities may use market, social, news, and
fundamentals analysts; ETFs and reference indices/futures exclude company
fundamentals; BTC and ETH use market/social/news on the crypto path. Reference
instruments remain non-investable context.

`DecisionCandidateFactory` accepts only the strict narrative schema. Unknown
fields such as model-authored target weights, invalid JSON, missing fields, or
ineligible data fail closed to status/rating `REVIEW`. Narrative output never
authorizes portfolio math or approval.

## Durable worker adapter

`platform.jobs.analysis.AnalysisJobHandler` can be registered for
`JobKind.ANALYSIS_RUN` on `JobWorker`. It validates the queued payload against
the owner-scoped run manifest, pins provider/model/analyst inputs from that run,
executes the graph outside database transactions, and writes one immutable
research report plus candidate atomically. Deterministic run-derived IDs allow
a retry after output commit to reuse the result without another model call.
Cancellation and lease validity are checked before execution and publication.

This initial handler preserves useful legacy research, but marks source
attestation `UNVERIFIED` and the candidate `REVIEW` with no target weight.
Legacy graph tools do not yet attest all reads to immutable run snapshots;
the handler does not fabricate claim links from a list of available snapshots.
Snapshot-attested graph execution, evidence/risk orchestration, periodic lease
renewal is now handled by the worker; worker command wiring remains integration
work. Renewal uses a separate short-lived session every third of the lease.
Report/candidate publication fences the current lease and cancellation status
inside its write transaction. A stale worker cannot publish or fail a job that
has been reclaimed by another worker. Synchronous model calls are not forcibly
terminated on cancellation; their result is withheld at publication.
