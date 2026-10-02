# R08 snapshot graph recovery — implementation contract

Status: UNVERIFIED for production recovery. This contract does not enable a
retry endpoint, authorize a paid call, raise an existing allowance or make a
working note an approvable decision. Original CLI checkpoint behavior remains
separate and unchanged.

## Verified prerequisite

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
