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

For runs without snapshot inputs, the handler preserves legacy research but marks source
attestation `UNVERIFIED` and the candidate `REVIEW` with no target weight.
Legacy graph tools do not yet attest all reads to immutable run snapshots;
the handler does not fabricate claim links from a list of available snapshots.
Lease renewal uses a separate short-lived session every third of the lease.
Report/candidate publication fences the current lease and cancellation status
inside its write transaction. A stale worker cannot publish or fail a job that
has been reclaimed by another worker. Synchronous model calls are not forcibly
terminated on cancellation; their result is withheld at publication.

## Snapshot-only graph execution

An `AnalysisRequest.snapshot_context` selects tool-free analyst nodes while
reusing the existing research/trader/risk/Portfolio Manager workflow. Context
must cover exactly the selected profile analysts with nonempty JSON snapshots;
input hashes, instrument identity, OK quality and source/retrieval eligibility
are checked before model invocation. A bounded input size prevents unbounded
snapshot prompt expansion. `load_snapshot_context` additionally resolves only
owner-readable artifacts already listed in the run manifest.

The snapshot path never constructs legacy tool nodes, reads/settles memory,
resolves a live vendor identity, or writes legacy ticker logs/checkpoints.
Its model clients are unbound to tools; analyst tool-call responses are errors.
Real graph fixture tests cover the full debate/manager path with forbidden
legacy hooks. They are offline evidence, not live-provider validation.

The authenticated run API accepts optional `decision_inputs` containing
`snapshots_by_analyst` and explicit `source_max_age_seconds` for every role.
Snapshot IDs and inputs are immutable across run lifecycle transitions.
The worker loads owner-scoped bytes and uses the snapshot-only graph path.
Portfolio Manager `evidence_claims` must cover the exact thesis and every risk
and invalidation condition, using only snapshots supplied to its analysts.
Missing/unknown/duplicate source links produce REVIEW, not invented citations.

Optional portfolio proposals supply `portfolio_snapshot_id`, a policy ID and
version, an owner-requested target weight, and risk snapshot IDs together.
The worker passes persisted holdings as narrative context, recomputes all risk
checks and writes evidence/report/candidate in one fenced transaction.
Only complete eligible narrative/evidence and passing deterministic checks can
yield `READY_FOR_APPROVAL`; approval still requires a separate owner event.
Reference profiles remain non-investable. Source binding proves provenance,
not that every model inference is correct. Worker command wiring and live
provider evidence remain separate gates.
