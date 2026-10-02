# R08 snapshot graph recovery — implementation contract

Status: UNVERIFIED for production recovery. This contract does not enable a
retry endpoint, authorize a paid call, raise an existing allowance or make a
working note an approvable decision. Original CLI checkpoint behavior remains
separate and unchanged.

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
