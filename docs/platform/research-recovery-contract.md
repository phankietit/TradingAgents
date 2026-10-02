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
