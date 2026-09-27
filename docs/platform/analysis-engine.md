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
The legacy CLI keeps its structured/plain fallback. Snapshot managers use a
schema aligned with the platform consumer and at most one strict JSON format
repair after a schema/tool-output miss. Transport failures are not formatting
failures. Invalid repairs remain unvalidated text, never a ready decision.
Safe diagnostics contain error types and field locations, not provider payloads.

The Typer CLI and public `TradingAgentsGraph.propagate()` API are unchanged.
The adapter does not calculate target weights, waive policies, approve a
decision, or submit an order. Those remain deterministic and human-approved
stages outside the LLM graph.

Asset profiles are deterministic. Equities may use market, social, news, and
fundamentals analysts; ETFs and reference indices/futures exclude company
fundamentals; BTC and ETH use market/social/news on the crypto path. Reference
instruments remain non-investable context.
Snapshot-only runs retain the same asset-specific prose constraints alongside
canonical metadata; they do not bypass ETF/reference guidance. Structured-call
fallback logs contain exception types only, never provider or validation payloads.
Platform UTC timestamps use the standard `timezone.utc` identity through a
compatibility alias, avoiding Python 3.11-only `datetime.UTC` imports while
retaining the package's declared Python 3.10+ support. Cross-version runtime
verification is a separate CI gate.

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

An `AnalysisRequest.snapshot_context` selects snapshot-bound analyst nodes while
reusing the existing research/trader/risk/Portfolio Manager workflow. Context
must cover exactly the selected profile analysts with nonempty JSON snapshots;
input hashes, instrument identity, OK quality and source/retrieval eligibility
are checked before model invocation. A bounded input size prevents unbounded
snapshot prompt expansion. `load_snapshot_context` additionally resolves only
owner-readable artifacts already listed in the run manifest.

The snapshot path never constructs legacy tool nodes, reads/settles memory,
resolves a live vendor identity, or writes legacy ticker logs/checkpoints.
Market analysts use only the run-bound candle/indicator/return tools. Full
history is pageable without live vendor reads or prompt truncation. Social
analysis retains the original SentimentReport schema with bounded repair.
Unknown tools fail closed; bounded tool-budget and report-format failures are
distinct exception classes. Other graph roles retain their original sequence.
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
not that every model inference is correct. Live provider evidence remains a
separate gate.

Source verification, research-format validity and portfolio approval are
separate states. A completed job can contain an unvalidated research report.
Snapshot facts verify declared numeric references and rounding; known authority
violations and unsupported money/percentage observations withhold a structured
candidate. These checks are not a general semantic proof of qualitative claims.
Human financial review remains required. Bilingual reports have canonical
English fields and saved EN/VI Markdown; numeric tokens must match across
locales. Switching the interface never invokes AI.

Progress comes from actual graph callbacks, not percentages. Each completed or
failed model call appends a cumulative `model.usage` receipt for its attempt;
sum the last receipt per attempt, not every cumulative event. Missing provider
usage is explicitly incomplete; subscription dollar cost is not inferred.
An in-flight provider call can still consume quota after cancellation. Snapshot
runs check a 1800-second wall-time budget at callback boundaries and cap model
starts at 128, with a 600-second provider timeout and one SDK retry by default.
An in-flight synchronous call may exceed the wall-time budget before the next
boundary observes it. Exceeding a budget fails the run,
never shortens the graph and labels it complete. Reports retain allowlisted
analyst/research/trader/debate sections, not raw messages or hidden reasoning.

Web retries currently restart the graph unless its final publication already
committed. The CLI's ticker/date checkpoint is deliberately not reused across
owner-scoped web runs. Mid-graph web resume requires separately fenced,
run/config/source-bound checkpoints; it is not an existing capability.

## Local worker command

After installing the `platform` extra and applying database migrations, set
`TRADINGAGENTS_DATABASE_URL` and `TRADINGAGENTS_ARTIFACT_ROOT` to the same private
database/artifact location as the API. Provider credentials remain server-side.
Run `tradingagents-worker --once` for at most one eligible job, or
`tradingagents-worker` for continuous processing. The module equivalent is
`python -m tradingagents.platform.jobs.runtime --once`.

The command performs no migration and exposes no network listener. Idle polling
is configurable with `--poll-seconds`; SIGINT/SIGTERM stop claiming new jobs
and allow the current call to finish. Runtime cache/reports live below the
configured artifact root. It does not add providers, change policy limits or
submit orders. Use a dedicated local test database for command smoke tests;
`--once` is not a dry run when eligible jobs are present.
