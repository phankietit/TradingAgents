# Analysis engine adapter

## Canonical report compilation and publication

Snapshot research retains every configured analyst, bull/bear debate, research
manager, trader and risk debate. The final manager produces an unpublished
English draft with `{{QA}}`-style quantity bindings to run-bound snapshot facts.
Application code resolves and rounds those facts; the model does not supply their
values. The compiler preserves conclusions and exact material-claim citations.
Unknown, duplicate, unused or unbound quantities fail closed. No historical report
is rewritten. Drafts remain private audit evidence, not approval payloads.

A dedicated Financial validation stage reviews financial meaning (including
percentage denominators, return/drawdown terminology and source availability),
then applies deterministic source, numeric, authority and claim-coverage checks.
It uses one review call with at most one schema-format repair; it does not rerun
the preceding debate. A failed upstream schema repair also withholds readiness.
Only accepted canonical output reaches protected bilingual presentation. Translation
uses unique quantity anchors and must restore every anchor exactly once without
introducing digits. Translation failure withholds bilingual readiness; it does not
replace English evidence or rerun the research debate.

Fact calculation version v3 supports closed, no-eval `calc.difference`, `calc.ratio`,
`calc.pct_change`, `calc.abs_pct_change` and `calc.atr_distance` expressions over
existing same-snapshot facts. Units, zero/positive denominator requirements and
indicator warm-up are checked. `window.N.candle.NAME.min|max` and corresponding
indicator windows count observations, not calendar days. No numeric literals,
nested expressions, cross-snapshot operands or invented values are accepted.
These checks establish quantitative reproducibility, not qualitative entailment
or a probability of profit. Human financial review remains required.

Thesis paragraphs, risks and invalidations are source-linked objects in the
unpublished draft. The compiler joins thesis paragraphs and unions only their
supplied source IDs into the historical canonical shape. It never invents source
links or asks the model to repeat the entire report in a second citation array.

For `openai_compatible` on the exact official HTTPS MiniMax API hosts, the client
uses MiniMax wire handling without changing the configured provider, key, model
or URL. `reasoning_split` separates private reasoning from report text, and
reasoning metadata is preserved in memory across tool turns as required by the
[MiniMax API contract](https://platform.minimax.io/docs/api-reference/text-openai-api).
Arbitrary compatible servers do not receive these vendor-specific flags. Raw
reasoning is not added to persisted run events or report artifacts.

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
New reports retain schema-valid `quantitative_references` for audit even when
publication checks reject the decision; they do not grant readiness. Older
artifacts without these references are not reconstructed or rewritten.
Calculation version `snapshot-market-facts-v2` distinguishes indicator distance
relative to price from price distance relative to an indicator, including an
explicit magnitude. Reversing a percentage denominator by changing its sign is
incorrect; the supplied formulas and IDs are not interchangeable.
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
Snapshot-run API requests may explicitly supply `execution_limits` with strict
integer `wall_seconds` (60–7200) and `model_calls` (1–128). The optional contract
is immutable, part of the config hash and job payload, and consumed by the
worker observer. An omitted selection preserves legacy defaults and historical
hashes. Limits cannot be attached to a legacy live-tool run. The authenticated
configuration response exposes defaults and `cooperative_boundaries`, not a
provider health probe or hard mid-request deadline. UI allowance selection and
transport deadline enforcement remain unfinished; no paid run is automatically
authorized by changing this contract.
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
# Canonical report and protected presentation (2026-09-27)

Snapshot Portfolio Manager generation produces an unpublished English draft.
The separate Financial validation node compiles quantity bindings and checks
numeric references, financial amount coverage, authority and exact material-claim
citations against immutable inputs. Its bounded repair receives the rejected
candidate and allowlisted failure codes; it cannot change source data or bypass
the gates. This is separate from the manager's schema-format repair budget.

Percentage bindings now occupy standalone sentence anchors (`{{QA}}.`). The
compiler renders the complete relationship from the verified fact ID: subject,
reference, denominator, sign, unit and rounding. This replaces the previous
pattern-based check of arbitrary percentage prose. Non-percentage bindings
remain inline. The model still supplies all interpretations, opposing arguments,
risks and invalidations; it must not remove a comparison just to satisfy the
format. Unsupported templates or anchors embedded in comparison prose fail
closed. Calendar returns, window drawdown, indicator-relative percentages and
verified `calc.pct_change`/`calc.abs_pct_change` operands are covered.

Exact compiler-owned percentage sentences have deterministic Vietnamese
equivalents and are protected as entire statements during model translation.
Historical free-form reports are not retroactively rewritten. This guarantees
the rendered relationship's numerical meaning, not the surrounding narrative's
entailment or the investment conclusion. Live acceptance of this changed
presentation contract is still UNVERIFIED.

After the complete research/risk graph, the `Report presentation` node translates
the accepted reader-facing report when Vietnamese is requested. Translation is
block-addressed: every supplied paragraph, risk, invalidation and horizon has a
required stable ID. Missing, duplicate, invented or empty blocks fail closed.
The application owns section headings/order, and protected quantities cannot
move to a different block. A bounded editorial check rejects reproduced literal
calques; it is not a claim of universal translation fidelity. Application-owned
anchors protect every digit (prices, percentages, dates, indicator periods and
horizons). Missing, duplicate, unknown anchors or new numeric tokens reject the
translation. Restoration is deterministic and the existing EN/VI parity gate
still applies. Translation uses the same configured deep model, one structured
attempt plus at most one repair, with normal usage/cancellation accounting. This
adds up to two model calls; it never restarts earlier research solely for language.

Missing translation withholds bilingual/VI publication. Canonical evidence and
diagnostics remain inspectable. Historical reports and the legacy CLI contract
are unchanged. Numeric identity/provenance checks do not prove qualitative
entailment, translation fidelity, profitability or approval; human review remains.

For MiniMax function-calling schemas, a response containing no tool calls may
already be one complete JSON object. The client now validates that entire
content against the same Pydantic schema before spending the existing repair
attempt. It never extracts a JSON fragment from prose or reasoning, hides a
failed tool call, or accepts a known truncated/refused response. Explicit
`include_raw=True` callers retain the original LangChain envelope contract.
Initial text parsing and format repair share strict object parsing (including
duplicate-field and non-JSON constant rejection). All publication callbacks
still run. Wire-mocked tests verify one request/one usage record on valid input
and no more than the original two attempts on rejection. Live cost savings
remain UNVERIFIED; this does not change provider, model, thinking configuration,
tool-choice support, graph roles or readiness requirements.

## Non-price acquisition status

The web has separate current-price and optional current-news preparation actions.
Existing readers for social snapshots do not establish automatic acquisition.
An owner-approved AAPL-only `prepare-fundamentals` path now uses the existing
SEC EDGAR adapter to save filed-date-aware US GAAP facts as a distinct immutable
`fundamentals` snapshot. It leaves CLI defaults unchanged. The analyst receives
a compact latest-by-metric view with a read-only full-history paging tool;
final quantitative bindings can resolve exact SEC fact IDs and units. The
report adds an application-owned bilingual coverage warning. This is not a
complete company profile, live valuation, or historical vintage, and other
equities/ETFs/crypto/references do not gain company-financial acquisition.
`dataflows.platform_news.collect_yahoo_news` is explicitly wired
to owner-scoped `prepare-news` and immutable news snapshot persistence.
It returns structured articles with instrument identity, requested window,
publication timestamps, retrieval timestamp, URL and publisher. Source text is
untrusted evidence. No article URL is fetched by this collector.

The collector has no historical as-of argument: today's article contents cannot
be backdated using their original publication dates. It distinguishes empty
reachable feeds, unavailable requests, malformed records and out-of-window
coverage. A malformed record prevents the batch being marked usable. An OK
result means eligible articles exist, not exhaustive coverage of the requested
week. The downstream run retains `recent_feed_not_exhaustive`, selects a cutoff
no earlier than retrieval, and adds a deterministic bilingual coverage notice
to the report. Social and macro acquisition remain separate unfinished work;
the news adapter must not cause them to be labeled available.
