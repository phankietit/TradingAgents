# R08 snapshot graph recovery — implementation contract

Status: UNVERIFIED for production recovery. This contract does not enable a
retry endpoint, authorize a paid call, raise an existing allowance or make a
working note an approvable decision. Original CLI checkpoint behavior remains
separate and unchanged.

### Internal original-context transfer (2026-10-03)

`SnapshotRecordingInputs` is an explicit private JSON envelope for trusted
original run/owner/book/policy/risk context. It has no callable, SDK, database,
lease, or credential field and does not accept browser consent. Its bounded
4 MB payload is revalidated in the parent and child; unknown/duplicate fields,
nonfinite JSON, wrong owner/source/book identity and policy credential keys or
non-JSON objects fail with fixed diagnostics. It transfers no completed/error
run and does not load checkpoint history. Private context is not logged/repr;
source prose remains data, not universally secret-scanned content.

An explicitly configured supervisor can now select the exact original
AnalysisEngine only with this context and a complete matching codec/thread/
parent commit bridge. The child constructs SnapshotRecorder with the original
context and bridge commit; actual graph/client fingerprint and original parent
allowance must still pass before invocation. Default worker/CLI configuration
and factory capability are unchanged. Request/source validation happens before
spawn; database and commit authority stay in the parent. Internal context is
not authenticated DB loading, full transport attestation or owner permission.

Local context and child-construction unit tests do not establish actual-engine
native-spawn acceptance. The subsequent `test_native_recorder_spawn.py` fixture
now runs the exact production child, AnalysisEngine, SnapshotRecorder and native
graph inside a real spawned process. A test bootstrap installs synthetic SDK
responses/network refusal; it does not replace engine/graph/propagate/graph.invoke or
fingerprint/allowance guards. Four roles and two debate/risk rounds in EN, VI,
bilingual and invalid VI match baseline prompt/model/stage traces and published
result fields. Parent-only commits reopen restricted bytes in disposable SQLite,
with child reaping and actual SDK cleanup checked. Synthetic callbacks do not
prove provider usage/admission accounting, live finance or transport attestation.

New-child restore, retained accounting, explicit consent/API/UI and live
financial/editorial acceptance remain UNVERIFIED. Default worker recorder/
resume remains disabled; this fixture grants no paid retry or owner consent.

The subsequent callback-enabled mode keeps the real NormalizedChatOpenAI
`invoke`/LangChain start/end lifecycle, replacing only provider generation and
schema binding with synthetic responses. No callbacks are manually injected.
Parent logical starts/completions and synthetic token counters match an actual-
SDK uninterrupted baseline across the same four language/translation cases.
A one-call fixture allowance stops the next admission and retains the first
usage event/checkpoints; it does not raise any product risk or run limit.
These observations validate local callback plumbing, not vendor usage truth,
hidden SDK request attempts, costs or a durable cross-attempt accounting ledger.
Synthetic `reported` counters must not be presented as live-provider evidence.

### Pre-admission usage reservations

The observer now emits the existing cumulative `model.usage` event after atomic
reservation and before returning model-start admission, then rechecks the same
clock/cancellation/lease boundary. The web worker's existing fenced append-only
event transaction commits before that return; no new table/event type is needed.
Failed emit or expired boundary cannot grant admission. Completion/error events
also include observed elapsed seconds and original limits. No prompt, model
reasoning, credential or raw error crosses the event payload.

`reported` now requires admitted, completed and usage-reported logical call
counts to match; a new outstanding reservation makes status `incomplete` even
when earlier calls were reported. SQLite reopen fixtures retain owner/run/
attempt-bound reservations and original limits before completion, including
native-spawn callback admission/completion events. This is not a cross-attempt
ledger or restore permission. Elapsed is a lower-bound observation, not an exact
crash duration; unknown hidden SDK attempts and provider cost remain unknown.
Existing general event transactions do not establish a hard end-to-end database
deadline. Durable aggregation/unknown-duration policy, explicit consent and
new-child restore remain required before enabling recovery.

### Read-only durable accounting aggregation

`accounting.py` reads existing owner/run-scoped append-only events through a
fixed high-water prefix, paging 500 rows at a time and rejecting a prefix over
10,000 events rather than truncating. It requires contiguous ordering, original
execution markers/attempt identity, exact immutable limits, strict logical
counter/status/token semantics and monotonic cumulative counters/elapsed within
each attempt. Latest counters per attempt are summed, never every receipt.
Token totals must be zero without a usage-bearing completion and cannot change
without an additional usage-bearing completion. Aggregate elapsed must remain
finite; finite per-attempt values do not alone prove a valid aggregate.
Malformed evidence produces fixed errors without raw event/DB content; missing
or legacy evidence withholds all totals instead of inventing zero cost.

The result identifies its high-water sequence, observed attempts, logical starts/
completions, unreported started calls, reported token counters and elapsed lower
bound. PASS describes parsed accounting evidence, not financial/production
acceptance or unused allowance. Exact elapsed is always unknown; cumulative
starts across attempts may already exceed the original cap and no fresh cap is
granted. No cost, remaining seconds, consent or publication authority is derived.

SQLite reopen, multi-attempt/multi-call, pagination and actual native-spawn
callback/exhaustion fixtures exercise this reader. Authentication of the caller,
transactional consent/high-water recheck, linked continuation identity, exact or
conservatively bounded crash-duration accounting and restoration remain required.
The component does not mutate old rows, reset budget, expose a browser endpoint
or activate worker recovery. General DB read transactions are not hard network/
pool/disk deadlines; PostgreSQL live and concurrent consent remain unverified.

Accounting observations additionally bind original owner/run/config hash and
scalar immutable wall/call limits (including legacy defaults). Internal
`recheck_accounting_evidence` reloads the complete bounded prefix and compares
the complete frozen observation, rejecting another owner/run, changed limits,
counter substitution or a newly appended event, even a non-accounting event.
The recheck returns no permission/token. It does not lock a writer or authenticate
browser input and cannot replace a transactional consent/lease fence: another
event may commit after its read. Production dispatch remains disabled.

### Local supervised stop accounting

After the child is confirmed stopped/reaped and the pipe reader is shut down,
the parent closes the original observer and emits one existing model.usage
observation with execution_stopped=True. It includes unchanged counters/limits
and elapsed on the same original monotonic clock, including local cleanup.
No later model callback/admission can use that observer. Stop publication is
subject to the existing lease/cancellation event fence; refusal is suppressed
only to preserve the original result/error, never treated as durable success.
An abrupt parent crash or missing stop append keeps elapsed upper bound unknown.

The strict reader rejects false/non-boolean stop claims, duplicate stop or usage
after stop in the same attempt. Only a bounded prefix containing stop evidence
for every observed attempt yields elapsed_upper_bound; exact_elapsed_known stays
False. This bound is local supervised execution, not the remote provider's
processing/billing duration; unreported usage and cost remain unknown. Legacy
history is not repaired, and this is not a consent or remaining-budget grant.

### Original allowance arithmetic observation

`load_remaining_allowance` loads authoritative accounting itself and accepts no
caller-provided cap, elapsed, checkpoint or consent. It subtracts every logical
start (including unfinished/failed reservations) across attempts from the
original call cap. Only a known local elapsed upper bound can produce remaining
seconds; legacy/missing accounting yields unknown values, not a new allowance.
A known exhausted call cap or elapsed lower bound blocks even if stop evidence
is missing. Values cannot become negative or increase the original limits.

PASS means bounded arithmetic only, not admission, financial acceptance or
permission to continue. The frozen private observation retains the complete
accounting/high-water/original identity and unknown provider usage, and has no
cost/refund/consent token. Transactional recheck/owner consent, linked execution,
trusted checkpoint restoration and original-budget enforcement in the supervisor
remain required before enablement. No reader mutates history or invokes models.

### Internal retained observer enforcement

`build_retained_observer` reloads original owner/run allowance evidence, requires
an exact full expected accounting observation and refuses unknown/stale/exhausted
history. Original wall/call limits stay unchanged. The parent observer subtracts
prior elapsed upper bound and prior logical starts at every boundary/admission;
its new attempt clock, counters and event elapsed remain attempt-local. This
avoids both fresh-budget replay and double-counting prior accounting on reload.
The existing supervisor uses the same observer for deadline/cancellation checks.

This internal builder is not authenticated transactional consent, an execution
identity or checkpoint restoration. Its read comparison cannot fence later
writers; a future caller must supply the reviewed consent/lease transaction and
linked execution before dispatch. Default worker/CLI/API do not call it. Tests
exercise synthetic callbacks and a simple spawned fixture engine, not original
graph recovery or financial/live/provider acceptance. No history is rewritten.

## Implemented codec prerequisite

`tradingagents/platform/analysis/checkpoint_codec.py` provides an unused-by-worker
JSON envelope component. It preserves native checkpoint-v4 channel versions,
versions_seen, control channels, metadata and pending-write order/task identity.
Only reviewed snapshot fields are accepted; raw messages are removed from
current/start/pending values before encoding and rejected on decoding. Unknown
fields, CLI memory, non-research authority, arbitrary typed objects, nonfinite
versions, duplicate JSON keys, incompatible formats and oversized data fail
closed with a fixed non-content diagnostic. Limits are 16 MiB per envelope and
one million characters per text field; nothing is truncated.

The caller must supply a digest and original graph-node allowlist. Digest
equality is checked, but this component does not construct a full fingerprint,
authenticate an owner, cryptographically attest content or validate source
freshness. It is not an ArtifactService reader, persistent saver or auto-retry
path. Production worker/CLI behavior remains unchanged.

Native fixture acceptance now includes JSON restoration into a fresh saver for
all 17 boundaries, four source roles, two debate/risk rounds, EN/VI/bilingual and
invalid translation. Both the latest checkpoint and a preceding checkpoint with
completed pending writes preserve full prompt/call/stage trace and all non-message
AnalysisResult fields. All source checkpoint versions are encoded and inspected;
no raw message/reasoning objects enter the resulting JSON. Invalid VI remains
unavailable rather than becoming a decision. These are synthetic in-process
mechanics, not separate-process/crash/live financial acceptance or durable storage.

The fixture loader groups writes by task before installing them; installing
one channel per put_writes call can reuse write indices and lose completed
outputs. Original debate nodes may omit judge_decision until the manager runs;
the codec preserves that absence without inventing a default or changing nodes.

Next integration must not reuse API `_config_hash` as the complete research
fingerprint: it presently binds declared models/roles/prompt/language/allowance,
not verified source contents, backend options or actual graph configuration.
Keep its existing history/idempotency semantics unchanged. Construct the new
fingerprint separately from validated run/request/source/portfolio/policy data
and effective runtime identity/options; never persist or log credentials.
Native LangGraph durability defaults to async; the future parent commit/ack
contract must explicitly verify synchronous persistence before node advance,
including pending writes, rather than assume checkpoint callbacks are synchronous.

## Verified prerequisite

### Fingerprint construction prerequisite

`recovery_fingerprint.py` now constructs a separate versioned digest without
changing API config_hash or stored history. It revalidates nested run/request/
snapshot models, exact owner/run/instrument/as-of/ordered-role identities,
freshness limits and source IDs; existing snapshot reports recheck payload
hashes and point-in-time eligibility. All source manifests, risk-source hashes,
full portfolio/policy content (not just their labels), rendered book, language,
original allowance, effective graph config/options and analyst plan bind.

It hashes actual package Python source bytes, Python version and all installed
distribution versions, so uncommitted code/dependency changes invalidate
recovery. Filesystem output/cache/memory paths are omitted for relocation;
snapshot mode does not consume CLI memory. Unknown configuration keys and
credential-bearing URL/config fields fail closed; no SDK/network call occurs,
and only a digest is returned. Source symlinks outside the package are rejected.

ResolvedClientBinding is mandatory and has no default for effective non-secret
SDK options hashes. The future trusted worker must derive/attest endpoint,
client implementation and these hashes from actual initialized client settings;
the current builder does not verify this supplied descriptor. It also cannot
authenticate owner_id, attest owner-readable DB/artifact loading, compare every
rendered position to DB instrument mappings, replay all risk-series semantics,
grant consent or validate a lease. These remain existing/future worker obligations.
Do not expose the builder as a browser-controlled recovery authority. Hash
equality is not a signature or an authorization to spend/publish.

`client_binding.py` now derives descriptors from actual initialized sync SDK
clients of the exact reviewed OpenAI-compatible classes, including MiniMax.
Endpoint, scalar/per-phase timeout, retries, wire model options and LangChain
response/stream settings bind without a network/model call or SDK auth-header
inspection. Declared custom headers/query/transports, unknown classes and
credential-bearing options fail closed with fixed errors. The builder accepts
only the SDK's precise appended trailing slash alongside an unchanged configured
endpoint; host/path/query/credential changes are not normalized away.

This adapter is not wired to the worker and is not a complete transport
attestation: post-construction SDK/header/HTTP-stack mutations, async execution,
other provider SDKs and trusted construction provenance remain unverified.
These must be reviewed before enabling recovery; no caller-supplied descriptor
or hash is sufficient permission to continue a paid run.

`build_initialized_graph_fingerprint` now composes that adapter with original
source/run/book validation using the actual exact TradingAgentsGraph instance.
It requires snapshot mode, exact effective config/selected roles, actual LLM
model names matching the run, and the digest of snapshot reports supplied at
graph construction matching revalidated original readers. Even a valid source
with recalculated hash cannot be substituted after graph construction. It
derives descriptors internally, not from supplied browser/model bindings.
Only the reader digest is retained by the graph, not a second raw source copy.
Errors use a fixed diagnostic; no model/network invocation is performed.

This is a mismatch guard, not full trusted-factory, graph-closure/SDK-header/
transport-mutation attestation or authenticated DB loading. Default engine/
supervisor/worker do not select it or enable recovery. Original owner consent,
allowance/usage accounting and new-child restore remain mandatory next gates.

### Internal AnalysisEngine recorder selection

`recording.py` supplies a private SnapshotRecorder carrying original run/owner,
expected full fingerprint, book/policy/risk context and a trusted fenced commit
callback. Its repr excludes fields. AnalysisEngine accepts only this exact
internal type with the original graph factory; arbitrary factories/recorders
and non-snapshot requests fail before graph invocation. After actual graph
construction it recomputes initialized identity and requires an exact match,
then constructs restricted codec/committed saver and canonical run-thread for
the native synchronous snapshot hook. No fallback after mismatch is permitted.

It requires the existing exact ResearchObserver with original stored (or legacy
default) limits and checks remaining allowance without creating a new observer
or resetting its start. Cancellation/exhaustion retain original classifications.
Saver ACK validation now independently requires exact UUID and positive integer
sequence (not bool/float/string), matching the parent bridge boundary.

This is direct internal engine recording, not supervised child capability or
worker enablement. Existing worker does not construct SnapshotRecorder and no
API accepts its fields. Native engine wiring tests use real SDK initialization
with an explicit invocation spy, not full native/live financial acceptance.
Trusted parent original-context transfer/attestation and observer adaptation,
new-child restore, durable retained accounting and explicit owner continuation
still require implementation and acceptance. Keep execution_started fencing;
this context cannot authorize a replay, enlarge allowance or mutate history.

Actual engine/recorder native fixtures now supplement the wiring spy. They
initialize real reviewed SDK clients with synthetic credentials but replace
only model response methods; propagate_snapshots/invoke and recording prepare
are not spied or replaced. Four analysts, two debate/risk rounds and EN/VI/
bilingual/invalid VI match the unrecorded baseline's full prompt/model-call/
stage sequence and all non-message result fields. Lease-fenced SQLite commits
are reopened and strict-decoded with matching owner/run/fingerprint, contiguous
sequence and no credential/private reasoning marker or nonempty message values.
Native channel-version metadata may still name messages; it is required for
native fidelity and is not message content. A separate original fixture run
remains unchanged. Original recorder observer/start is preserved.
Fixture construction uses exactly two initialized SDK instances for the engine;
both sync/async clients are explicitly closed and asserted closed after use.

This is same-process native integration with synthetic responses, not live
provider/semantic/MT proof or supervised worker activation/new-child restore.
Synthetic methods bypass SDK callback accounting, so usage is explicitly
incomplete and does not prove admission counts or billing. Remaining parent
construction/observer transfer, retained accounting/consent and recovery gates
are not replaced by these tests.

### Parent-owned recorder allowance proof

SnapshotRecorder.prepare now supports either the existing exact ResearchObserver
or the exact private checkpoint-enabled child bridge. The latter sends a
recording_allowance RPC with only original wall/call limits, expected fingerprint
and run-thread. Parent rejects unknown fields, non-int limits (including bool),
non-string identity or any mismatch with its selected checkpoint identity and
original observer limits. It checks remaining_seconds on its original clock,
retaining cancellation/lease/deadline checks, before sending the exact True ACK.
Child refuses any other ACK and never starts a new local budget/observer clock.
Disabled bridge cannot send this request. RPC serializes through the existing
send/ACK lock; model admission still uses original parent observer.

Spawn fixtures cover success, larger limits, boolean limit, changed fingerprint/
thread, extra private marker and expired original budget. Invalid requests admit
zero models/commits and spawned children are confirmed stopped; success preserves
start and original limits and accounts for one synthetic model callback. Direct
recorder unit cases exercise bridge selection/True-only ACK without claiming a
live parent proof from their fake pipe.

No original run/book/source context is transferred by this RPC and it is not
owner consent, an allowance grant or complete client/transport attestation.
Default engine/worker remain unable to select supervised recorder capability;
trusted context transfer, native recorder through spawn, new-child restore,
retained accounting and API/UI continuation remain open. No history is mutated.

### Private persistence prerequisite

`checkpoint_store.py` and migration `0011_research_checkpoints` provide a
separate private table, not an ArtifactKind or generic reader endpoint. The
parent commits bounded validated codec bytes with owner/run/thread/job identity,
checkpoint ID, content hash and monotonic sequence. Identical bytes are
idempotent; pending-write revisions append without modifying earlier rows.
The existing publication_session locks/renews the job and rejects cancellation
or lease loss in the same transaction. A success receipt is returned only after
that transaction exits; rollback produces no ACK. Latest loading rechecks hash,
fingerprint, codec and checkpoint ID and never falls back to an older row after
incompatibility/corruption. Missing history remains missing, not backfilled.

Only disposable SQLite fixtures have exercised upgrade/downgrade and reopen;
no private runtime DB was migrated. PostgreSQL/concurrent writers, a native
checkpointer, child bridge/commit-ack, cross-process crash boundaries, retained
usage accounting and explicit continuation consent remain unverified. This
internal store is not invoked by production worker/CLI/API and cannot authorize
recovery. A trusted worker must derive the fingerprint and authentic owner
context before using it, and preserve execution_started/no-blind-replay fences.

### Native saver / sync durability prerequisite

`checkpoint_saver.py` wraps the original ephemeral InMemorySaver for native
checkpoint and pending-write fidelity. After each put/put_writes it encodes the
complete addressed tuple with the restricted codec and synchronously requires
a commit receipt matching those exact bytes. Failed/ambiguous ACK poisons the
saver; later reads/list/writes fail closed rather than retry implicitly. Only
native thread/ns/checkpoint identifiers address persistence: invocation-only
task helpers do not enter the envelope. Codec state/control/metadata allowlists
remain unchanged. Raw messages are retained only in ephemeral native memory;
they do not enter commit bytes.

The caller MUST invoke the compiled native graph with durability="sync".
Blocking put alone does not fence advancement under default async durability.
A native scheduler fixture waits on a deliberately delayed ACK before the next
node can run. Full original-graph fixtures cover all 17 interruption boundaries,
two debate/risk rounds, all four analyst roles, EN/VI/bilingual and invalid VI,
current JSON and completed pending-write restoration. Bytes are reopened from
the actual SQLite store and restored into a fresh native saver; model-call/
prompt/stage traces and non-message results equal uninterrupted execution.

This remains a same-process synthetic integration, not production or financial
acceptance. The worker/supervisor does not instantiate it yet. Parent bridge,
write/ACK crash boundaries in separate processes, trusted client construction,
consent/retained accounting, PostgreSQL/concurrency and live tests remain open.
No existing owner history is backfilled or migrated and no allowance reset is
authorized by a readable checkpoint.

### Opt-in supervised checkpoint RPC

The supervisor now accepts an internal complete tuple of reviewed codec,
canonical run-thread ID, parent-only commit callback and explicitly capable
engine factory. Missing/partial or unsupported setup is rejected before spawn.
Only fingerprint/thread identity is passed to child: no DB, job lease or
callback object crosses. The child committed saver calls the serialized bridge;
parent revalidates restricted JSON/thread, commits and validates exact receipt
type/UUID/positive integer sequence/hash, then rechecks cancellation/deadline
before ACK. A result with no checkpoint commits is rejected when opted in.
Raw DB/callback diagnostics do not cross as public errors.

Fixture-only native engine wiring exercises all 14 original stages with this
RPC and parent SQLite commits in EN/VI/bilingual/invalid VI. Separate-process
fixtures kill the parent before commit and after durable commit but before ACK:
waiting child stops executing through the existing parent guard; zero/one row
respectively remains, without automatic replay. A terminal zombie is not
described as reaped. Callback exception, malformed bytes, invalid ACK and
post-commit cancellation/lease/deadline prevent any subsequent model admission.

Default AnalysisEngine is intentionally not declared capable and default worker
does not select the opt-in path. Production graph hook/trusted client identity,
restore in a new supervised child, linked immutable accounting/consent/API/UI,
PostgreSQL/concurrency and bounded parent DB-lock timeout remain open. These
tests do not prove a hard deadline while a synchronous parent DB callback is
itself blocked, or provider billing determinism. No private DB migration,
automatic resume, execution_started bypass or allowance reset is enabled.

### Transaction-local lock-wait budget

PrivateCheckpointStore commits now require a positive local lock-wait budget,
default five seconds; internal callers can supply a shorter value. Generic
Database/JobExecutionContext publication sessions retain their existing behavior
when no budget is requested. SQLite checks out a dedicated connection, sets
busy_timeout, then restores its original value before pool return (invalidates
the connection if restoration fails). After a failed COMMIT it explicitly
rolls back this context's DBAPI connection too: SQLAlchemy can have deactivated
its transaction while SQLite still holds one, and resetting timeout first can
otherwise retry the failed COMMIT with a longer wait. This rollback affects
only uncommitted work in the task-owned transaction, not historical records.

PostgreSQL sets transaction-local lock_timeout and statement_timeout through
parameterized set_config; no engine/global settings change. That path still
needs actual PostgreSQL evidence. SQLAlchemy DB failures are converted to a
fixed CheckpointDatabaseError; bridge refuses ACK and does not enter a second
unbounded DB-backed lease/cancel query after this known DB failure.

Real SQLite writer lock and commit lock fixtures prove bounded refusal, no
checkpoint row/ACK, restored pool settings and a later successful explicit
commit after releasing the fixture lock. This is not a total deadline: limits
apply per busy operation/statement, not pool checkout, connect/pre-ping, driver
network read, disk stall or the sum of multiple statements. Production integration
must cap the requested budget to remaining owner allowance, retain post-commit
checks and prove the outstanding I/O/total-deadline gates before readiness.
No provider/model timeout, risk limit, owner DB migration or resume changes.

Full package/dependency invalidation is conservative: a new machine must restore
the compatible runtime, not silently waive mismatches. Missing versus flat book
remains distinct; an exhausted run's limits cannot be changed by hashing a new
value. An authorized continuation needs the separately governed linked execution
identity and retained accounting required below. No resume endpoint is enabled.

Source `60ef7e2c4b2ec04d51d9b564dcfeda5f9432d44a` characterizes the native graph
with synthetic models. Seventeen interruption boundaries cover all four analyst
and message-clear nodes, researchers/managers/trader/risk nodes and financial
validation. Two debate/risk rounds and bilingual presentation remain enabled.
Removing the current message channel and continuing the original compiled
workflow preserves all remaining prompts, complete model-call sequence, stage
sequence and the final non-message AnalysisResult versus uninterrupted execution.

The fixture uses InMemorySaver, retains earlier in-memory checkpoint versions,
and performs a manual update_state. It is NOT a safe durable serializer, crash
test, ownership gate, checkpoint fingerprint or production resume implementation.
Only messages are excluded from final-result equality; all decision, evidence,
validation, diagnostics and localized fields must match. Synthetic coverage is
not actual social/news/fundamentals coverage or financial acceptance.

The first fixture attempt failed because continuation happened outside
TradingAgentsGraph.config_scope. Restoring the same scope fixed the mismatch.
Recovery must therefore reconstruct both graph configuration and invocation
scope; persisting state alone is insufficient.

## Required production boundary

### Snapshot graph recording hook

`TradingAgentsGraph.propagate_snapshots` accepts an internal paired
`checkpoint_saver`/`checkpoint_thread_id` setup. Saver must implement native
BaseCheckpointSaver and thread must be a canonical UUID; partial/invalid setup
is rejected before compile/invoke. It compiles the original workflow locally
and invokes with `durability="sync"`, retaining callbacks/config_scope, snapshot
state, rounds and validation/presentation. It never replaces the instance graph
on success or failure and never accesses the separate CLI checkpoint path.
Default invocation has no new saver/thread/durability option.

Native supervised recording fixtures now exercise this production graph hook
instead of patching graph.invoke. The hook is not a trusted-client construction
mechanism or checkpoint loader: callers remain responsible for authenticated
original context and isolated saver identity. Default AnalysisEngine/worker do
not select it; no resume, consent/accounting route or paid replay is enabled.

1. Preserve the original workflow, reducers, routing, rounds, financial
   validation and presentation. Restore native channel versions, versions_seen,
   routing/control channels and pending writes, not a guessed next-stage list.
   A completed stage may not be replayed just because a worker was lost.
2. Validate a versioned fingerprint before any model admission. Bind owner,
   original run/instrument/as-of, ordered analyst selection, immutable source
   IDs AND verified content hashes, portfolio/policy identity and content,
   provider/model/backend options, effective configuration, prompt/runtime
   identity and graph shape. Never use the CLI ticker/date signature for web.
3. Persist only explicitly reviewed graph fields and control metadata in a
   strictly validated representation. Reject unknown fields or incompatible
   versions, rather than silently dropping them. No raw messages, prompts,
   provider reasoning, tool payloads or executable sizing. All checkpoint
   versions and pending writes need this filter, not only the latest state.
   Do not deserialize persisted pickle or unrestricted typed object payloads.
4. Child sends checkpoint data through the supervised bridge. Parent alone
   validates and commits it under the existing lease/cancellation publication
   fence; acknowledge durable commit before advancing beyond its boundary.
   Failed, partial or ambiguous writes cannot authorize recovery. Private
   checkpoint content must not be exposed through the generic artifact reader.
5. Recovery must be explicit and owner-authorized, not queue auto-replay. Keep
   the execution_started/no-blind-replay fence. Persisted original allowance
   cannot be enlarged or reset. Any separately authorized continuation must
   have its own immutable execution identity/consent, linked checkpoint and
   retained prior elapsed/call/usage records; disclose unknown interrupted
   provider usage and never fabricate a cost or refund.
6. Restore config_scope and original snapshot-only tools, risk/approval gates
   and supervised process. A saved structured draft is still unvalidated.
   Only the existing completed report/decision pair may take model-free
   finalization. Missing checkpoints in historical failures are not backfilled.

## Required acceptance before enablement

Original-context `SnapshotRecorder` optionally accepts restricted bytes; after
actual initialized graph/client fingerprint and original observer allowance
checks, it restores into a fresh committed saver. The paired graph hook uses
`invoke(None)` with original config scope, callbacks and sync durability, not
an inferred stage list. Default invocation remains unchanged. Native recorder
fixtures reopen immutable intermediate rows, compare continuation traces and
full non-message outputs, and check prior rows are unchanged. These are
same-process synthetic tests, not trusted new-child transport, retained-budget
admission, authenticated consent or live financial acceptance. No worker/API
activation is introduced; caller authority remains a separate requirement.

The committed saver has an internal `restore` mechanism for one restricted
codec tuple in a fresh saver. It checks expected thread identity and codec
fingerprint, seeds native checkpoint versions and grouped pending writes through
the native saver, then checks decoded tuple equality (JSON key order is not
scheduler state). It does not republish old checkpoint rows. Failed imports,
occupied targets and repeat imports poison the saver. Original graph fixtures
use this mechanism rather than a bespoke importer for committed checkpoints.
This is not an owner/consent grant, a new-child transport or worker activation;
those requirements below remain open.

- Native uninterrupted versus restored equivalence with real serializer and
  separate process, all four roles, repeated rounds, EN/VI/bilingual paths,
  invalid structured outputs and invalid translation; identical model-call
  traces before/after boundary and final validation/evidence.
- Reject owner/run/source-hash/as-of/provider/model/prompt/config/graph/
  portfolio/policy mismatch before any paid call; reject malformed or oversized
  payloads without truncation or executing serialized data.
- Commit-before-advance, parent/child crash, cancellation and lease loss at
  write/ack boundaries; no old worker publication, duplicate decision or
  detached process. Retain immutable history and accounting uncertainty.
- Explicit API consent/idempotency and UI distinction between initial run,
  stopped attempt, resumable checkpoint and complete report. No invented
  progress, auto-retry or approval of notes.
- Exact-SHA local gates and separately authorized live acceptance. NQ=F remains
  BLOCKED on contract/roll metadata; no substitute asset or provider.

These are open requirements, not a claim that recovery is implemented. R04
source acquisition, live financial/translation quality and operational web
acceptance remain in the full R01–R14 goal.
