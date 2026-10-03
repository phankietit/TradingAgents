# Research acceptance checkpoint — 2026-10-03

Latest tested source `c04b23e3bf88a71b594c57fdb7db3b0e07a132f8`: see the
appended **Native portfolio approval and linked lifecycle timing** section. Earlier
incremental evidence and failures below retain their original source scope.
The full private-platform goal remains incomplete; no live-finance or browser
acceptance follows from the local approval gate.

Branch `fix/TA-R01-research-quality`, source
`c705cad32c3e6579c94942d8131ea32f0ac34def`. Private platform candidate remains
incomplete; Draft PR #7 remains draft. No deployment, provider/risk-limit
change, historical rewrite, worker restart or paid/vendor call.

## R08 recovery fingerprint construction prerequisite

New internal `recovery_fingerprint.py` is not wired to the worker, API or CLI.
It constructs a separate digest; existing API config_hash and immutable run
history remain unchanged. Owner/run/instrument/as-of/ordered analysts, source
IDs/freshness and revalidated payload hashes bind to the original request.
The digest includes source manifests, full portfolio/policy content, rendered
book, risk-source content hashes, language/allowance, effective configuration,
native graph options/analyst plan, supplied resolved-client descriptors,
actual Python-package source bytes and installed runtime/dependency versions.

| Gate | Status | Evidence |
| --- | --- | --- |
| Identity construction / mismatch rejection | PASS | 44 focused tests, 5.47 s: effective config/model/provider/endpoint, owner/instrument/date/roles, source changes/corruption/future availability, original run/allowance/prompt, runtime, risk and full book/policy binding |
| Existing JSON codec coupling | PASS | Changed risk-round fingerprint rejects previously encoded checkpoint before model reentry; client factory explicitly forbidden in this test |
| Privacy and relocation | PASS | Returns digest only, no SDK/network initialization. Credential-bearing/invalid URLs and common credential fields/unknown config keys rejected; fixed error text. Output/cache/memory paths do not change research identity; no CLI memory read |
| Actual runtime identity | PASS | Source-byte changes alter digest without changing Git HEAD or package version; Python and installed distribution versions bind. Package-source symlinks rejected, no env/credential file read |
| Full local Python | PASS | `.venv/bin/python -m pytest -q --disable-warnings`: 1,924 tests + 88 subtests, 20 skips, 22 warnings, 131.46 s; Python 3.14.7/macOS, clean c705cad source throughout gate |
| Ruff/diff/templates | PASS | `.venv/bin/ruff check .`, `git diff --check`, Ruby issue-template YAML load |
| PostgreSQL/optional providers | UNVERIFIED | Same 18 PostgreSQL, missing Bedrock dependency and live DeepSeek-key gates skipped |
| Web/CLI activation or live acceptance | NOT_IN_SCOPE | New internal prerequisite only; no frontend change, new recovery route, queue retry, supervisor integration or runtime restart |
| Trusted resolved-client attestation | UNVERIFIED | Mandatory descriptor binds endpoint/class/non-secret effective SDK-option hashes, but caller supplies it. Actual client initialization must derive/attest these fields before production use |
| Durable authorized recovery | UNVERIFIED | Owner-readable load/authentication, checkpoint-byte integrity, state/context validation, parent lease-fenced synchronous commit/ack, continuation consent and retained accounting remain open |
| Financial/MT acceptance | UNVERIFIED | No live report produced; earlier manual semantic/editorial failures unchanged |
| NQ=F | BLOCKED | Owner's contract/roll-source hold unchanged; no substitute |

Fingerprint equality is not authentication, a signature, policy approval, source
coverage proof or permission to spend. Full risk-series semantics still require
the existing replay checks; rendered book must be constructed from trusted DB
instrument mappings. Hashing both supplied inputs does not attest their origin.
Actual initialized-client settings must be observed, not invented from API
declarations or supplied by browser/model content. No worker path consumes this
component yet; no exhausted allowance is reset or increased.

The runtime digest deliberately invalidates on any package-Python or installed
distribution-version change. Restore a compatible environment on another
machine; do not waive this conservatively broad identity check. Synthetic test
fixtures establish binding mechanics, not provider billing, determinism,
investment correctness or release readiness. The full R01–R14 goal remains open.

Next: derive trusted effective-client descriptors, then integrate the private
durable saver and supervised parent commit/ack, preserving execution_started
and explicit continuation consent. See `research-recovery-contract.md` and
`HANDOFF.md`; older dated receipts remain immutable.

## Initialized-client observation follow-up

Source `a120d5f33d6ed3653da187b470bf3f6c276ce638`, same branch/worktree,
clean source throughout full gate. No new dependencies, provider/endpoint/prompt/
risk-limit change, worker restart, private-history rewrite or paid/vendor call.
New internal adapter constructs descriptors from initialized OpenAI-compatible
sync SDK clients, rather than inventing effective settings from config alone.

| Gate | Status | Evidence |
| --- | --- | --- |
| Initialized SDK endpoint/options | PASS | Actual NormalizedChatOpenAI/MiniMax SDK instances with synthetic credentials; effective wire params, scalar/per-phase timeout, root retries and response settings hash. Mutation changes identity; descriptors exclude the credential |
| No model/network invocation | PASS | All new fixtures forbid sync/async HTTP send and model invoke; close both SDK clients. No vendor calls |
| Fail-closed configuration | PASS | Unreviewed object, declared custom headers/query/transports and credential-bearing extra-body rejected; fixed error text, no credential echo |
| SDK normalization / builder coupling | PASS | SDK-appended slash accepted; host/path/extra slash/query/credential changes rejected. Actual descriptor builds fingerprint; retry mutation changes it |
| Focused local gate | PASS | `.venv/bin/python -m pytest -q tests/test_initialized_client_binding.py tests/test_recovery_fingerprint.py --disable-warnings`: 62 passed, 4.21 s |
| Full local Python | PASS | `.venv/bin/python -m pytest -q`: 1,942 passed + 88 subtests, 20 skipped, 22 warnings, 102.05 s; Python 3.14.7/macOS, exact a120d5f source |
| Ruff/diff/templates | PASS | `.venv/bin/ruff check .`, `git diff --check`, Ruby YAML load of issue templates |
| Initial focused attempt | FAIL | Timeout assertion assumed SDK stored httpx.Timeout but it stored float 600; corrected test to interpret scalar, adapter already handled both. Initial import-order Ruff finding corrected before source commit |
| Full transport attestation | UNVERIFIED | Worker-controlled initialization/provenance, post-construction SDK/header/HTTP mutations, async invocation and other provider SDKs require review before production use |
| PostgreSQL/optional providers | UNVERIFIED | 18 missing TEST_POSTGRES_URL gates, missing langchain_aws and absent live DeepSeek key; skips not passes |
| Web recovery / durable storage | UNVERIFIED | No worker/API/CLI integration, private saver, lease-fenced commit/ack, continuation consent or crash accounting enabled |
| Live financial/MT acceptance | UNVERIFIED | No new report or paid run; earlier FAIL evidence unchanged |
| NQ=F live acceptance | BLOCKED | Owner's contract/roll-source hold unchanged |

The adapter observes selected safe initialized settings, not all possible
transport mutations. Its exact class allowlist does not attest construction
origin or ownership. It must not be treated as a browser-controlled recovery
permission. Next: trusted construction/mutation guards and durable supervised
parent commit/ack, with existing no-blind-replay and consent/accounting gates.
R01–R14 remains incomplete; no CI or public deployment.

## Private checkpoint persistence follow-up

Source `77b32d81a84f6abb4e5705fdd6a8e3e63e6c8852`, same branch/worktree,
clean throughout full regression. Migration `0011_research_checkpoints` adds
a separate recovery-only table; existing report/artifact/decision readers are
unchanged. No private owner DB was migrated, no runtime restarted, no provider,
endpoint, risk limit or execution authority changed. No AI/vendor call.

| Gate | Status | Evidence |
| --- | --- | --- |
| Private persistent records | PASS | Real disposable SQLite migration and database reopen retain restricted JSON; raw messages/reasoning absent; generic artifacts table empty |
| Commit-before-ACK | PASS | Real publication transaction rollback after flush yields no return receipt and no stored row; normal ACK only after transaction exits |
| Lease/cancellation fences | PASS | Real JobExecutionContext rejects expired lease, wrong worker, cancellation and recorded heartbeat failure; zero checkpoint rows |
| Owner/run/thread/hash/identity | PASS | Wrong owner/thread cannot write or read; changed fingerprint, corrupt latest bytes or checkpoint ID rejected without fallback |
| Append/idempotency | PASS | Same bytes return existing receipt; completed pending-write revision increments sequence and leaves original bytes unchanged; missing history returns None |
| Migration roundtrip | PASS | Fixture downgrade to 0010 and upgrade to head removes/recreates only new table; existing run/job can still accept checkpoint. No real historical data touched |
| Focused local gate | PASS | `.venv/bin/python -m pytest -q tests/test_private_checkpoint_store.py tests/test_snapshot_checkpoint_codec.py tests/test_durable_jobs.py tests/test_platform_persistence.py --disable-warnings`: 72 passed, 2 PostgreSQL skips, 7.20 s |
| Full local Python | PASS | `.venv/bin/python -m pytest -q --disable-warnings`: 1,955 tests + 88 subtests passed, 20 skipped, 22 warnings, 121.18 s; Python 3.14.7/macOS, clean 77b32d8 source |
| Ruff/diff/templates | PASS | `.venv/bin/ruff check .`, `git diff --check`, Ruby YAML issue-template load |
| Initial formatting gate | FAIL | Two import-order findings fixed before source commit; focused behavior gate had no failures |
| PostgreSQL/concurrent durability | UNVERIFIED | No TEST_POSTGRES_URL; new store not characterized under PostgreSQL or concurrent writer/crash workload |
| Native saver / production bridge | UNVERIFIED | No LangGraph saver or supervisor RPC invokes this store; separate-process write/ACK crash and accounting still required |
| Continuation authority | UNVERIFIED | Trusted fingerprint/client construction, original allowance accounting, explicit owner consent/idempotency and operational UI remain open; store/readability is not permission to continue |
| Runtime migration/deployment | NOT_IN_SCOPE | Only fresh disposable test DBs changed; no existing private DB, worker, public deployment or CI |
| Financial/translation/live | UNVERIFIED | No new report, existing manual FAIL not cured by storage tests; BTC/AAPL acceptance outstanding |
| NQ=F | BLOCKED | Owner's contract/roll-source hold unchanged |

The parent-only internal service must receive trusted original context; its
arguments are not authenticated browser inputs. DB commit/rollback tests are
not native process crash or provider-billing proof. The next integration must
preserve execution_started and no-blind-replay, refuse uncertain checkpoints,
and not increase/reset the original allowance. R01–R14 remains open.

## Native committed saver follow-up

Source `18c7d6975004863d08787d884bb359249c76a167`, same branch/worktree,
clean source throughout full gate. Internal CommittedSnapshotSaver uses native
ephemeral InMemorySaver while committing only restricted codec bytes. It is not
instantiated by production worker/API/CLI; no private DB migration, restart,
provider/prompt/risk change, AI/vendor call, CI or deployment.

| Gate | Status | Evidence |
| --- | --- | --- |
| Checkpoint/pending JSON commit | PASS | Both put/put_writes commit addressed native tuple; raw message/reasoning markers absent, JSON codec revalidates every captured version |
| Commit ACK refusal | PASS | Missing/wrong hash/nonpositive sequence/exception ACK rejects; fixed diagnostic/no callback payload echo; poisoned saver refuses future reads/list |
| Native sync scheduling fence | PASS | Event-controlled actual StateGraph fixture holds ACK, next node and completion cannot occur until release, using durability="sync" |
| Original graph / real DB restoration | PASS | 136 added cases: 17 boundaries × EN/VI/bilingual/invalid VI × latest/pending restoration, all 4 analysts, 2 debate/risk rounds. Restore exact bytes read from a new SQLite DB session into a fresh saver, verify owner/run/hash row match; identical model-call/prompt/stage traces and non-message AnalysisResult |
| Financial/translation gates preserved | PASS | Synthetic invalid VI still rejected after one repair; no valid decision_payload. This is gate behavior, not live editorial accuracy |
| Focused native/saver gate | PASS | `.venv/bin/python -m pytest -q tests/test_committed_checkpoint_saver.py tests/test_supervised_native_graph.py --disable-warnings -x`: 350 passed, 74.23 s; final test version includes DB read-back before restore |
| Initial fixture failure | FAIL | Put_writes invocation-only configurable fields reached tuple address and strict codec rejected. Corrected native address to thread/ns/checkpoint IDs, without changing state/control/metadata schema; subsequent 6 saver tests passed and final native matrix passed |
| Full local Python | PASS | `.venv/bin/python -m pytest -q --disable-warnings`: 2,097 passed + 88 subtests, 20 skipped, 22 warnings, 155.31 s; Python 3.14.7/macOS, clean 18c7d69 source |
| Ruff/diff/templates | PASS | `.venv/bin/ruff check .`, `git diff --check`, Ruby YAML issue-template load |
| PostgreSQL/optional providers | UNVERIFIED | Same 18 PostgreSQL, Bedrock dependency and live DeepSeek-key skips; new saver/store not characterized under PostgreSQL/concurrent workloads |
| Parent bridge / crash recovery | UNVERIFIED | New matrix is same-process native integration. Separate-process write/ACK crash, cancellation/lease loss, ambiguous provider billing and orphan/publication fences remain required before enablement |
| Owner continuation authority | UNVERIFIED | Trusted client/runtime/source construction, original allowance/usage accounting, explicit consent/idempotency and operational UI remain open |
| Production activation | NOT_IN_SCOPE | No saver hook in engine/supervisor/CLI/API or runtime restart; original workflow/runtime remains unchanged |
| Live finance/MT | UNVERIFIED | No new paid report; older manual failures remain unchanged |
| NQ=F | BLOCKED | Owner's contract/roll-source hold unchanged |

Blocking a saver callback alone is not sufficient under default async durability;
the eventual snapshot worker hook must require native sync durability. Raw
native objects remain ephemeral and are not serialized into DB JSON. A private
checkpoint/valid receipt is still not consent, budget reset, human approval or
a release/financial-quality claim. Next: supervised child bridge to parent
private commit/ACK and separate-process crash/lease/cancel tests, without
weakening execution_started/no-blind-replay or replaying any historical failure.
The full R01–R14 goal remains open.

## Opt-in supervised checkpoint bridge follow-up

Source `90f009b28745e58dc17d7ad2e1a3eabbfefdc9ce`, same branch/worktree,
clean source throughout full gate. Supervisor gains optional internal codec/
thread/commit/factory wiring, but default AnalysisEngine does not declare the
recording capability and default worker does not supply this setup. No API
request field, continuation route, history backfill, private DB migration,
restart, provider/prompt/risk-limit change, AI/vendor call, CI or deployment.

| Gate | Status | Evidence |
| --- | --- | --- |
| Parent-only commit boundary | PASS | Spawn fixture callback asserts parent PID; only fingerprint/thread goes to child. Codec JSON/thread validated before callback, exact receipt UUID/integer sequence/hash before ACK; partial/unsupported setup rejected before spawn |
| Malformed/failure ACK | PASS | Malformed bytes never reach callback; callback exception/private error text and wrong hash fail closed with no subsequent model admission |
| Post-commit fences | PASS | Owner cancellation, expired/lost lease and deadline at commit/ACK prevent model start. Committed row can remain but does not imply successful ACK/recovery; no allowance reset |
| Separate-process parent crash | PASS | POSIX/macOS fixture kills task-owned parent before commit or after commit/before ACK; waiting child stops executing via parent guard. Reopened SQLite retains zero/one row respectively. Terminal zombie is not called reaped; no replay |
| Native full graph via RPC | PASS | Four added native spawn cases, EN/VI/bilingual/invalid VI; all 14 stages, snapshot gates and 600s/retry1 unchanged; more than 17 owner/run-bound parent checkpoint rows. Invalid VI still has no decision_payload. This is fixture model evidence, not live financial proof |
| Focused bridge/crash | PASS | `.venv/bin/python -m pytest -q tests/test_checkpoint_bridge.py --disable-warnings -x`: final 11 passed, 20.28 s. Earlier 17-test bridge/native subset passed 41.20 s before adding two crash cases; not summed into a final standalone gate |
| Initial fixture assertion | FAIL | Used nonexistent observer.model_calls; corrected to actual started_calls to prove admission after ACK. Runtime path was not weakened; final focused/full gates pass |
| Full local Python | PASS | `.venv/bin/python -m pytest -q --disable-warnings`: 2,112 passed + 88 subtests, 20 skipped, 22 warnings, 252.17 s; Python 3.14.7/macOS, clean 90f009b source |
| Ruff/diff/templates | PASS | `.venv/bin/ruff check .`, `git diff --check`, Ruby YAML issue-template load |
| PostgreSQL/other OS | UNVERIFIED | 18 PostgreSQL, Bedrock dependency and live DeepSeek-key skips; new crash gate proven on this Mac, not complete OS matrix/concurrent PostgreSQL |
| Bounded parent DB callback | UNVERIFIED | Before/after cancellation/deadline checks do not interrupt a blocked synchronous parent DB callback; reviewed DB-lock/commit timeout remains required |
| Production recording/recovery | UNVERIFIED | Default worker/AnalysisEngine recorder hook, trusted initialized-client/source fingerprint, restored child execution, linked accounting/explicit consent/API/UI not enabled or proven |
| Financial/MT/live | UNVERIFIED | No new paid report, earlier semantic/editorial FAIL remains |
| NQ=F | BLOCKED | Owner's contract/roll-source hold unchanged |

Internal opt-in is not a user consent mechanism or trusted factory attestation
by itself. A readable checkpoint after lost ACK must not cause blind replay.
Child received no persistence callback/DB handle/lease and cannot publish rows;
parent-side private JSON remains separate from report artifacts. Existing
execution_started, original allowance, approval, source and finalization gates
remain unchanged. Next: bounded parent DB behavior, trusted production graph
capture and new-child restoration with explicit retained accounting/consent;
all R01–R14 source/UI/live requirements remain in scope and unfinished.

## Checkpoint database lock-wait follow-up

Source `63d63d2b3aec6bf984080a15978cfea9464aa6bc`, same branch/worktree,
clean throughout full regression. Explicit checkpoint sessions bound individual
SQLite busy operations and PostgreSQL lock/statement waits; default checkpoint
budget is 5 seconds. Normal database sessions and model timeouts are unchanged.
No private runtime DB migration, restart, AI/vendor call, CI or deployment.

| Gate | Status | Evidence |
| --- | --- | --- |
| Real SQLite writer/COMMIT contention | PASS | Independent connections hold writer or reader locks; checkpoint with 0.05-second budget fails within 1.5 seconds, stores zero rows and returns a fixed diagnostic without cause. After fixture lock release, explicit commit succeeds; pooled timeout restored |
| Rollback and budget validation | PASS | Body exception rolls back; boolean/nonfinite/out-of-range/string budgets rejected before transaction; checkpoint None budget cannot disable bound |
| Parent bridge failure fence | PASS | Held SQLite lock causes fixed checkpoint failure, zero model admissions/rows/ACK and child shutdown within 2.5 seconds from lock start; no second unbounded DB observer query |
| Initial COMMIT-lock test | FAIL | About 5.24 seconds exceeded unchanged 1.5-second threshold. Failed COMMIT left a DBAPI transaction while SQLAlchemy had deactivated its transaction; cleanup restored old timeout then retried. Corrected by explicit DBAPI rollback before restoration, not relaxing test |
| Final focused gate | PASS | `.venv/bin/python -m pytest -q tests/test_checkpoint_db_timeout.py tests/test_private_checkpoint_store.py tests/test_checkpoint_bridge.py --disable-warnings -x`: 37 passed, 22.57 s |
| Full local Python | PASS | `.venv/bin/python -m pytest -q --disable-warnings`: 2,125 passed + 88 subtests, 20 skipped, 22 warnings, 175.20 s; Python 3.14.7/macOS at clean source 63d63d2 |
| Ruff/diff/templates | PASS | `.venv/bin/ruff check .`, `git diff --check`, Ruby YAML issue-template load |
| Total transaction/network/disk deadline | UNVERIFIED | Per-operation bound is not a total deadline. Pool checkout, connect/pre-ping, driver/network/disk stalls and summed statements remain outside this proof; integration must cap waits to remaining owner allowance |
| PostgreSQL/optional providers | UNVERIFIED | No TEST_POSTGRES_URL: 18 integration skips; Bedrock dependency and live DeepSeek key account for remaining two skips. Transaction-local PostgreSQL implementation is not live proof |
| Production recovery and finance/MT | UNVERIFIED | Default worker still does not enable recorder/resume; trusted context/client construction, new-child restoration, original accounting and explicit consent/API/UI remain required. No new live report; older semantic/editorial FAIL unchanged |
| NQ=F | BLOCKED | Owner contract/roll-source hold unchanged |

This closes the characterized local SQLite checkpoint contention failure, not
all parent I/O/deadline or product acceptance. Preserve execution_started,
original allowance and no-blind-replay when wiring the production graph. The
full R01–R14 goal and Draft PR #7 remain open.

## Native snapshot recording hook follow-up

Source `8b08628500df74e8641b151669bf8ee82cf9857d`, same branch/worktree,
clean source throughout full regression. Added internal optional paired saver/
canonical run-thread parameters to actual propagate_snapshots. Default engine/
worker invocation unchanged; no private DB migration, restart, AI/vendor call,
CI, provider/risk change or deployment.

| Gate | Status | Evidence |
| --- | --- | --- |
| Sync invocation/config isolation | PASS | Hook compiles original workflow locally, passes sync durability and canonical thread alongside original callbacks/recursion limit/config_scope; instance graph unchanged on success or invoke failure |
| Invalid setup/default/CLI separation | PASS | Partial setup, non-saver, noncanonical/private invalid string, UUID object rejected before compile/invoke with fixed diagnostic; default snapshot path unchanged; non-snapshot graph rejects hook |
| Native full-flow bridge | PASS | Four committed spawn fixture cases now use actual graph hook rather than monkeypatched graph.invoke: EN/VI/bilingual/invalid VI, all 14 original stages, parent-owned restricted commit/ACK and existing financial/translation gates |
| Focused local gate | PASS | `.venv/bin/python -m pytest -q tests/test_snapshot_checkpoint_hook.py tests/test_supervised_native_graph.py -k 'internal_hook or incomplete_or_invalid_hook or default_snapshot_path or non_snapshot_graph or all_fourteen' --disable-warnings -x`: 18 passed, 340 deselected, 23.48 s |
| Full local Python | PASS | `.venv/bin/python -m pytest -q --disable-warnings`: 2,135 passed + 88 subtests, 20 skipped, 22 warnings, 199.46 s; Python 3.14.7/macOS, clean 8b08628 |
| Ruff/diff/templates | PASS | `.venv/bin/ruff check .`, `git diff --check`, Ruby YAML issue-template load |
| Production construction/continuation | UNVERIFIED | Hook accepts a trusted internal saver, not browser authority; default engine/worker do not select it. Trusted fingerprint/client/source construction, new-child restoration, retained accounting and explicit consent/API/UI still required |
| PostgreSQL/live finance/MT | UNVERIFIED | Same 18 PostgreSQL plus optional Bedrock/live DeepSeek skips; no paid report, older semantic/editorial failures remain |
| NQ=F | BLOCKED | Owner contract/roll-source hold unchanged |

This adds the actual graph recording invocation boundary; it is not an enabled
resume feature or product-completion claim. Preserve execution_started and the
original allowance when integrating the trusted platform path. R01–R14 remains
open, including outstanding asset ingestion, financial/translation and UX gates.

## Initialized snapshot graph identity follow-up

Source `c0d3cc7dbf832671b4aa1f58121e76634870e060`, same branch/worktree,
clean source throughout full regression. New internal guard derives descriptors
from actual clients on the exact initialized TradingAgentsGraph, not supplied
client bindings. Graph retains only a construction-time snapshot-reader digest.
No default engine/worker selection, private DB migration, restart, AI/vendor
call, CI, provider/risk change or deployment.

| Gate | Status | Evidence |
| --- | --- | --- |
| Actual initialized graph/SDK composition | PASS | Real snapshot graph plus reviewed OpenAI-compatible SDK with synthetic credential; HTTP sync/async send and model invoke forbidden. Derived fingerprint equals existing full original-input builder with actual client bindings; no legacy memory/tools |
| Pre-invocation mismatch refusal | PASS | Config, roles, quick/deep model, snapshot mode, owner, corrupt source, changed run model, endpoint, graph subclass and non-graph rejected with fixed diagnostic/no cause; zero provider invocations |
| Readers bound to graph construction | PASS | Valid recalculated source hash still rejected if different from readers used to construct graph; only digest added, no second raw source copy |
| Effective SDK options | PASS | Actual SDK retry mutation changes fingerprint while declared graph config stays unchanged; not a promise to authorize changed settings |
| Final focused gate | PASS | `.venv/bin/python -m pytest -q tests/test_initialized_graph_fingerprint.py tests/test_initialized_client_binding.py tests/test_recovery_fingerprint.py --disable-warnings -x`: 76 passed, 28 warnings, 5.73 s. Earlier 75-case gate preceded reader-digest case; not final evidence |
| Full local Python | PASS | `.venv/bin/python -m pytest -q --disable-warnings`: 2,149 passed + 88 subtests, 20 skipped, 50 warnings, 233.64 s; Python 3.14.7/macOS, clean c0d3cc7 |
| Ruff/diff/templates | PASS | `.venv/bin/ruff check .`, `git diff --check`, Ruby YAML issue-template load |
| Complete attestation and worker recovery | UNVERIFIED | Guard is an internal mismatch check, not authenticated DB loading, factory provenance or arbitrary SDK/header/transport/graph-closure mutation attestation. Trusted original context through supervised boundary, new-child restore, linked accounting/consent/API/UI still required; default worker unchanged |
| PostgreSQL/live finance/MT | UNVERIFIED | Same 18 PostgreSQL, missing optional Bedrock dependency and live DeepSeek-key skips; no new report, earlier semantic/editorial failures unchanged |
| NQ=F | BLOCKED | Owner contract/roll-source hold unchanged |

Hash identity cannot grant continuation consent, reset original allowance or
replace execution_started fencing. The full R01–R14 product goal remains open,
including remaining ingestion, financial/translation quality and operational UX.

## Original AnalysisEngine recorder wiring follow-up

Source `cb4e7061813c395d50e01fa61f6badb8418b016e`, same branch/worktree,
clean source throughout full regression. Optional exact SnapshotRecorder in the
original AnalysisEngine binds original context/expected fingerprint to actual
initialized graph before invoking the native sync recording hook. Default
engine/worker/CLI unchanged; no private DB migration/restart, AI/vendor call,
CI, provider/risk change or deployment.

| Gate | Status | Evidence |
| --- | --- | --- |
| Original engine wiring | PASS | Real graph/SDK initialization with synthetic credentials; explicit invocation spy receives restricted committed saver and canonical original run-thread only after full fingerprint matches. Mismatch produces no invocation; missing final structured output remains REVIEW/no decision |
| Setup/factory/legacy refusal | PASS | Owner/fingerprint/commit invalid setup fixed diagnostic; arbitrary recorder types/factories and non-snapshot request rejected. Recorder repr excludes private original context |
| Original observer/allowance | PASS | Exact existing ResearchObserver with original stored/legacy limits required; missing or enlarged wall/call limit rejected, exhausted allowance retains ResearchBudgetExceeded. Original start and calls not reset |
| Direct saver ACK parity | PASS | Saver now rejects bool/float/string sequences and string/missing record UUID, poisoning reuse; same strict boundary as parent bridge |
| Initial local checks | FAIL | Ruff imported-fixture shadowing fixed with explicit module alias. After allowance addition, collection failed because ResearchExecutionLimits is not package-exported; imported from contracts.runs, preserving guard |
| Final focused gate | PASS | `.venv/bin/python -m pytest -q tests/test_analysis_recording.py tests/test_analysis_engine.py tests/test_initialized_graph_fingerprint.py tests/test_committed_checkpoint_saver.py tests/test_checkpoint_bridge.py --disable-warnings -x`: 57 passed, 58 warnings, 21.55 s |
| Full local Python | PASS | `.venv/bin/python -m pytest -q --disable-warnings`: 2,167 passed + 88 subtests, 20 skipped, 80 warnings, 209.23 s; Python 3.14.7/macOS, clean cb4e706 |
| Ruff/diff/templates | PASS | `.venv/bin/ruff check .`, `git diff --check`, Ruby YAML issue-template load |
| Native/supervised recording enablement | UNVERIFIED | New recorder engine test is a wiring spy, not a native full-flow test. Existing native hook/bridge fixtures remain separate. Default supervisor/worker do not construct this recorder; trusted parent context transfer/attestation and observer adaptation remain required |
| Continuation authority/live | UNVERIFIED | New-child restore, immutable retained elapsed/calls/usage, consent/idempotency/API/UI, complete SDK/transport attestation and live financial/translation quality still open; no additional paid report |
| PostgreSQL/optional providers | UNVERIFIED | Same 18 PostgreSQL, Bedrock dependency and live DeepSeek-key skips; local gate cannot establish missing environments |
| NQ=F | BLOCKED | Owner contract/roll-source hold unchanged |

An internal recorder is not permission to replay a stopped job. Retain
execution_started and original allowance/accounting when wiring spawn and owner
continuation. Full R01–R14 remains open, including asset ingestion and operational
UX/financial acceptance; Draft PR stays draft.

## Actual recorder native-flow equivalence follow-up

Final source `c78908326a85bdeb642d4c0ad63afffdd92dc940`, same branch/worktree,
clean source throughout full gate. Test/helper and documentation changes only;
no production runtime/prompt/provider/risk change, private DB migration,
restart, AI/vendor call, CI or deployment. SDK construction uses synthetic key,
HTTP sync/async send is forbidden, only model-response methods are synthetic.
Actual AnalysisEngine, recorder prepare, propagate_snapshots and native invoke
are not replaced by a wiring spy.

| Gate | Status | Evidence |
| --- | --- | --- |
| Full native recorder / baseline equivalence | PASS | Four cases: EN/VI/bilingual/invalid VI, four analysts and two debate/risk rounds; full actual model-prompt/call trace, stage sequence and every non-message AnalysisResult field match unrecorded synthetic baseline. Invalid VI still has no decision payload |
| Original observer and private persistence | PASS | Original recorder start preserved. Real lease-fenced SQLite commits reopened in new session, contiguous sequences >17, owner/run/fingerprint binding; strict codec revalidates all rows, empty/absent message values and no synthetic credential/private reasoning marker. Original fixture run remains unchanged |
| Exact SDK cleanup | PASS | Fixture creates two actual SDK instances used by graph, closes both sync/async clients and asserts closed after execution; no second get_llm allocation discarded from tracking |
| Initial fixture checks | FAIL | Import order corrected. Updating saved run inputs hit immutable gate: fixture creates a new run, not weakening immutability. Assertion banning messages channel-version metadata was wrong: now checks actual values/strict decode/private marker, preserving native metadata. Original-row check initially omitted required owner argument, corrected |
| Final focused gate | PASS | `.venv/bin/python -m pytest -q tests/test_native_analysis_recording.py tests/test_analysis_recording.py tests/test_supervised_native_graph.py -k 'actual_recorder or original_engine or all_fourteen' --disable-warnings -x`: 14 passed, 351 deselected, 28 warnings, 21.36 s |
| Previous full gate | PASS | Clean `21a5ad1d67cba82faf6e85e911a6b8eaa719a87c`: 2,171 passed + 88 subtests, 20 skipped, 100 warnings, 312.28 s. Subsequently found fixture get_llm creates a new object on each call; corrected exact-instance tracking and reran. Earlier gate is not final cleanup evidence |
| Final full local Python | PASS | `.venv/bin/python -m pytest -q --disable-warnings`: 2,171 passed + 88 subtests, 20 skipped, 100 warnings, 264.81 s; Python 3.14.7/macOS, clean c789083 |
| Ruff/diff/templates | PASS | `.venv/bin/ruff check .`, `git diff --check`, Ruby YAML issue-template load |
| Usage/admission/billing / live finance/MT | UNVERIFIED | Synthetic methods bypass SDK callback accounting; observer usage explicitly incomplete. No live provider, source-coverage/semantic entailment/editorial proof or additional paid report; previous live failures remain |
| Supervised worker continuation | UNVERIFIED | Same-process recorder/native proof only. Trusted context/observer transfer through spawn, complete client/transport attestation, new-child restoration, retained original elapsed/calls/usage and explicit consent/API/UI still required; default worker does not enable recorder/resume |
| PostgreSQL/optional providers | UNVERIFIED | Same 18 PostgreSQL, optional Bedrock dependency and live DeepSeek-key skips |
| NQ=F | BLOCKED | Owner contract/roll-source hold unchanged |

Do not promote native synthetic equivalence to financial acceptance or permission
to replay a paid job. execution_started, original allowance, immutable history
and human approval remain mandatory. Full R01–R14, outstanding ingestion and
operational UX/live gates remain open; PR remains draft.

## Parent recorder allowance RPC follow-up

Source `98446bef42ce010b2a1733d9e91f198215e3ff78`, same branch/worktree,
clean source throughout full regression. Exact private checkpoint-enabled bridge
can validate original recorder allowance with the parent observer. No original
context transfer, worker recording/resume activation, private DB migration,
restart, AI/vendor call, CI, provider/risk change or deployment.

| Gate | Status | Evidence |
| --- | --- | --- |
| Original parent allowance proof | PASS | Spawn fixture requests original limits/fingerprint/thread, parent checks exact fields/types/identity and remaining_seconds using original observer. Success keeps start/limits unchanged, one synthetic model callback/commit accounted; no child clock created |
| Fail-closed setup | PASS | Larger wall/call limits, boolean wall, changed fingerprint/thread, private extra marker and expired budget refuse before model/commit. Spawned failed children verified stopped using PID marker; expired precheck spawns none. No private marker in error |
| Recorder bridge selection/ACK | PASS | Four real-SDK initialization unit cases use fake pipe: actual recorder prepare selects exact bridge and sends original fields; only True accepted, False/None/int 1 refused. These are unit selection checks, not parent proof or financial acceptance |
| Disabled bridge | PASS | Without checkpoint identity, no allowance RPC can be sent; fixed refusal |
| Focused final gate | PASS | `.venv/bin/python -m pytest -q tests/test_recording_allowance_bridge.py tests/test_analysis_recording.py tests/test_checkpoint_bridge.py --disable-warnings -x`: 38 passed, 38 warnings, 30.51 s. Import-only Ruff formatting corrected before source commit; no behavioral gate failure |
| Full local Python | PASS | `.venv/bin/python -m pytest -q --disable-warnings`: 2,184 passed + 88 subtests, 20 skipped, 108 warnings, 179.33 s; Python 3.14.7/macOS, clean 98446be |
| Ruff/diff/templates | PASS | `.venv/bin/ruff check .`, `git diff --check`, Ruby YAML issue-template load |
| Complete supervised recorder / authority | UNVERIFIED | Allowance proof alone transfers no original run/book/source and grants no consent. Trusted context/observer construction through spawn, complete transport attestation, actual recorder-native spawn, new-child restoration and retained accounting/API/UI remain required; default worker unchanged |
| Live finance/MT/PostgreSQL | UNVERIFIED | No fresh paid report or live semantic/translation acceptance; 18 PostgreSQL, optional Bedrock dependency and live DeepSeek-key skips unchanged |
| NQ=F | BLOCKED | Owner contract/roll-source hold unchanged |

This RPC never resets allowance or bypasses execution_started. Parent remains
the existing budget/admission/lease authority. Per-operation DB wait limitations
and provider-billing uncertainty are not cured by an allowance ACK. Full R01–R14,
remaining ingestion/UX/live requirements and Draft PR remain open.

## Original context to supervised recorder follow-up

Source `7172e3c79b309772b994cd71125eb3673dbd04eb`, branch
`fix/TA-R01-research-quality`, worktree
`/Volumes/Data/codex/worktrees/ta-030-analysis-risk/TradingAgents`, clean throughout
the full regression. Python 3.14.7, Darwin 25.5.0. No AI/vendor call, private DB
migration, runtime restart, CI, new provider, risk change, merge or deployment.

| Gate | Status | Evidence |
| --- | --- | --- |
| Original private context transfer | PASS | JSON-only owner/run/book/policy/risk envelope, 4 MB maximum, independent decoded copies; private fields excluded from repr. No SDK/DB/callable field. Actual initialized graph fingerprint still required before invocation |
| Context failure semantics | PASS | Wrong owner/book/policy owner, unknown/credential fields, policy object/nonfinite numbers, duplicate JSON keys, missing inputs, raw error/completed runs and malformed/oversized wire rejected with fixed messages. Tests cover applicable synthetic inputs; no claim of universal secret detection in source prose |
| Parent original setup | PASS | Complete codec/thread/commit required; exact original AnalysisEngine with context only. Its global fixture capability remains absent; arbitrary factory/context, missing callback and mismatched thread/fingerprint rejected |
| Pre-spawn request fence | PASS | Changed date/roles/source payload/freshness and missing snapshot reject before get_context, with zero admitted model calls |
| Child recorder construction | PASS | Explicit unit probe receives exact SnapshotRecorder, original run/owner and exact bridge-bound commit. This test replaces the child engine symbol with a probe and does not prove original native engine execution in spawn |
| Focused final gate | PASS | `.venv/bin/python -m pytest -q tests/test_recording_context.py tests/test_recording_allowance_bridge.py tests/test_checkpoint_bridge.py tests/test_analysis_recording.py --disable-warnings -x`: 73 passed, 38 warnings, 31.96 s |
| Initial collection gate | FAIL | Test fixture constructed codec without required nodes; fixed fixture before final gates, no production contract weakened. Earlier 65-pass focused run preceded extra policy/JSON cases and is not final-source proof |
| Full local Python | PASS | `.venv/bin/python -m pytest -q --disable-warnings`: 2,219 passed + 88 subtests, 20 skipped, 108 warnings, 180.37 s, clean exact source |
| Ruff/diff/templates | PASS | `.venv/bin/python -m ruff check .`, `git diff --check`, Ruby YAML load of issue templates |
| Actual native-spawn recorder / recovery | UNVERIFIED | Needs actual original engine/client/native graph through spawn with parent persistence. No checkpoint restore, retained-accounting/consent API/UI, authenticated loading or complete SDK transport attestation enabled |
| Live finance/MT/PostgreSQL | UNVERIFIED | No new live report; 18 PostgreSQL skips, missing optional Bedrock dependency and absent live DeepSeek key remain. Prior failed financial/editorial evidence unchanged |
| NQ=F | BLOCKED | Owner-selected contract/roll-data hold unchanged |

This is an internal opt-in integration, not default worker activation or a new
owner continuation permission. It preserves the original parent allowance,
execution_started, immutable private history and human approval. Next: actual
native-spawn recorder acceptance, trusted-client and accounting/consent gates,
new-child restoration; remaining R01–R14 ingestion/UX/live work is still required.

## Actual original recorder native spawn follow-up

Source `5195f554fc512cabff1752d9dffea07578c7a527`, same branch/worktree,
clean source throughout full regression; Python 3.14.7, Darwin 25.5.0. Tests and
contract documentation only; no production activation, new dependency, paid
model/vendor call, private DB migration, runtime restart, CI, provider/risk
change, historical rewrite, merge or deployment.

| Gate | Status | Evidence |
| --- | --- | --- |
| Exact engine/recorder/native process | PASS | Real spawn child PID differs from parent. Test bootstrap installs synthetic responses on reviewed real initialized SDKs, then calls exact production child with exact AnalysisEngine. No replacement of engine/graph/propagate/graph.invoke, identity/allowance or saver/store guards |
| Graph/presentation equivalence | PASS | Four analyst roles and two debate/risk rounds in EN/VI/bilingual/invalid VI; full prompt/model/stage trace matches uninterrupted fixture. All result fields compared after applying existing supervisor publication allowlist and debate-history projection; internal graph state is not claimed as published output |
| Invalid translation | PASS | Invalid VI remains report_translation_unavailable with no decision_payload; no fallback decision invented |
| Parent private persistence | PASS | Callback PIDs all parent; reopened disposable SQLite owner/run/fingerprint match, contiguous sequences and strict codec bytes. Messages empty/absent and synthetic credential/private reasoning markers absent. Original fixture run unchanged, no legacy report writes |
| Original allowance/cleanup | PASS | Original observer start and 1800/128 limits unchanged; actual two child SDK sync/async clients closed, exited child PID no longer exists after supervisor reaping |
| Focused final gate | PASS | `.venv/bin/python -m pytest -q tests/test_native_recorder_spawn.py tests/test_native_analysis_recording.py tests/test_analysis_recording.py tests/test_supervised_native_graph.py -k 'exact_engine or actual_recorder or original_engine or all_fourteen' --disable-warnings -x`: 18 passed, 355 deselected, 40 warnings, 29.60 s |
| Initial focused comparison | FAIL | Baseline included internal graph state excluded by supervisor; corrected comparison to existing RESULT_FIELDS and debate projection. Production projection/guards unchanged; initial import-only Ruff issue fixed. Subsequent 25-pass focused run preceded final reap/parent-PID assertions and is not final-source proof |
| Full local Python | PASS | `.venv/bin/python -m pytest -q --disable-warnings`: 2,223 passed + 88 subtests, 20 skipped, 120 warnings, 223.00 s, clean exact source |
| Ruff/diff/templates | PASS | `.venv/bin/python -m ruff check .`, `git diff --check`, Ruby YAML issue-template load |
| SDK callback accounting / recovery authority | UNVERIFIED | Synthetic methods bypass actual provider callbacks; usage explicitly incomplete. Retained elapsed/call/usage accounting, full transport attestation, owner consent/API/UI and restoration in a new child remain required before enablement |
| Live finance/MT/PostgreSQL | UNVERIFIED | No new live report or semantic financial/editorial acceptance; 18 PostgreSQL, optional Bedrock and live DeepSeek-key skips unchanged |
| NQ=F | BLOCKED | Owner-selected contract/roll-source hold unchanged |

This closes the synthetic actual-engine/native-spawn recording acceptance,
not live billing, financial quality, consent or production recovery. Default
worker recorder/resume remains disabled. Full R01–R14 ingestion, operational
UX and live requirements remain intact; goal and Draft PR #7 stay open.

## Native callback accounting and admission follow-up

Source `c5e6314f6593a86fd5727747928b1deb217e94f3`, same branch/worktree,
clean during full regression; Python 3.14.7, Darwin 25.5.0. Test/contract changes
only. No paid/vendor call, private DB migration/restart, CI, provider/risk change,
historical rewrite, merge or deployment; default worker remains unchanged.

| Gate | Status | Evidence |
| --- | --- | --- |
| Actual callback lifecycle | PASS | NormalizedChatOpenAI invoke and LangChain start/end remain actual; only _generate and schema binding are synthetic. No manual observer/bridge callbacks. Logical starts/completions and token counters match actual-SDK uninterrupted baseline for EN/VI/bilingual/invalid VI, all four roles and two rounds |
| Synthetic usage/authority | PASS | Each synthetic reply provides 10 input/5 output/15 total tokens; exact totals equal trace call counts. Parent original start/1800/128 allowance unchanged, cost and hidden provider request attempts stay None. This is not vendor-reported or billing evidence |
| Exhausted admission | PASS | Separate one-call original fixture allowance stops next admission with ResearchBudgetExceeded. One logical start/completion, first 15-token event and parent-owned strict checkpoint bytes retained. No failed provider call invented for denied admission; original fixture history unchanged |
| Native equivalence/persistence | PASS | Existing full published-result, prompt/stage trace, restricted SQLite reopen, child SDK cleanup/reaping and invalid-translation assertions also run in callback-enabled completion mode |
| Focused final gate | PASS | `.venv/bin/python -m pytest -q tests/test_native_recorder_spawn.py tests/test_native_analysis_recording.py tests/test_analysis_recording.py tests/test_supervised_native_graph.py -k 'exact_engine or actual_recorder or original_engine or all_fourteen' --disable-warnings -x`: 26 passed, 355 deselected, 76 warnings, 45.88 s. Earlier 8-pass run preceded exhausted cases; import-only Ruff formatting corrected before commit, no behavioral pytest failure |
| Full local Python | PASS | `.venv/bin/python -m pytest -q --disable-warnings`: 2,231 passed + 88 subtests, 20 skipped, 156 warnings, 230.77 s, exact clean source |
| Ruff/diff/templates | PASS | `.venv/bin/python -m ruff check .`, `git diff --check`, Ruby YAML issue-template load |
| Durable accounting / recovery | UNVERIFIED | No cross-attempt ledger or elapsed/unknown interrupted-usage retention, owner continuation consent/API/UI, restore or complete transport attestation enabled. Successful synthetic callback counters do not establish these gates |
| Live finance/MT/PostgreSQL | UNVERIFIED | No new live report; 18 PostgreSQL plus optional Bedrock and live DeepSeek-key skips unchanged. Financial/editorial acceptance remains incomplete |
| NQ=F | BLOCKED | Owner-selected contract/roll-source hold unchanged |

Next: durable original allowance and execution accounting/consent, then new-child
restore while preserving execution_started/no-blind-replay and immutable history.
Full R01–R14 ingestion/operational UX/live acceptance remains required; goal and
Draft PR stay open. No synthetic token count may be published as actual cost.

## Durable pre-admission usage reservation follow-up

Source `7833efd35664164e48459a4d8733cba310449cb8`, same branch/worktree,
clean throughout full regression; Python 3.14.7, Darwin 25.5.0. New observer
behavior and documented additive existing-event payload; no event type/table,
dependency/provider/risk change, private DB migration/restart, paid/vendor call,
CI, historical rewrite, merge or deployment. Recorder/resume remains disabled.

| Gate | Status | Evidence |
| --- | --- | --- |
| Reservation before admission | PASS | Atomic logical counter reservation emits existing model.usage before model-start callback returns. Existing worker fenced transaction commits counters/limits/observed elapsed, then same clock/cancellation checked; failed emission or expired commit boundary does not return permission to invoke |
| Unknown usage semantics | PASS | Admitted/completed/usage-reported counts must match for reported status. A second unfinished call is incomplete despite first reported call; counters/cost remain explicit, no fabricated refund/zero cost |
| Reopened durable events | PASS | Disposable SQLite fresh session reads unfinished reservation with owner/run/attempt, limits and observed 12 seconds; no completion is invented. Native spawned callback test uses same parent publication_session event pattern: original start/completion counters reopen, final usage matches and exhaustion retains [0,15] token observations plus private checkpoints |
| Deadline/emit failure | PASS | Synthetic emit exception prevents following provider entry; emit consuming original one-second budget is rejected after persistence, reservation retained and original start unchanged |
| Focused final gate | PASS | `.venv/bin/python -m pytest -q tests/test_usage_reservation.py tests/test_research_budget_clock.py tests/test_research_validation.py tests/test_research_supervision.py tests/test_native_recorder_spawn.py --disable-warnings -x`: 40 passed, 48 warnings, 69.32 s |
| Initial focused expectation | FAIL | Old supervision assertion expected only post-call usage; updated to assert both pre-call reservation and post-call completion. Reported-usage fixture now includes real logical start before end; no production guard weakened. Earlier 39-pass run preceded post-commit deadline case and is not final-source proof |
| Full local Python | PASS | `.venv/bin/python -m pytest -q --disable-warnings`: 2,235 passed + 88 subtests, 20 skipped, 156 warnings, 275.68 s, clean exact source |
| Ruff/diff/templates | PASS | `.venv/bin/python -m ruff check .`, `git diff --check`, Ruby YAML issue-template load; initial import-only Ruff formatting fixed before commit |
| Cross-attempt accounting/recovery | UNVERIFIED | No durable aggregation/unknown crash-duration policy, full transport attestation, owner consent/API/UI or new-child restore enabled. Elapsed is a lower bound at event time, general event transactions are not a hard end-to-end DB deadline; synthetic counters are not vendor billing |
| Live finance/MT/PostgreSQL | UNVERIFIED | No fresh live report; 18 PostgreSQL, optional Bedrock and live DeepSeek-key skips unchanged. Runtime upgrade/browser behavior not verified; no restart |
| NQ=F | BLOCKED | Owner's contract/roll-data hold unchanged |

Original execution_started/no-blind-replay, immutable history and human approval
remain mandatory. No missing historical reservations are backfilled. Next:
safe durable aggregation/unknown-duration accounting and explicit consent before
restore; remaining R01–R14 ingestion/operational UX/live acceptance still required.

## Read-only durable accounting evidence follow-up

Source `6034b88b6b158f1666828146a27b2f3db31bc861`, same branch/worktree,
clean throughout full regression; Python 3.14.7, Darwin 25.5.0. Internal reader
and synthetic fixture coverage only; no runtime activation, paid/vendor call,
private DB migration/restart, CI, provider/risk change, history rewrite, merge
or deployment.

| Gate | Status | Evidence |
| --- | --- | --- |
| Bounded owner-scoped evidence | PASS | Authoritative run lookup, contiguous owner/run event prefix at observed high-water, maximum 10,000 events and pages of at most 500; over-bound evidence rejects rather than truncates |
| Cross-attempt counters | PASS | Latest cumulative receipt per attempt summed once; reopened fixture with two completed calls and a second unfinished attempt retains 30 tokens, three starts and one unreported start. Pagination covers 504 rows without duplication |
| Unknown and invalid evidence | PASS | Empty, marker-only and legacy usage yield UNVERIFIED with totals None, not zero. Wrong owner/limits, bool counters, regression, inconsistent totals/status, invented cost, extra fields, bad scope/elapsed, missing marker and sequence gaps reject with fixed non-sensitive diagnostics |
| Actual native integration | PASS | Existing production-child/engine/recorder/native-spawn synthetic callback cases read committed parent event evidence; completion and exhausted cases retain matching synthetic counters and checkpoints. Exact elapsed remains unknown |
| Focused final gate | PASS | `.venv/bin/python -m pytest -q tests/test_accounting_evidence.py tests/test_usage_reservation.py tests/test_native_recorder_spawn.py --disable-warnings -x`: 34 passed, 48 warnings, 29.77 s. Earlier 23-pass/one-skip run preceded strengthened fixtures and is not final-source proof; import-only Ruff fix, no behavioral failure |
| Full local Python | PASS | `.venv/bin/python -m pytest -q --disable-warnings`: 2,253 passed + 88 subtests, 20 skipped, 156 warnings, 258.01 s, clean exact source |
| Ruff/diff/templates | PASS | `.venv/bin/python -m ruff check .`, `git diff --check`, Ruby YAML issue-template load |
| Continuation authority | UNVERIFIED | No transactional consent/high-water recheck, remaining-budget grant, authenticated artifact loading, new-child restore or complete transport attestation enabled. PASS means evidence parsed, not permission to continue; elapsed is a lower bound and totals may exceed original allowance |
| Live finance/MT/PostgreSQL | UNVERIFIED | No fresh live report or billing proof; 18 PostgreSQL, optional Bedrock dependency and live DeepSeek-key skips remain. Financial/editorial acceptance and runtime/browser upgrade remain incomplete |
| NQ=F | BLOCKED | Owner-selected contract/roll-source hold unchanged |

No private historical events are repaired or backfilled. Next: explicit original
allowance/unknown-duration policy and transactional consent, then new-child
restoration; full R01–R14 ingestion, operational UX and live acceptance remain
required. Default recorder/resume remains disabled; goal and Draft PR stay open.

## Accounting aggregate invariant follow-up

Source `b831d6ba7ad921918dd10533eeaef5198e05c35d`, same branch/worktree,
clean throughout full regression; Python 3.14.7, Darwin 25.5.0. No paid/vendor
call, private DB migration/restart, history rewrite, CI, provider/risk change,
merge or deployment. Reader remains internal and read-only.

| Gate | Status | Evidence |
| --- | --- | --- |
| Impossible token evidence | PASS | Reject nonzero token counters with zero usage-bearing completions, and token growth without increasing calls_with_usage; unchanged receipts and genuine native callback completion remain accepted |
| Aggregate elapsed | PASS | Reject nonfinite sum even when each attempt's elapsed is individually finite; no exact crash-duration or remaining-budget inference introduced |
| Immutable failure handling | PASS | Three disposable SQLite fixtures reopen, reject with fixed AccountingEvidenceError, and compare all ordered event sequence/payload pairs before/after; no repair or backfill |
| Focused gate | PASS | `.venv/bin/python -m pytest -q tests/test_accounting_evidence.py tests/test_usage_reservation.py tests/test_native_recorder_spawn.py --disable-warnings -x`: 37 passed, 48 warnings, 54.87 s; no behavioral failure |
| Full local Python | PASS | `.venv/bin/python -m pytest -q --disable-warnings`: 2,256 passed + 88 subtests, 20 skipped, 156 warnings, 254.09 s at clean exact source |
| Ruff/diff/templates | PASS | `.venv/bin/python -m ruff check .`, `git diff --check`, Ruby YAML issue-template load |
| Recovery/live/operational acceptance | UNVERIFIED | Consent/high-water transaction, unknown interrupted-duration policy, trusted loading/transport, new-child restore, remaining ingestion/UX and live finance/translation still required; synthetic evidence is not provider billing or production approval |
| PostgreSQL/other skips | UNVERIFIED | 18 PostgreSQL skips plus optional Bedrock dependency and live DeepSeek-key skips; no skip promoted to PASS |
| NQ=F | BLOCKED | Owner-selected contract/roll metadata hold unchanged |

Full R01–R14 goal and Draft PR #7 remain open. No continuation authority or
default worker recorder/resume activation follows from these local gates.

## Accounting original identity and observation recheck follow-up

Tested source `6ad3bba87f7a0a66cd3facbbfe6170d1eaa0117e`; implementation
`e7ec914720baea8fdf6c55808e976a665e5df92b`. Same branch/worktree; clean throughout
final full regression, Python 3.14.7/Darwin 25.5.0. Internal read-only changes,
no default activation, paid/vendor call, private DB migration/restart/history
rewrite, CI, provider/risk change, merge or deployment.

| Gate | Status | Evidence |
| --- | --- | --- |
| Original identity | PASS | Both PASS and UNVERIFIED observations bind owner/run/config hash and original scalar wall/call limits, including legacy defaults. Frozen repr suppresses identity/accounting fields |
| Full observation recheck | PASS | Fresh bounded evidence must equal complete expected observation. Wrong owner, another same-owner run with identical counters, altered totals/limits, wrong object type and newly appended non-accounting event reject with fixed diagnostic; unchanged observation returns None, not permission |
| Focused final gate | PASS | `.venv/bin/python -m pytest -q tests/test_accounting_evidence.py tests/test_usage_reservation.py tests/test_native_recorder_spawn.py --disable-warnings -x`: 44 passed, 48 warnings, 31.30 s after assertion repair. Earlier 44-pass run at implementation source took 31.56 s |
| Initial full regression | FAIL | At e7ec914: 1 failed, 2,262 passed + 88 subtests, 20 skipped, 156 warnings, 208.75 s. Privacy test banned substring 15, but default object repr's arbitrary hex address contained 15. Owner/accounting fields were not exposed; repaired assertion checks object.__repr__ field suppression and owner/run/config exclusion, no production validation weakened |
| Full final local Python | PASS | `.venv/bin/python -m pytest -q --disable-warnings`: 2,263 passed + 88 subtests, 20 skipped, 156 warnings, 207.69 s, exact clean tested source |
| Ruff/diff/templates | PASS | `.venv/bin/python -m ruff check .`, `git diff --check`, Ruby YAML issue-template load |
| Transactional consent/continuation | UNVERIFIED | Recheck is not writer locking, authenticated browser consent, an allowance grant or dispatch fence; another writer can commit after read. Linked execution, conservative unknown-duration accounting, trusted artifact loading/transport and new-child restore remain required |
| Live/operational/PostgreSQL | UNVERIFIED | No fresh live financial/translation or billing report, runtime upgrade/browser proof. Remaining ingestion/UX and 18 PostgreSQL plus Bedrock/DeepSeek-key skips unchanged |
| NQ=F | BLOCKED | Owner-selected contract/roll metadata hold unchanged |

No model invocation or history mutation is caused by either reader or recheck.
Full R01–R14 objective, explicit human approval and no-blind-replay remain intact;
goal and Draft PR #7 stay open, default recorder/resume stays disabled.

## Local supervised stop elapsed boundary follow-up

Source `af087670821882c161b56b275736438013148baa`, same branch/worktree;
clean throughout full regression, Python 3.14.7/Darwin 25.5.0. Additive existing
model.usage event payload, no new table/event type or default recorder/resume.
No paid/vendor call, private DB migration/restart/history rewrite, CI,
provider/risk change, merge or deployment.

| Gate | Status | Evidence |
| --- | --- | --- |
| Stop-after-cleanup boundary | PASS | Parent records execution_stopped=True only after process termination/join/close and reader shutdown; original observer clock/limits retained. Actual spawned fixture asserts child PID is already absent inside the stop emit callback |
| Closed observer | PASS | Later admission, completion/error callback and duplicate close reject; no usage/token/cost fabrication for unfinished calls. Failed stop persistence leaves no durable stop marker and cannot reopen the observer |
| Durable aggregation | PASS | Reader requires exact True, rejects duplicate stop or usage after stop, and derives elapsed_upper_bound only if every observed attempt has stop evidence. Partial history remains unknown; existing owner/config/high-water identity and strict cumulative counters retained |
| Native integration | PASS | Actual production child/engine/recorder/native fixtures retain original language/results/stage traces and private checkpoints. Completion/exhaustion rows reopen with synthetic token totals unchanged plus one stop event; exact_elapsed_known remains False |
| Publication refusal | PASS | Separate-process success/failure fixtures reject stop append; preserve original result/error without raw diagnostic exposure and assert child stopped. Missing append is never treated as durable accounting proof |
| Focused final gate | PASS | `.venv/bin/python -m pytest -q tests/test_accounting_evidence.py tests/test_usage_reservation.py tests/test_research_supervision.py tests/test_native_recorder_spawn.py --disable-warnings -x`: 66 passed, 48 warnings, 60.92 s. Earlier 57/64-pass gates preceded final fixtures; initial Ruff import formatting fixed, no behavioral failure |
| Full local Python | PASS | `.venv/bin/python -m pytest -q --disable-warnings`: 2,272 passed + 88 subtests, 20 skipped, 156 warnings, 211.36 s at exact clean source |
| Ruff/diff/templates | PASS | `.venv/bin/python -m ruff check .`, `git diff --check`, Ruby YAML issue-template load |
| Recovery/billing/production acceptance | UNVERIFIED | Upper bound concerns local supervised execution including cleanup, not remote provider processing/billing or exact elapsed. Unknown interrupted usage/cost retained. No remaining-budget grant, authenticated transactional consent, trusted loading/transport, new-child restore or default recovery activation |
| Live/operational/PostgreSQL | UNVERIFIED | No new live finance/translation report or runtime/browser upgrade proof; remaining ingestion/UX and 18 PostgreSQL plus optional Bedrock/live DeepSeek-key skips unchanged |
| NQ=F | BLOCKED | Owner-selected contract/roll metadata hold unchanged |

Old private rows remain unchanged. Abrupt parent crash or lease/cancellation
refusal cannot be inferred into a stop marker. Full R01–R14 goal and Draft PR #7
remain open; explicit human approval and no-blind-replay are mandatory.

## Original allowance arithmetic observation follow-up

Source `eb799a08adf79863c1e3f6f846a3698fb32c776f`, same branch/worktree;
clean throughout full regression, Python 3.14.7/Darwin 25.5.0. Internal read-only
observation, no new endpoint/table/dependency or default activation. No paid/vendor
call, private DB migration/restart/history rewrite, CI, provider/risk change,
merge or deployment.

| Gate | Status | Evidence |
| --- | --- | --- |
| Original cap debit | PASS | Loads authoritative owner/run accounting with no caller allowance/time input. All logical starts across attempts, including unfinished reservations, debit original cap; known stop upper bound debits original wall time |
| Uncertainty/exhaustion | PASS | Empty/legacy accounting withholds remaining values. Missing stop yields unknown remaining seconds, not fresh budget; exhausted call cap or elapsed lower bound blocks even without a stop marker. Overrun cannot become negative or enlarge limits |
| Private immutable observation | PASS | Frozen repr-suppressed result retains complete accounting/identity/high-water and unknown started usage. Wrong owner rejects; disposable fixture ordered event payloads and original run remain unchanged |
| Native receipt arithmetic | PASS | Existing actual production-child/engine/recorder native fixtures read completion/exhaustion receipts: remaining calls equals 128 minus actual logical trace calls, and exhausted one-call fixture remains BLOCKED with zero remaining calls. No new admission performed |
| Initial fixture gate | FAIL | Optional allowance on legacy unsnapshotted fixture rejected by RunManifest validation (1 failed, 1.18 s). Fixture repaired with valid snapshot binding; production validator unchanged. Subsequent 60-pass gate preceded two additional exhausted-history cases |
| Focused final gate | PASS | `.venv/bin/python -m pytest -q tests/test_remaining_allowance.py tests/test_accounting_evidence.py tests/test_usage_reservation.py tests/test_native_recorder_spawn.py --disable-warnings -x`: 62 passed, 48 warnings, 31.87 s |
| Full local Python | PASS | `.venv/bin/python -m pytest -q --disable-warnings`: 2,283 passed + 88 subtests, 20 skipped, 156 warnings, 218.78 s, exact clean source |
| Ruff/diff/templates | PASS | `.venv/bin/python -m ruff check .`, `git diff --check`, Ruby YAML issue-template load |
| Consent/supervisor/restore acceptance | UNVERIFIED | PASS means bounded arithmetic, not financial acceptance, consent token or admission. Transactional recheck/owner consent, linked execution, retained budget enforcement and trusted new-child restore/transport remain required before enablement |
| Live/operational/PostgreSQL | UNVERIFIED | No new live finance/translation/billing or runtime/browser proof. Remaining ingestion/UX and 18 PostgreSQL plus optional Bedrock/live DeepSeek-key skips unchanged |
| NQ=F | BLOCKED | Owner-selected contract/roll metadata hold unchanged |

No allowance reset, refund or inferred provider cost follows from positive
arithmetic. Full R01–R14 goal and Draft PR #7 stay open; default recorder/resume
remains disabled and existing private history remains immutable.

## Internal retained observer enforcement follow-up

Source `ff0e3be987e6aa28707adbff5c362df2577a1f74`, same branch/worktree;
clean throughout full regression, Python 3.14.7/Darwin 25.5.0. Internal budget
enforcement, no default worker/CLI/API selection, new provider/dependency/table,
paid/vendor call, private DB migration/restart/history rewrite, CI, risk-limit
change, merge or deployment.

| Gate | Status | Evidence |
| --- | --- | --- |
| Original evidence reload | PASS | Builder accepts no caller cap/time and reloads complete owner/run accounting. Wrong owner/run/type, altered allowance, newly appended event, unknown duration and exhausted original cap reject before observer construction |
| Retained wall/call enforcement | PASS | Original max_seconds/max_calls stay 60/3 in fixture. Prior 10 seconds/one logical start debit every new boundary; only two new calls fit, third denied. At new-attempt elapsed 50 seconds wall budget is exhausted, not reset to another 60 |
| Attempt-local event accounting | PASS | New events record only current-attempt elapsed/counters/tokens; reopened aggregation produces three starts, 45 synthetic tokens and 20 seconds (10 prior plus 10 new), not prior-inclusive duplicate time/calls |
| Post-emit deadline | PASS | Original retained deadline expiring during emit prevents provider entry; reservation remains incomplete, current-attempt elapsed remains 49.5 seconds rather than adding prior 10 into the event |
| Spawned fixture integration | PASS | Existing simple SpawnFixtureEngine traverses actual supervised bridge with retained parent observer, one remaining logical call, original cap and child reaping. Aggregate starts reaches three and remaining cap zero; frozen clock is synthetic, not latency or original-graph recovery proof |
| Focused final gate | PASS | `.venv/bin/python -m pytest -q tests/test_retained_observer.py tests/test_remaining_allowance.py tests/test_research_budget_clock.py tests/test_usage_reservation.py tests/test_native_recorder_spawn.py --disable-warnings -x`: 44 passed, 48 warnings, 48.65 s. Earlier 29-pass gate preceded final cases; Ruff import/nested-with formatting fixed, no behavioral failure |
| Full local Python | PASS | `.venv/bin/python -m pytest -q --disable-warnings`: 2,294 passed + 88 subtests, 20 skipped, 156 warnings, 254.40 s, exact clean source |
| Ruff/diff/templates | PASS | `.venv/bin/python -m ruff check .`, `git diff --check`, Ruby YAML issue-template load |
| Consent/restore/production acceptance | UNVERIFIED | Internal observer is not authenticated consent, a linked execution identity, writer locking or checkpoint restoration. Read comparison cannot fence later writers. Trusted transaction/lease/consent and original graph restoration/transport are still required; no default selection enabled |
| Live/operational/PostgreSQL | UNVERIFIED | No fresh live financial/translation/billing or runtime/browser proof; remaining ingestion/UX and 18 PostgreSQL plus optional Bedrock/live DeepSeek-key skips unchanged |
| NQ=F | BLOCKED | Owner-selected contract/roll metadata hold unchanged |

No builder may be presented as permission for a paid replay. Full R01–R14 goal,
immutable private history, explicit human approval and no-blind-replay remain
intact; goal and Draft PR #7 stay open.

## Internal native saver restore mechanism

Source `4e5b9aaf3015dd44970efe81b6a7c561931bfabb`, same branch/worktree;
clean throughout full regression, Python 3.14.7/Darwin 25.5.0. Internal restore
mechanism only, no default worker/API/CLI activation, paid/vendor call, private
DB migration/restart/history rewrite, CI, provider/risk change, merge or deploy.

| Gate | Status | Evidence |
| --- | --- | --- |
| Reviewed native import | PASS | Fresh saver only, expected thread and codec fingerprint binding; native versions/routing/metadata/parent/pending writes preserved with decoded tuple equality. Existing history is not republished during import |
| Invalid/partial import | PASS | Wrong thread/fingerprint, malformed bytes, occupied/repeated targets and native pending-write failure reject with fixed diagnostics and poison saver; no commit callback during import |
| Original graph equivalence | PASS | Committed native graph fixtures use actual restore method, not bespoke importer, across existing interruption/pending-write cases; prompt/model traces and final non-message results equal uninterrupted synthetic fixture. Same-process restore, not new-child recovery or live financial proof |
| Initial focused gate | FAIL | 1 failed/1 passed, 1.23 s: native JSON key order differs despite equal tuple fields. Changed byte equality to equality of validated decoded tuples; no field/routing validation removed |
| Focused gates | PASS | Saver/native graph suite: 365 passed, 76.94 s before final partial-failure case was added. Final saver suite: 18 passed, 1.18 s. Full gate below covers all final tests |
| Full local Python | PASS | `.venv/bin/python -m pytest -q --disable-warnings`: 2,301 passed + 88 subtests, 20 skipped, 156 warnings, 214.37 s, terminal exit 0 on exact clean source |
| Ruff/diff/templates | PASS | `.venv/bin/python -m ruff check .`, `git diff --check`, Ruby YAML issue-template load; import ordering fixed before source commit |
| Recovery activation | UNVERIFIED | Caller still needs initialized actual graph fingerprint, owner/lease/consent, linked execution, retained accounting and trusted new-child transport. This mechanism does not authenticate or authorize replay |
| Live/operational/PostgreSQL | UNVERIFIED | Ingestion, UI/browser and fresh live finance/translation/billing gates remain open; 18 PostgreSQL and optional Bedrock/live DeepSeek-key skips unchanged |
| NQ=F | BLOCKED | Owner-selected contract/roll metadata hold unchanged |

Next safe slice is trusted original-graph restoration into a new supervised
child with retained original allowance, before consent/API/UI activation.
Historical failures without checkpoints are not backfilled or replayed.

## Original recorder and snapshot graph restore hook

Source `7c36a2609c33ec3352295fbcb694a6d42539b4fe`, same branch/worktree;
clean throughout full regression, Python 3.14.7/Darwin 25.5.0. Internal hook only:
no default worker/API/CLI enablement, paid/vendor call, private DB migration,
runtime restart, history rewrite, provider/risk change, CI, merge or deploy.

| Gate | Status | Evidence |
| --- | --- | --- |
| Original native invocation | PASS | Recorder checks initialized original fingerprint and existing original-cap observer, restores restricted bytes, passes paired saver/thread/resume option. Snapshot graph invokes None under original config scope, recursion limit/callbacks and sync durability. No inferred next-stage list or replacement of instance graph |
| Fail-closed hook | PASS | Invalid resume types, missing/wrong saver and malformed recorder bytes reject before graph compile/invocation; invalid recorder bytes type/empty value rejected. Fixed diagnostics omit raw input; default initial-state invocation unchanged |
| Native recorder/engine equivalence | PASS | Four language/invalid-translation fixtures reopen intermediate immutable SQLite bytes through actual recorder/engine/native graph hook. Remaining synthetic model/prompt trace equals baseline suffix and complete non-message result matches baseline; no prior row mutated or observer start reset; initialized clients closed |
| Focused gate | PASS | `.venv/bin/python -m pytest -q tests/test_native_analysis_recording.py tests/test_analysis_recording.py tests/test_snapshot_checkpoint_hook.py tests/test_native_recorder_spawn.py --disable-warnings -x`: 52 passed, 122 warnings, 33.90 s |
| Full local Python | PASS | `.venv/bin/python -m pytest -q --disable-warnings`: 2,310 passed +88 subtests, 20 skipped, 172 warnings, 380.16 s on exact clean source, process terminal exit 0 (not inferred from 100% output) |
| Ruff/diff/templates | PASS | `.venv/bin/python -m ruff check .`, `git diff --check`, Ruby YAML issue-template load; import ordering fixed before source commit, no behavioral gate failure |
| Supervised recovery/consent | UNVERIFIED | New restore path exercised in same process; existing spawn recording fixtures remain passing, not new-child restore proof. Trusted checkpoint transfer/retained accounting, linked execution and transactional owner consent remain required before API/worker activation |
| Live/operational/PostgreSQL | UNVERIFIED | No fresh live financial/translation/billing or browser acceptance. Ingestion/UX requirements and 18 PostgreSQL plus optional Bedrock/live DeepSeek-key skips remain open |
| NQ=F | BLOCKED | Owner-selected contract/roll metadata hold unchanged |

Full R01–R14 goal and Draft PR #7 remain open. Next gate is actual separate-child
restoration under the parent retained allowance, not a new paid replay or budget.

## Restricted restore transfer into a new original child

Source `60e9200a1d47ac596c79c4135ef0bebb6628fcf8`, same branch/worktree;
clean throughout the completed regression, Python 3.14.7/Darwin 25.5.0.
No default worker/API/CLI activation, paid/vendor call, private DB migration,
runtime restart, history rewrite, provider/risk change, CI, merge or deploy.

| Gate | Status | Evidence |
| --- | --- | --- |
| Parent/child restricted transfer | PASS | Optional codec bytes require exact original recording context and AnalysisEngine. Parent validates and revalidates thread/fingerprint before spawn. Original child recorder checks initialized actual graph/client fingerprint and parent allowance before invoking restored original scheduler; DB/lease/commit stay parent-only |
| Invalid setup | PASS | Malformed bytes, wrong type/thread/fingerprint, missing original context and post-construction mutation reject with fixed diagnostic before spawn; no model admitted |
| Actual new-child native equivalence | PASS | Four callback-enabled EN/VI/bilingual/invalid-translation fixtures run a distinct new original child with an intermediate tuple from a completed synthetic run. Remaining prompt/model trace equals baseline suffix; published fields equal baseline, SDKs closed, both children reaped, existing SQLite rows unchanged |
| Retained accounting | PASS | Builder reloads first-attempt accounting; original 1,800 seconds/128 calls stay unchanged and all first-attempt calls/time debit, including work after the chosen tuple. Durable reader sums attempts 1/2 and synthetic tokens without resetting counters or inventing provider cost |
| Focused gates | PASS | Previous turn on unchanged source: native recorder spawn suite 12 passed, 48 warnings, 43.71 s; recording context/recording allowance bridge/retained observer suite 61 passed, 15.49 s. Full completed gate below covers final source |
| Interrupted full gate | UNVERIFIED | Previous handle 99476 disappeared after turn interruption; current process inventory contained no pytest. Terminal result was not captured, so no PASS inferred and no concurrent duplicate process started |
| Completed full local gate | PASS | `.venv/bin/python -m pytest -q --disable-warnings`, new handle 27976: 2,316 passed +88 subtests, 20 skipped, 172 warnings, 261.25 s, terminal exit 0 on exact clean source |
| Ruff/diff/templates | PASS | `.venv/bin/python -m ruff check .`, `git diff --check`, Ruby YAML issue-template load; import ordering fixed before source commit |
| Production recovery/consent | UNVERIFIED | Fixture branch from completed synthetic run is deliberately NOT stopped/crashed recovery or authorization. Transactional owner consent/linked execution, stale writer exclusion, stopped/ACK/crash-boundary restoration, trusted construction/transport attestation and default API/UI activation remain open |
| Live/operational/PostgreSQL | UNVERIFIED | Ingestion, UI/browser and fresh live financial/translation/billing gates remain open. Eighteen PostgreSQL and optional Bedrock/live DeepSeek-key skips unchanged |
| NQ=F | BLOCKED | Owner-selected contract/roll metadata hold unchanged |

Next safe acceptance slice is original native recovery after an actual stopped
fixture attempt, with retained accounting and immutable checkpoint selection.
Consent and linked execution must still be established before product activation;
historical failures without checkpoints are not backfilled or replayed.

## Stopped native attempt with durable pending writes and lost ACK

Source `d87ee6261a41d26df6d1639ef937eee08e433a53`, same branch/worktree;
clean throughout full regression, Python 3.14.7/Darwin 25.5.0. Test/fixture and
capability documentation only; production flow is unchanged. No paid/vendor
call, default resume activation, private DB migration/restart/history rewrite,
provider/risk change, CI, merge or deployment.

| Gate | Status | Evidence |
| --- | --- | --- |
| Actual stopped attempt | PASS | Parent commits the first returned nonempty market report's native pending writes in fenced disposable SQLite, then deliberately loses ACK. Actual supervisor raises fixed review error, terminates/reaps the first child and retains its original-clock stop accounting; no first-attempt final result is returned |
| Original native continuation | PASS | New original child uses latest tuple after private store owner/hash/fingerprint checks. Completed pending writes skip the completed model invocation; test-only captured prefix plus continuation prompt/model trace equals uninterrupted baseline across EN/VI/bilingual/invalid VI, and all published result fields match baseline |
| Retained budget/history | PASS | First-attempt one logical call/15 synthetic tokens and bounded stop duration debit the retained observer with original 1,800 seconds/128 calls. Reader sums attempts 1/2 to baseline call/token totals once; prior rows and original fixture run unchanged, parent-only commits, both child PIDs absent |
| Cleanup uncertainty/privacy | PASS | Killed child SDK cleanup is None/unknown, not claimed closed; resumed child's two SDKs are confirmed closed. Synthetic prompt-prefix capture is a fixture-only sink to disposable files outside Git; no production logging or checkpoint raw-message filter changed |
| Initial fixture gate | FAIL | 1 failed, 12 deselected, 3 warnings, 9.38 s: stop condition matched empty market_report in initial pending writes before any model trace existed. Corrected to require returned nonempty report; no product gate weakened |
| Focused gates | PASS | Stopped subset: 4 passed, 12 deselected, 20 warnings, 23.28 s. Final `.venv/bin/python -m pytest -q tests/test_native_recorder_spawn.py tests/test_retained_observer.py tests/test_committed_checkpoint_saver.py --disable-warnings -x`: 45 passed, 68 warnings, 80.42 s |
| Full local Python | PASS | `.venv/bin/python -m pytest -q --disable-warnings`: 2,320 passed +88 subtests, 20 skipped, 192 warnings, 267.81 s, terminal exit 0 on exact clean source |
| Ruff/diff/templates | PASS | `.venv/bin/python -m ruff check .`, `git diff --check`, Ruby YAML issue-template load; import ordering fixed before source commit |
| Product recovery/consent | UNVERIFIED | One completed-pending-write/lost-ACK boundary, not all stages or abrupt parent crash. Original fixture lease context reused; no production continuation consent or linked job identity created. Concurrent/stale writer exclusion, full transport attestation and API/UI activation remain open |
| Live/operational/PostgreSQL | UNVERIFIED | Ingestion/UX and fresh live financial/translation/billing acceptance remain open; 18 PostgreSQL and optional Bedrock/live DeepSeek-key skips unchanged |
| NQ=F | BLOCKED | Owner-selected contract/roll metadata hold unchanged |

Full R01–R14 goal and Draft PR #7 stay open. Next integration must create and
validate owner-authorized linked continuation identity/checkpoint/accounting
transactionally before any product dispatch; readable bytes are not consent.
Broader stopped/ACK boundaries and abrupt-crash uncertainty remain separate
acceptance work, not waived by this fixture.

## Supervised restore requires original retained observer construction

Source `6cd566f7e27a45ce247357bd2ee2b405c3d7c980`, branch
`fix/TA-R01-research-quality`, worktree
`/Volumes/Data/codex/worktrees/ta-030-analysis-risk/TradingAgents`.
Clean throughout full regression; Python 3.14.7/Darwin 25.5.0.
No paid/vendor call, CI, default recovery activation, private DB migration,
runtime restart, history rewrite, provider/risk change, merge or deployment.

| Gate | Status | Evidence |
| --- | --- | --- |
| Restore budget binding | PASS | Exact builder-created observer must match original owner/run/config/limits, prior elapsed/starts and clock/start/callback identities; fresh/copied/reset/mutated/used/stopped attempts reject before multiprocessing context creation |
| Deadline/cancellation | PASS | An unused binding preserves original remaining time, not a restarted clock; expired restore cannot spawn. Original cancellation callback wins both before and at deadline expiry |
| Private binding | PASS | Frozen binding suppresses field repr; request observer remains excluded from child request serialization. No binding enters events or grants consent; failed preflight admits no model and leaves disposable event rows unchanged |
| Initial focused fixture | FAIL | 1 failed, 1.51 s: reused generic database fixture already owned AAPL alias, preventing setup before observer guard. Changed fixture to empty disposable SQLite; alias/owner validators unchanged. Initial Ruff import ordering also corrected |
| Focused regression | PASS | `.venv/bin/python -m pytest -q tests/test_restore_observer_binding.py tests/test_recording_context.py tests/test_retained_observer.py --disable-warnings -x`: 73 passed, 4.98 s before final two cancellation cases |
| Actual native-spawn regression | PASS | `.venv/bin/python -m pytest -q tests/test_native_recorder_spawn.py tests/test_restore_observer_binding.py tests/test_recording_context.py tests/test_retained_observer.py --disable-warnings -x`: 89 passed, 68 warnings, 59.44 s before final cancellation cases. Existing stopped/lost-ACK and completed-branch EN/VI/bilingual/invalid-VI equivalence remains exercised |
| Final binding cases | PASS | `.venv/bin/python -m pytest -q tests/test_restore_observer_binding.py --disable-warnings -x`: 23 passed, 2.82 s, including original cancellation priority |
| Full local Python | PASS | `.venv/bin/python -m pytest -q --disable-warnings`, handle 51810: 2,343 passed +88 subtests, 20 skipped, 192 warnings, 350.14 s; actual terminal exit 0 on exact clean source, no source/test edits during the run |
| Ruff/diff/templates | PASS | `.venv/bin/python -m ruff check .`, `git diff --check`, Ruby YAML issue-template load; no public package/dependency/CLI entrypoint or frontend change |
| Product authority/dispatch | UNVERIFIED | Private binding detects accidental trusted-parent substitution, not arbitrary Python mutation, authenticated consent, transactional checkpoint/accounting/high-water selection, later-writer exclusion or linked execution. No default resume endpoint/worker enabled |
| Remaining acceptance | UNVERIFIED | Broader stopped/crash boundaries, trusted client/transport attestation, ingestion, operational browser/report UX and fresh live financial/editorial/provider evidence remain open; 18 PostgreSQL and optional Bedrock/live DeepSeek skips are not passes |
| NQ=F | BLOCKED | Owner's active-contract/roll metadata hold unchanged; no source substitution |

Read-only inspection additionally confirms constraints for the next linked
execution integration: `JobRow` enforces unique run ID, private checkpoint commit
requires the leased job's original run ID, recording context rejects terminal
run lifecycle/error fields, and fingerprint/native thread retain original run
identity. Do not erase old errors/completion, reset allowance or silently relabel
the checkpoint to get past these guards. An append-only authenticated execution
link and transactionally bound consent/checkpoint/accounting are still required;
this source supplies no production continuation identity. R01–R14 goal and
Draft PR #7 remain open, not complete or release-approved.

## Authenticated continuation consent reservation and PostgreSQL DDL repair

Initial source `f2f42354134bf5d53775e0019187a6421628de5e`; final source
`fdd0b717059f5067788c8af0dce4ea7064eb0fb4`, same branch/worktree.
Both full regressions ran without source/test edits. Python 3.14.7/Darwin 25.5.0.
No default resume route, model dispatch, provider/risk change, private runtime
migration/restart/history rewrite, paid AI/market-data call, CI, merge or deploy.

| Gate | Status | Evidence |
| --- | --- | --- |
| Authenticated reservation | PASS | Own bounded-lock transaction derives current active owner from session, checks CSRF/expiry/revocation and literal confirmation, then reloads stopped failed/cancelled original job/run, latest restricted checkpoint and complete accounting/high-water. UUID idempotency key and canonical payload preserve bool/int distinctions; constructor and mutated timeout reject None/zero/NaN |
| Durable immutable link | PASS | New 0012 table binds original digests, checkpoint ID/hash/fingerprint, all accounting and fixed original-budget/unknown-cost/unvalidated-research disclosures. Commit-before-ACK, same-key reopen, stale/foreign/corrupt/latest-row/input cases and commit rollback tested; original run/job/event/checkpoint history unchanged. No job/model call or fresh budget |
| Initial fixture failure | FAIL | 1 failed, 31 passed, 8.66 s before source commit: ORM JSON assignment with bool/int-equal values did not actually write the intended corrupt row. Fault injection changed to explicit SQL UPDATE; production digest comparison not weakened. Earlier Ruff fixture-name/import errors repaired before committed gates |
| Initial focused SQLite | PASS | 72 passed, 2 PostgreSQL skips, 15.44 s at final f2f4235 test content: continuation consent, owner auth, private checkpoint and platform persistence. Two actual threads exercise same/different keys, busy-writer bound, rollback and no original-history changes |
| Initial full normal Python | PASS | f2f4235, handle 12736: 2,386 passed +88 subtests, 20 skipped, 192 warnings, 343.82 s; terminal exit 0. Eighteen missing-URL PostgreSQL cases and two optional provider gates were not passes |
| Initial full disposable PostgreSQL | FAIL | f2f4235, handle 17994: 12 failed, 6 errors, 2,386 passed +88 subtests, 2 skipped, 192 warnings, 313.14 s; terminal exit 1. Root DDL error at 0011: both checkpoint UNIQUE constraints named uq_research_checkpoints_run_id, generating colliding PostgreSQL indexes. SQLite had accepted identical names. Task-owned container removed after exit |
| Draft DDL repair | PASS | fdd0b71 gives explicit distinct constraint names in model and 0011 migration. Offline PostgreSQL migration DDL checks all emitted unique names are distinct and checkpoint model names match. Does not change global naming convention, uniqueness semantics or private existing rows; no drop/recreate of an already migrated owner database |
| Final focused regression | PASS | Final source content: 66 passed, 5 missing-URL PostgreSQL skips, 18.05 s, tests/test_platform_persistence.py, tests/test_continuation_consent.py and tests/test_private_checkpoint_store.py. This gate alone did not prove PostgreSQL |
| PostgreSQL consent / concurrency | PASS | Four new actual disposable PostgreSQL cases in final full gate: failed/cancelled durable authenticated reservation and reopen; two concurrent requests with same key return one identity, different keys allow one reservation only. Original rows unchanged. These are service tests, not HTTP/browser consent, all races or dispatch evidence |
| Final full Python + PostgreSQL | PASS | Clean fdd0b71, handle 83844, TA_ALLOW_TEST_DB_RESET=1 bash scripts/verify-postgres-local.sh: 2,409 passed +88 subtests, 2 skipped, 192 warnings, 343.62 s; terminal exit 0. Ruff, pip check and git diff --check passed. PostgreSQL 16-alpine task-only loopback/ephemeral-port database; container ownership checked and only task-owned container removed |
| Optional providers / runtime matrix | UNVERIFIED | Missing langchain_aws and explicitly unset live DeepSeek key remain two skips. Other supported Python/runtime versions were not run; no optional provider was replaced or invoked |
| Clean package install prerequisite | PASS | Exact f2f4235 tracked source export, fresh noneditable isolated .[platform] installation, pip check and imports from site-packages outside export CWD: tradingagents, cli.main, API/jobs, new consent service and packaged 0012 migration. Fresh owned SQLite upgrades to 0012 and contains new table. Managed external run retained: /Volumes/Data/codex-builds/TradingAgents/fix-TA-R01-research-quality/20261002T224230Z-56814. No private .env/database/artifacts exported |
| Final-SHA clean package install | PASS | Exact fdd0b71 tracked source export, new isolated noneditable .[platform] install (handle 38189, terminal exit 0), fresh pip check, installed imports from site-packages rather than source CWD, packaged PostgreSQL offline DDL with distinct constraints and fresh owned SQLite upgrade/table/head checks (handle 3922, terminal exit 0). Managed external run completed and retained: /Volumes/Data/codex-builds/TradingAgents/fix-TA-R01-research-quality/20261002T231012Z-69916. No private env/runtime files exported |
| Fresh dependency full suite | UNVERIFIED | Clean-install import/migration proof is not the full regression suite on newly resolved dependencies. The full PostgreSQL gate used the unchanged project venv; no dependency lock/configuration was altered |
| Product continuation / private rollout | UNVERIFIED | Persisted dispatch_enabled remains false. No API/UI disclosure endpoint, consumption state, linked leased job, linked attempt accounting/publication, terminal-original-context reader or model entry enabled. An execution ID is not bearer authority. Existing private SQLite installations can retain old constraint names; additive migration/backup/rollout must be reviewed instead of dropping their history |
| Remaining goal acceptance | UNVERIFIED | Broader stopped/ACK boundaries and abrupt parent crashes, transport/client attestation, asset-appropriate ingestion/coverage, financial semantic/VI editorial checks, operational UI/report flow and fresh live BTC/AAPL acceptance remain open; no prior live failure reclassified |
| NQ=F | BLOCKED | Owner's active-contract/roll-source hold unchanged; no substitute/provider added |

Fresh install resolved tradingagents 0.5.0, langgraph 1.2.12, langchain-core
1.6.6, langchain-openai 1.6.7, pydantic 2.13.5, SQLAlchemy 2.1.2 and Alembic
1.20.0 under Python 3.14.7 at f2f4235. The subsequent fdd0b71 fresh install resolved
the same versions except SQLAlchemy 2.1.3; the project environment stayed unchanged.
These dependency observations are not a lockfile or
compatibility guarantee; runtime/source fingerprints remain conservative.

Next integrate transactional link consumption and separately leased execution,
retaining original native thread/source/client identity and all prior allowance.
The current terminal-context rejection and JobRow unique(run_id) stay unchanged.
Do not erase errors/completed_at, reset caps, relabel checkpoints or silently
create a fresh paid run. Request authentication and consent must share one
transaction, not nested connections contending on an outer last_seen/session
write lock; cookie/header consistency, Origin and CSRF checks remain mandatory.
No paid continuation is authorized by these tests. Full R01–R14 goal and Draft
PR #7 remain open; CI remains disabled_manually as verified via GitHub this turn.

## Separate linked allocation / lease consumption prerequisite

Source `dbde6ff46ddb5ad99b2e43b229c5460b444ac000`, same feature branch and
authoritative worktree. Clean source throughout the full gate; Python 3.14.7/
Darwin 25.5.0. This remains a private-platform draft, not release approval.
No default worker/API/CLI activation, paid AI/market-data call, private database
migration/restart/history rewrite, provider/risk change, CI, merge or deployment.

| Gate | Status | Evidence |
| --- | --- | --- |
| Authenticated allocation | PASS | Current owner/session/CSRF and immutable original consent/source/accounting/checkpoint are rechecked before one independent allocation. Same execution UUID is primary/foreign key; unique source-run/attempt prevents duplicate next-attempt identity. Original JobRow unique run ID and historical rows unchanged |
| Separate private lease | PASS | One trusted worker claims reserved allocation after full observation reload. Token hash only persisted; actual UUID returned after commit, excluded from repr. Durable reopen/renewal and same/different-worker races tested. A lease is not model/publication permission |
| Fixed remaining deadline | PASS | Claim-time deadline uses unchanged original wall cap minus known prior elapsed upper bound; renewals cannot extend it. Strict integer window, current owner, worker/token/source identity, clock rollback, fixed stored deadline and reset/foreign/bool/float handle cases reject. Matching corrupted deadline in both DB and handle also rejects |
| Cancellation / uncertain expiry | PASS | Unclaimed cancellation is cancelled; leased cancellation remains cancel_requested and rejects renewal. Expired/lost-ACK committed claim is review_required and cannot auto-reclaim/requeue. Disabled owner cannot renew; trusted expired-lease maintenance can retain review state without claiming child termination or zero cost |
| Commit / busy-writer boundaries | PASS | Pre-commit allocation/claim failure rolls back and produces no ACK. Deliberate post-commit claim ACK loss retains exactly one leased row, refuses another claim and later marks review. Real SQLite busy writer refuses under .05-second local bound; no raw DB/private marker in errors |
| Original history / accounting | PASS | Run/job/event/checkpoint columns unchanged across lifecycle tests. No actual new RESEARCH_EXECUTION_STARTED or MODEL_USAGE event emitted: accounting still observes original attempt only. This is not evidence of linked model usage or permission to omit a real leased execution from future accounting |
| Initial static gate | FAIL | Ruff reported two import-order issues; mechanically fixed before source commit. No pytest behavioral failure or validator weakening |
| Initial/intermediate focused | PASS | 78 passed, 8 missing-URL PostgreSQL skips, 19.54 s before extra fault cases; then 89 passed, 8 skips, 20.73 s before final deadline-corruption/clock cases |
| Final focused | PASS | Handle 97463: tests/test_linked_execution.py, test_continuation_consent.py, test_owner_auth.py, test_private_checkpoint_store.py and test_platform_persistence.py: 111 passed, 9 missing-URL PostgreSQL skips, 25.21 s. This gate alone did not establish PostgreSQL |
| Actual PostgreSQL linked mechanics | PASS | Three new disposable PostgreSQL cases in final full suite: original-history-preserving claim/reopen/renewal, two authenticated simultaneous allocations and two competing worker claims. Cancellation/expiry/fault variants were SQLite evidence, not all PostgreSQL race/crash coverage |
| Full Python / PostgreSQL | PASS | Exact clean source, handle 35237, TA_ALLOW_TEST_DB_RESET=1 bash scripts/verify-postgres-local.sh: 2,450 passed +88 subtests, 2 skipped, 192 warnings, 291.69 s; terminal exit 0. Ruff/pip check/diff PASS; helper verified ownership and removed only its disposable loopback PostgreSQL container, none remaining afterward |
| Final-source clean install | PASS | Exact tracked git archive into new externally managed source export, fresh isolated noneditable .[platform] install (handle 65472, terminal exit 0), pip check, imports of package/CLI/API/jobs/new linked service and packaged 0013 module from site-packages outside source CWD. Packaged offline PostgreSQL DDL unique/check constraints and fresh owned SQLite table/head 0013 checks passed (handle 58106, terminal exit 0) |
| Runtime observations | PASS | Project environment after full gate: langgraph 1.2.12, langchain-core 1.6.5, langchain-openai 1.6.6, pydantic 2.13.5, SQLAlchemy 2.1.1, Alembic 1.20.0. Fresh install: tradingagents 0.5.0, langgraph 1.2.12, langchain-core 1.6.6, langchain-openai 1.6.7, pydantic 2.13.5, SQLAlchemy 2.1.3, Alembic 1.20.0; Python 3.14.7. Observations are not a dependency lock or full matrix guarantee |
| Install evidence retention | PASS | /Volumes/Data/codex-builds/TradingAgents/fix-TA-R01-research-quality/20261002T233539Z-76938 ownership marker verified; run finished completed/exit 0, artifacts retained. No private env/database/reports exported; PyPI dependency installation is not an AI or market-data vendor call |
| Fresh dependency full suite / optional providers | UNVERIFIED | Full regression was project-environment evidence, not the fresh resolved dependency suite or other Python versions. Missing langchain_aws and explicitly unset live DeepSeek key remain two skips |
| Dedicated secret / vulnerability tooling | UNVERIFIED | command -v gitleaks and command -v detect-secrets both unavailable; repository scripts contain local/PG verification only. Changed-file inspection and authentication/redaction tests are not comprehensive secret or vulnerability scanning. No dependency manifest, production provider, endpoint or credential was changed |
| Actual graph / linked output integration | UNVERIFIED | No new execution event/observer/model admission, linked publication context, checkpoint execution provenance, closed-original-context reader, linked report/decision finalization or default worker consumed the lease. No successful state or supervised stop ACK invented; sequential multi-continuation accounting/consent is not implemented by relabeling the root job |
| Browser / financial / remaining scope | UNVERIFIED | No frontend edit or new browser consent journey tested. Broad stop/crash/transport, asset-appropriate sources, financial evidence semantics, VI editorial quality and fresh live BTC/AAPL acceptance remain open; older manual live failures unchanged |
| NQ=F | BLOCKED | Owner-selected active-contract/roll source hold unchanged; no provider or asset substituted |

The internal lease does not change persisted consent dispatch_enabled=false and
is not a default queue job or a bearer permission. Root job/run/history remain
immutable. Future model entry must bind the lease's deadline and token fence,
reload immutable original context without clearing terminal errors, preserve
native thread/fingerprint, record new linked attempt start/usage/known-stop
evidence and fence synchronous parent-only checkpoint/result commits. Do not
claim stopped/expired leases were free or settled merely because this prototype
has not emitted model accounting. Unknown termination must remain review.
Actual new-child native graph equivalence and all boundary tests must precede
API/UI or paid activation. Full R01–R14 goal and Draft PR #7 stay open.

## Linked parent publication / accounting prerequisite

Source `b089fe599a45655fe503119e162683caf5bc4294`, branch
`fix/TA-R01-research-quality`, authoritative worktree
`/Volumes/Data/codex/worktrees/ta-030-analysis-risk/TradingAgents`. Clean throughout
the full source gate; Python 3.14.7, Darwin 25.5.0 (macOS 26.5.2 arm64). This is
internal private-platform draft evidence, not product/live/release acceptance.

| Gate | Status | Evidence |
| --- | --- | --- |
| One-time parent entry | PASS | Exact unused retained observer + full original consent/source/accounting/checkpoint recheck under nonce/owner/job/run/execution locks. Entry marker and initial observer receipt commit together. Deliberate lost post-commit entry ACK retains attempt 2 with unknown stop and refuses another observer/entry |
| Linked transaction fence | PASS | Same-transaction worker/token/owner/root identity, unchanged source, active owner, entry actor, cancellation and expiry checks. Final check after caller flush rejects a checkpoint that expires mid-transaction. Clock after source-lock acquisition refuses expired heartbeat instead of reviving it. Renew retains original deadline |
| Append-only provenance | PASS | Additive 0014 creates entry/event/checkpoint side links only; root RunRow/JobRow and all old event/checkpoint columns remain unchanged. New checkpoint has original thread/job, linked attempt 2 and atomically committed actor link. Identical original bytes return original attempt-1 receipt without relabeling. Missing/corrupt latest link, marker, attempt and codec fingerprint/node mismatch refuse without fallback |
| Cumulative accounting | PASS | Actual parent callbacks reserve before admission, record completion usage and aggregate each attempt's latest cumulative receipt once. Fixture total 1 prior +1 new logical call, 15 +27 reported tokens; bound elapsed includes claim/prepare gap. Prior 1 +127 new starts exhaust original 128 cap. Even a matching tampered observer payload that would aggregate to 129 rolls back before ACK. No cap/provider/risk change |
| Stop uncertainty | PASS | Bound observer hook with matching private stopped state can persist stopped receipt under valid lease; arbitrary payload True cannot fabricate it. Duplicate stop rejects. Cancelled/expired late hook cannot persist stop and retains unknown elapsed upper bound; no refund/requeue/success. Fixture hook invocation is not actual child reaping or remote termination proof |
| Commit/concurrency/migration | PASS | Before-commit checkpoint failure rolls back actor and bytes; post-commit ACK loss retains one receipt and idempotent byte ACK does not append twice. Two concurrent writers obtain sequences 2/3 with separate actor links. Disposable empty side-table downgrade to 0013/up preserves original evidence. This does not authorize destructive private downgrades |
| Initial static failures | FAIL | Ruff flagged import formatting and two blind pytest Exception assertions; fixed with explicit boundary exception classes and mechanical import formatting. Subsequent checkpoint import ordering mechanically fixed. No validator weakened |
| Initial focused exception expectation | FAIL | Handle 25069: 1 failed, 8 passed, 2 PostgreSQL skips, 4.40 s. Tampered root run is rejected by codec/thread validation before linked context, so fixture's LinkedExecutionError-only expectation was wrong; now accepts the two explicit refusal boundaries, still asserts no persistence |
| Intermediate new fixtures | PASS | Handle 53686: 23 passed, 2 missing-URL PostgreSQL skips, 15.43 s; before added codec/commit-uncertainty/final lock-expiry cases |
| Further focused exception expectation | FAIL | Handle 26196: 1 failed, 21 passed, 2 skips, 10.14 s. Linked transaction sanitizes codec-contract ValueError into LinkedExecutionError; corrected explicit fixture expectation, not the refusal itself |
| Intermediate combined focused | PASS | Handle 32317: 165 passed, 10 missing-URL PostgreSQL skips, 35.40 s, before final source-lock-expiry case |
| Final combined focused | PASS | Handle 4155: `.venv/bin/python -m pytest -q tests/test_linked_publication.py tests/test_linked_execution.py tests/test_continuation_consent.py tests/test_private_checkpoint_store.py tests/test_accounting_evidence.py tests/test_platform_persistence.py --disable-warnings -x`: 166 passed, 10 PostgreSQL skips, 35.53 s |
| Actual PostgreSQL linked fixtures | PASS | Two new cases in final full suite: parent entry/cumulative usage/trusted-hook/checkpoint provenance and two concurrent checkpoint writers. These do not establish every fault variant on PostgreSQL or actual child execution |
| Full exact-source Python/PostgreSQL | PASS | Handle 99764, terminal exit 0: `TA_ALLOW_TEST_DB_RESET=1 bash scripts/verify-postgres-local.sh`: 2,481 passed +88 subtests, 2 skipped, 192 warnings, 303.69 s. Source remained clean/exact throughout. Ruff, pip check and diff PASS. Only task-owned disposable loopback PostgreSQL container removed by verified-label helper |
| Clean isolated installation | PASS | Exact tracked `git archive b089fe599a45655fe503119e162683caf5bc4294` export, fresh Python venv, noneditable `Source[platform]` pip install, handle 98138 terminal exit 0; per-command TMPDIR and pip cache below managed external run. Fresh pip check passed; package/CLI/API/jobs/linked context/packaged 0014 imports verified from site-packages outside source CWD |
| Initial full-chain offline DDL smoke | FAIL | Handle 6774: packaged offline `command.upgrade(config, "head", sql=True)` fails in existing 0007 data-reading migration because offline SELECT returns no rows result. No package/source change made to hide this. Offline generation from base is not claimed supported; actual base-to-head migrations remain covered by fresh owned SQLite and full disposable PostgreSQL suite |
| Scoped packaged migration smoke | PASS | Handle 61123 terminal exit 0: offline PostgreSQL `command.upgrade(config, "0010_owner_watchlist:head", sql=True)` validates packaged recovery table DDL and distinct checkpoint/attempt unique names. Fresh owned SQLite upgrades from base and verifies tables/head 0014. This is not full-chain offline PostgreSQL DDL evidence |
| Evidence retention / runtime | PASS | Ownership marker checked; managed run `/Volumes/Data/codex-builds/TradingAgents/fix-TA-R01-research-quality/20261003T001635Z-91802` finished completed/exit 0, retained. Fresh `Results/clean_install_smoke.py` and owned database stay local/untracked. Project dependencies: langgraph 1.2.12, core 1.6.5, openai 1.6.6, pydantic 2.13.5, SQLAlchemy 2.1.1, Alembic 1.20.0. Fresh: tradingagents 0.5.0, langgraph 1.2.12, core 1.6.6, openai 1.6.7, pydantic 2.13.5, SQLAlchemy 2.1.3, Alembic 1.20.0 |
| Dedicated secret/vulnerability scanners | UNVERIFIED | gitleaks and detect-secrets unavailable. Changed-file review/auth/redaction/unit tests and pip dependency consistency are not comprehensive secret/vulnerability scanning |
| Dependency/Python matrix and optional providers | UNVERIFIED | Full suite used project environment, not fresh resolved dependencies or other Python versions. Missing langchain_aws and explicitly unset live DeepSeek key are the two skips |
| Native child/default activation | UNVERIFIED | New context did not invoke a model or spawn a child. Terminal-original-context reader, linked stage/artifact/report/decision finalization, all transport/crash/late-stop reconciliation and sequential multi-continuation remain unwired. Consent dispatch_enabled=false; API/worker/CLI default behavior is unchanged |
| Browser / finance / broader R01–R14 | UNVERIFIED | No frontend change or new rendered/browser proof. Ingestion by asset, operational UX, financial source entailment, VI editorial and fresh live BTC/AAPL still open. Old private run failures remain untouched. SEC name/email has not actually been supplied; no fake local contact configured |
| NQ=F | BLOCKED | Owner-approved active-contract/roll source hold unchanged, no provider or instrument substitution |

No hosted CI, private DB migration/restart/history rewrite, paid AI/market-data
call, provider/risk change, broker/execution, main merge or deployment. PyPI
installation and disposable PostgreSQL are separate local build/test evidence.
Post-gate inventory confirms this task's container
`ta-research-qa-1790986610-91827` is absent. One older exited QA container belongs
to another run; it was not deleted or repurposed.
Next implement terminal original-context loading and linked stage/result
publication, then actual new-child native graph equivalence and complete stop/
cancel/expiry/ACK reconciliation before default API/UI activation or paid live
acceptance. A side actor link or hook call alone does not prove source/client
attestation, financial correctness or human-approval readiness. Full R01–R14
goal and Draft PR #7 remain open.

## Terminal original-context and single-use linked native dispatch

Source `27e969bd18b389854ebdb5b6c6b0af934b6cac10`, branch
`fix/TA-R01-research-quality`, authoritative worktree
`/Volumes/Data/codex/worktrees/ta-030-analysis-risk/TradingAgents`. Source was
committed/clean throughout the final full regression. Python 3.14.7,
macOS 26.5.2 arm64 / Darwin 25.5.0. Internal private-platform draft only.

| Gate | Status | Evidence |
| --- | --- | --- |
| Complete terminal context | PASS | Separate strict linked JSON retains full original FAILED/CANCELLED RunManifest including errors/completed_at and original fingerprint/thread. Ordinary context rejects the same terminal bytes. No original history edit, lifecycle projection, live fallback or fresh observer |
| Source/owner revalidation | PASS | Loader and pre-dispatch transaction reload actual owner-readable analyst/risk artifacts and snapshots, verify indexed row columns against manifest JSON and actual bytes/hash, original portfolio/policy and pinned checkpoint. Missing/foreign/changed data refuses dispatch; token/session/CSRF/nonce absent from transport and repr |
| Single-use parent dispatch | PASS | Additive 0015 stores one marker per execution with pinned checkpoint ID/hash. Exact context/codec/bound checkpoint callback, request/restore bytes and unused retained observer required; mutable setup rechecked. Marker commits before Process construction; deliberate precommit failure starts nothing, lost postcommit ACK refuses respawn, original deadline checked again before start |
| Native linked graph integration | PASS | Four actual spawn cases EN/VI/bilingual/invalid VI: original child stopped/reaped after committed nonempty market pending writes with lost ACK; root job/run become immutable FAILED; authenticated consent, separate lease/entry and original loader construct linked child restore. Prefix + suffix calls/prompts and non-message AnalysisResult match uninterrupted baseline. New checkpoint attempt 2/actor links, unchanged old rows; invalid VI still has no valid decision payload. Synthetic SDK/network-forbidden fixture, not live finance/provider billing |
| Real-clock receipt validation | PASS | Captured observer elapsed is finite/nonnegative and ≤ fresh monotonic read; usage counters/flags remain exact, cumulative accounting still rejects reset/decrease. Five bool/nonfinite/negative/future elapsed refusal cases added. The earlier exact comparison across two real clock reads was identified by source inspection, not a reproduced native failure; final native/full gates exercise corrected real-clock callbacks |
| Disposable PostgreSQL dispatch | PASS | Full suite executes two added integration cases: single-use original-history-preserving consumption and two concurrent parent consumers with exactly one winner. Other fault variants primarily SQLite, not every PostgreSQL crash/cancel boundary |
| Disposable migration reversal | PASS | Empty 0015 dispatch table down to 0014/up retains original evidence. No private-history downgrade/delete or private migration performed |
| Initial native fixture | FAIL | Handle 56037: 1 failed, 16 deselected, 5 warnings, 7.66 s. Fixture expected root error_message=ResearchExecutionFailed but worker stores root error_code and leaves error_message None; corrected assertion to full original manifest equality, without clearing/inventing history |
| Intermediate native matrix | PASS | Handle 31499: 4 passed, 16 deselected, 20 warnings, 45.72 s, before later source-column/reload/prestart guards |
| Initial source-integrity fixture | FAIL | Handle 2407: 1 failed, 3 passed, 5.17 s. ArtifactRow content_hash column changed while repository manifest payload stayed intact and loader accepted it. Fixed loader row↔manifest checks plus SnapshotRow checks and actual source reload before dispatch, not a weakened test |
| Intermediate focused | PASS | Handle 35782: 97 passed, 2 missing-URL PG skips, 20.31 s; then handle 33108: 120 passed, 4 skips, 38.32 s, before final strict guards/elapsed cases |
| Final combined focused | PASS | Handle 9748, terminal exit 0: `.venv/bin/python -m pytest -q tests/test_linked_recording.py tests/test_linked_publication.py tests/test_recording_context.py tests/test_retained_observer.py tests/test_native_recorder_spawn.py tests/test_recording_allowance_bridge.py --disable-warnings -x`: 145 passed, 4 missing-URL PostgreSQL skips, 88 warnings, 128.63 s. Precommit local evidence, not PostgreSQL proof on its own |
| Full exact-source regression | PASS | Handle 98733, terminal exit 0: `TA_ALLOW_TEST_DB_RESET=1 bash scripts/verify-postgres-local.sh`: 2,522 passed +88 subtests, 2 skipped, 212 warnings, 408.24 s. Includes actual disposable PG migration/race cases; Ruff/pip check/diff passed. Source clean/exact throughout |
| Templates/static | PASS | Ruby issue-template YAML load, Ruff and diff checks. Initial import-order lint repaired mechanically; no behavioral gate weakened |
| Clean noneditable install | PASS | Exact `git archive 27e969bd18b389854ebdb5b6c6b0af934b6cac10` into managed external Build; fresh Packages/venv installs Build[platform] noneditable, handle 16682 terminal exit 0. TMPDIR and pip cache per-command below managed run; no .env/runtime copy |
| Packaged imports/migrations | PASS | Handle 98271 terminal exit 0: fresh pip check and Results/clean_install_smoke.py from outside source CWD; site-packages package/CLI/API/jobs/linked recording/context/packaged 0015 imports, offline PG DDL `0010_owner_watchlist:head` and actual owned SQLite base→head0015. Known data-reading 0007 prevents full-chain base offline DDL; not claimed supported or rerun here |
| Install evidence/runtime | PASS | Managed `/Volumes/Data/codex-builds/TradingAgents/fix-TA-R01-research-quality/20261003T005331Z-4519`, ownership marker verified, finished completed/exit0, retained. Project langgraph1.2.12/core1.6.5/openai1.6.6/pydantic2.13.5/SQLAlchemy2.1.1/Alembic1.20.0; fresh tradingagents0.5.0/langgraph1.2.12/core1.6.6/openai1.6.7/pydantic2.13.5/SQLAlchemy2.1.3/Alembic1.20.0. Observations are not a dependency lock |
| Matrix/scanners/optional providers | UNVERIFIED | Full suite used project env, not fresh resolved deps or complete Python matrix. gitleaks/detect-secrets unavailable; auth/redaction tests and pip check not comprehensive security scanning. Missing langchain_aws and explicitly unset live DeepSeek key are the two skips |
| Default activation/finalization | UNVERIFIED | No API/worker/CLI route consumes new loader/context; consent dispatch_enabled=false. Linked stage artifact/report/decision finalization, multi-continuation and all late-stop/cancel/expiry/crash/transport reconciliation remain unfinished. Dispatch consumed is not successful execution or human approval |
| Browser/financial/full product | UNVERIFIED | No frontend change or new browser journey; asset ingestion, operational UX, source entailment, VI editorial and fresh live BTC/AAPL remain open. Old private financial failures unchanged; no paid rerun. SEC name/email not actually supplied/configured |
| NQ=F live | BLOCKED | Owner-selected active-contract/roll-source hold; no new provider or instrument substitute |

CI verified `disabled_manually`; Draft PR7 still open/draft before push.
Disposable helper removed only its labelled container
`ta-research-qa-1790988792-4121`; other app/container state was not changed.
No private database migration/restart/history rewrite, paid AI/vendor call,
provider/risk change, broker/execution, main merge or deployment. Full R01–R14
goal remains active; next work is linked report/decision finalization and
stop/cancel/expiry/ACK reconciliation before default API/UI activation.

## Linked stage, ordinary output pipeline and atomic completion receipt

Implementation source `02e956e6ab6c4d18aa32f049ecc37961bac8461c`, ORM parity
fix `e9cc2faa75c04916ad50e5319aa66eff531b1996`, final tested source
`f107b18e3c8f86e45328fce57271b3274289375b`. Same authoritative branch/worktree;
Python 3.14.7 / macOS26.5.2 arm64. Final full gate ran against committed, clean,
unchanged f107b18. Internal private-platform draft, not release approval.

| Gate | Status | Evidence |
| --- | --- | --- |
| Shared original pipeline | PASS | Ordinary handler and linked publisher use extracted `jobs/report.py` and existing EvidenceGraphService/RiskEngine/DecisionCandidateFactory. No graph role, round, finance/VI/schema gate, evidence or policy path cut; no model-based executable sizing |
| Stage retention | PASS | Exact unused observer-bound publisher, original owner-readable source reload and dispatch required. ResearchStageService retains role-owned text only, marked unvalidated/approval=false, with atomic execution/event/artifact actor links. Messages/reasoning/weights excluded; before dispatch/after stop rejected |
| Atomic output receipt | PASS | Additive0016 stores side artifact links and one completion per execution, pins final checkpoint, report/evidence/decision, result and cumulative accounting hashes. Return/ACK only after fenced commit; original FAILED/CANCELLED run/job unchanged. Missing schema/invalid translation stays REVIEW |
| Deterministic risk not bypassed | PASS | Real existing seeded book/policy/risk pipeline returns original target .3/current .2, identical seeded checks, three evidence entries, requires_human_approval=true. Missing portfolio remains REVIEW. This is synthetic fixture proof, not actual investment approval |
| Publication refusal | PASS | Wrong/unreturned result, mismatched request, unstopped/unclean child, missing dispatch/latest actor, changed original sources, owner mismatch, cancelled/expired lease and duplicate writer refuse without partial completion metadata. Final-flush expiry rolls metadata back; unreferenced content-addressed blobs can survive rollback and are not deleted |
| Committed ACK recovery | PASS | Owner-scoped read checks full original run/job, consent/dispatch/original+final checkpoint, actor links, indexed artifact columns↔manifest, actual hashes, candidate/evidence and stopped accounting. Corrupt/foreign/missing evidence rejected. Postcommit ACK loss can be read without models or live lease; no replay grant |
| Completion fences | PASS | Further checkpoint/publication/heartbeat/cancel refused. Expiry maintenance retains committed marker, does not mark success or silently refund. Read-only archived receipt remains available after deadline subject to full integrity validation |
| Native original-flow result | PASS | Actual spawned original child/engine/recorder/native graph: immutable failed root → authenticated linked execution → retained original restore. Interrupted prefix+suffix and result fields match uninterrupted EN/VI/bilingual/invalid-VI baseline; invalid VI remains rejected. Linked receipt/report/candidate checked, old history unchanged, child reaped. Synthetic network-forbidden SDK, not live provider/financial proof |
| Slow clean exit / original limit | PASS | Four added actual native slow-exit cases delay local cleanup 1.5s after returning the original result. Linked supervisor polls within original retained allowance/cancel/lease checks rather than terminating at fixed1s. Five clock-controlled helper cases verify clean exit beyond1s, nonzero exit, original deadline, cancel and cancel-at-exit; no model start/new allowance |
| PostgreSQL/migration parity | PASS | Final full suite runs actual PG atomic writer, two-concurrent-writer and named-constraint cases, plus full Alembic autogenerate metadata parity. ORM explicit unique names match packaged0016; migration itself was not rewritten. Disposable empty-table down0015/up retains old evidence; no private downgrade/migration |
| Initial ACK diagnostic | FAIL | Handle98619: 1 failed, 12 passed, 1 PG skip, 10.60s. Artificial postcommit exception escaped fixed diagnostic boundary; added known-exception sanitization wrappers, not replay or a weakened fixture. Intermediate handles52528/42599 each14PASS+1skip; 57064:23PASS+1skip/10.37s |
| Contaminated intermediate gate | FAIL | Handle48187: 1 failed,112 passed,6PG skips,79warnings,102.34s; source edited while native test active. Its exact-source acceptance is UNVERIFIED; runtime fingerprint drift was a hypothesis, not established root cause. No fingerprint/VI gate waived. Later unchanged67573:27PASS,1skip,16deselected,21warnings,39.79s |
| Initial finalization focused | PASS | Handle75876:138PASS,7missing-URL PG skips,89warnings,122.81s. Ordinary handler/snapshot worker handle3728:17PASS/3.20s; initial native linked subset7661:4PASS,16deselected,20warnings,25.12s. These precede later schema/exit repairs, not final-source proof |
| Initial full schema gate | FAIL | Handle44150 at clean02e956e:1failed,2552passed+88subtests,2skips,213warnings,553.71s. `test_migration_schema_parity_and_rollback` found ORM-generated unique names differing from migration explicit names. e9cc2fa aligns metadata names and adds SQLite/PG assertions; no private constraint rename/history rewrite |
| Post-parity focused | PASS | Handle23941:139PASS,8missing-URL PG skips,89warnings,145.70s; shared six-file focused command below, before slow-exit repair |
| Post-parity full native gate | FAIL | Handle11444 at clean e9cc2fa:1failed,2554passed+88subtests,2skips,213warnings,671.87s. Bilingual linked stopped fixture reached `linked result publication requires review`; sanitized exception alone does not establish which internal predicate failed |
| Deterministic exit counterexample | FAIL | Handle34405:1failed,23deselected,5warnings,22.95s. Added real restored child delays local exit1.5s: parent returned result then terminated child, `_linked_clean_exit=False`, publication refused. This establishes the fixed1s cutoff defect without claiming underlying attestation from the earlier sanitized exception |
| Final focused | PASS | Handle53139 terminal0:163passed,8missing-URL PG skips,109warnings,328.51s. Seven-file command below, includes four slow native cases and five wait-boundary tests. Import-only Ruff formatting repaired afterward; behavior unchanged, final full f107b18 includes repair |
| Full final exact-source | PASS | Handle96475 terminal0: `TA_ALLOW_TEST_DB_RESET=1 bash scripts/verify-postgres-local.sh`, source f107b18 clean throughout:2564passed+88subtests,2skipped,233warnings,832.32s. Ruff/pip check/diff PASS; only helper-created labelled PG container removed |
| Static/templates | PASS | `.venv/bin/ruff check .`, `git diff --check`, Ruby issue-template YAML load. Import-order lint found in research-supervision test, mechanically corrected after focused terminal; no source edits during final native/full gates |
| Fresh noneditable final install | PASS | Exact tracked `git archive f107b18e3c8f86e45328fce57271b3274289375b` → managed Build, new Packages/venv installs Build[platform], handle51384 terminal0. Per-command TMPDIR/PIP_CACHE_DIR below managed run; no .env/private runtime copy |
| Packaged final imports/schema | PASS | Handle33483 terminal0: fresh pip check + Results/clean_install_smoke.py outside source cwd; package/CLI/API/worker/report/linked-results/0016 imports, PG offlineDDL `0010_owner_watchlist:head`, owned fresh SQLite base→head0016 + full metadata parity. Additional handle9720 terminal0 asserts all checked module origins inside fresh venv. Full base offlineDDL remains unsupported at known data-reading0007; not claimed/rerun |
| Retained build evidence | PASS | Final managed `/Volumes/Data/codex-builds/TradingAgents/fix-TA-R01-research-quality/20261003T015357Z-24296` finished completed/exit0, retained. Earlier02e install6038/smoke63350 and e9 install33713/smoke8551 passed, but their associated full gates failed; runs20261003T012543Z-15961 and20261003T013901Z-19298 finished failed/exit1, retained rather than replacing FAIL evidence |
| Dependency/matrix/scanner scope | UNVERIFIED | Project full env:langgraph1.2.12/core1.6.5/openai1.6.6/pydantic2.13.5/SQLAlchemy2.1.1/Alembic1.20.0. Fresh imports:tradingagents0.5.0/langgraph1.2.12/core1.6.6/openai1.6.7/pydantic2.13.5/SQLAlchemy2.1.3/Alembic1.20.0. Not full fresh-resolved-deps suite, lock or supported-Python matrix. gitleaks/detect-secrets unavailable; pip check/auth tests not comprehensive scanning. Optional Bedrock dependency and explicitly unset live DeepSeek key are two skips |
| Approval/default activation | UNVERIFIED | Existing approval still requires root SUCCEEDED, deliberately refuses the linked READY_FOR_APPROVAL fixture. Integrate verified completion with immutable candidate evidence and append-only lifecycle before human approval, without relabeling root. Default worker/API/CLI dispatch disabled; multi-continuation and all late-stop/crash/cancel/expiry/transport/ACK boundaries remain open |
| Full product/live/UI | UNVERIFIED | No frontend change/new browser journey or new paid report. Broader ingestion/source entailment, financial/VI editorial, operational process/layout/report UX and fresh live BTC/AAPL acceptance remain open; old private failures unchanged. SEC name/email not actually supplied/configured |
| NQ=F | BLOCKED | Owner hold pending active-contract/roll metadata; no new provider or substitute instrument |

Focused six-file command (75876/23941):
`.venv/bin/pytest -q tests/test_linked_results.py tests/test_linked_publication.py tests/test_linked_execution.py tests/test_native_recorder_spawn.py tests/test_analysis_job_handler.py tests/test_snapshot_decision_worker.py --disable-warnings -x`.
Final seven-file command53139:
`.venv/bin/pytest -q tests/test_research_supervision.py tests/test_native_recorder_spawn.py tests/test_linked_results.py tests/test_linked_publication.py tests/test_linked_execution.py tests/test_analysis_job_handler.py tests/test_snapshot_decision_worker.py --disable-warnings -x`.
Slow-exit counterexample34405:
`.venv/bin/pytest -q tests/test_native_recorder_spawn.py -k 'linked_slow_exit and English and not Vietnamese' --disable-warnings -x`.
Final full96475 uses per-command TMPDIR below the final managed run; same helper
and reset acknowledgement as earlier full gates, exclusively disposable QA DB.
Fresh install uses managed venv `python -m pip install 'Build[platform]' --quiet`
with exact absolute Build path above, not editable developer installation.

CI rechecked disabled_manually. One older exited QA container from another run
was left untouched; final task's container was removed by the ownership-labelled
helper. No private DB migration/restart/history rewrite, provider/endpoint/risk
change, AI/vendor call, broker/execution, main merge or deployment. Next implement
verified completion human-review/approval integration, then remaining stop/ACK
reconciliation and authenticated API/UI activation before separately authorized
live acceptance. Full R01–R14 goal stays active; Draft PR7 stays draft.

## Verified linked-completion human review/approval

Source `bb738a7205aac9e6d10e455959e8c07368bfbe98`, branch
`fix/TA-R01-research-quality`, worktree
`/Volumes/Data/codex/worktrees/ta-030-analysis-risk/TradingAgents`. This slice
uses the existing authenticated decision transition route; it does not enable
default continuation dispatch, change ordinary success authority, run a model,
replace a provider, alter risk limits or migrate the private database.

| Gate | Status | Evidence |
| --- | --- | --- |
| Completion authority | PASS | Approval resolves receipt by decision first; full owner/root/job/consent/dispatch/original+final checkpoint, report/evidence/accounting hashes and actor links verified before approval or cached identical ACK. Root stays FAILED/CANCELLED; no forged SUCCEEDED column accepted. Missing artifact store/receipt and pre-completion event time refuse |
| Immutable candidate/current projection | PASS | Candidate payload/hash stays pinned; indexed owner/run/instrument/rating/schema/as-of and status must match immutable payload plus append-only lifecycle. Indexed event columns↔payload/time match, events cannot precede linked completion. Human review→ready→approve and reject retain old root/job/event/checkpoint history |
| Actual sources/deterministic risk | PASS | Reload all owner-readable analyst/risk artifact bytes and snapshot/artifact columns at original as-of, then replay existing READY candidate risk/source policy checks. Source-column mutation, changed evaluated policy and wrong owner/policy fail; no fresh live fallback or portfolio/risk override |
| Authenticated API mechanics | PASS | TestClient existing route: unauthenticated401, missingCSRF403, spoofed actor422, foreign/missing decision404, wrong policy409. Two identical authorized transitions produce one event/current approved with immutable ready candidate; changed request conflicts. Synthetic owner/database, not browser/live proof |
| Actual concurrent PostgreSQL | PASS | Full disposable PG helper supplies TEST_POSTGRES_URL. Same-event two-writer calls acknowledge one committed event; differing event IDs commit only one. Decision row lock/CAS, owner-scoped verified receipt and immutable old history preserved. SQLite concurrent writer may fail closed |
| Corruption/privacy refusal | PASS | Missing/foreign/corrupt receipt/report/source, failed stop, indexed root/status/event mutation and lifecycle SYSTEM actor rejected. ArtifactIntegrityError sanitized to fixed LinkedExecutionError without synthetic private diagnostic; zero approval event on failure |
| Initial import formatting | FAIL | New test initially had unused sqlalchemy.select (F401), removed before execution. Later fault-fixture import list failed I001; a grouped shell command nevertheless ran its behavior gate. Formatter applied only after that test terminated and before source commit; final full lint PASS. No package source edited during final focused/full gates |
| Intermediate focused evidence | PASS | Handles91447:75PASS/4missingURL PG skips/12warnings/32.99s; 28944:82PASS/6skips/19warnings/36.19s; 6773:107PASS/6skips/128warnings/163.94s; 32293:85PASS/6skips/22warnings/42.26s. These predate the final indexed-root guard; not final-source acceptance |
| Final focused/native regression | PASS | Handle54351 terminal0, 110PASS/6missingURL PG skips/131warnings/163.63s. Seven files listed below; includes actual native recorder/spawn fixtures. Test import formatting repaired after terminal, no package fingerprint change; exact committed full gate follows |
| Full clean exact-source local/PG | PASS | Handle88995 terminal0: 2,589 tests +88 subtests, 2 optional-provider skips, 258 warnings, 730.85s. Ruff/pip-check/diff PASS within helper; clean unchanged source bb738a7 throughout. Python3.14.7/macOS26.5.2 arm64. Only task-labelled ta-research-qa-1790995520-38830 stopped/removed; earlier exited container untouched |
| Exact noneditable tracked installation | PASS | Handle31007 terminal0: git archive bb738a7 → owned managed Build, fresh Packages/venv, pip install absolute `Build[platform]` --quiet; per-command TMPDIR/PIP_CACHE_DIR inside managed run, not editable source or private env copy |
| Packaged imports/schema parity | PASS | Handle27428 terminal0: Results/clean_install_smoke.py from outside source cwd asserts package/CLI/API/worker/report/repository/linked-results/0016 modules are inside fresh venv site-packages. Scoped PG offlineDDL `0010_owner_watchlist:head`, owned fresh SQLite base→head0016 + full ORM metadata and named completion uniqueness parity, pip check PASS. Not full base offlineDDL; known data-reading0007 limitation unchanged |
| Retained managed evidence | PASS | `/Volumes/Data/codex-builds/TradingAgents/fix-TA-R01-research-quality/20261003T022602Z-34694` finished completed/exit0 after all handles terminal, valid ownership marker, retained on verified external SSD. No deletion of prior builds/test evidence |
| Matrix/fresh dependency/scanner scope | UNVERIFIED | Project full env:langgraph1.2.12/core1.6.5/openai1.6.6/pydantic2.13.5/SQLAlchemy2.1.1/Alembic1.20.0. Fresh imports:tradingagents0.5.0/langgraph1.2.12/core1.6.6/openai1.6.7/pydantic2.13.5/SQLAlchemy2.1.3/Alembic1.20.0. Not a dependency lock, full fresh-resolved suite or Python matrix. gitleaks/detect-secrets unavailable; optional Bedrock module and explicitly unset live DeepSeek key remain two skipped gates |
| Default continuation/reconciliation | UNVERIFIED | API/worker/CLI continuation dispatch remains disabled. Multi-continuation and full late stop/cancel/expiry/transport/crash/ACK reconciliation still open. Real native graph fixtures regress report publication but do not yet prove an actual native portfolio-ready report→human approval path |
| Product/browser/live finance/VI | UNVERIFIED | No frontend/browser journey, new financial report or paid/vendor call. Ingestion/source entailment, editorial finance/VI and process/layout/decision UX plus fresh BTC/AAPL acceptance remain open. SEC_EDGAR_USER_AGENT presence-only recheck false; real name/email not yet supplied/configured |
| NQ=F | BLOCKED | Owner hold pending active-contract/roll metadata unchanged; no provider or substitute added |

Final focused command54351:
`.venv/bin/pytest -q tests/test_linked_approval.py tests/test_linked_results.py tests/test_decision_event_persistence.py tests/test_decision_lifecycle.py tests/test_risk_provenance.py tests/test_decision_api.py tests/test_native_recorder_spawn.py --disable-warnings -x`.
Final full88995:
`TMPDIR=/Volumes/Data/codex-builds/TradingAgents/fix-TA-R01-research-quality/20261003T022602Z-34694/Tmp TA_ALLOW_TEST_DB_RESET=1 bash scripts/verify-postgres-local.sh`.
Static precommit: `.venv/bin/ruff check .`, `.venv/bin/pip check`,
`git diff --check`, Ruby YAML load of `.github/ISSUE_TEMPLATE/*.yml` PASS.

README/ProductContract/persistence/recovery docs updated in source commit.
CI remains disabled_manually. No private DB migration, runtime restart, source
history rewrite, provider/endpoint/risk-limit change, broker action, AI/vendor
call, main merge or deployment. Next characterize actual native portfolio-ready
approval and remaining recovery/reconciliation boundaries before default owner
API/UI activation, then separately authorized live acceptance. This removes
the earlier linked-approval root-SUCCEEDED restriction only for fully verified
completion evidence; it does not remove any financial or human-approval gate.
Full R01–R14 goal remains active; Draft PR7 remains draft.

## Native portfolio approval and linked lifecycle timing

Source `c04b23e3bf88a71b594c57fdb7db3b0e07a132f8`, branch
`fix/TA-R01-research-quality`, worktree
`/Volumes/Data/codex/worktrees/ta-030-analysis-risk/TradingAgents`.
Production change is the shared linked lifecycle timestamp check before any
write/idempotent ACK. Ordinary non-approval behavior is unchanged; full human
approval/source/risk/completion gates are retained. No new migration, provider,
risk limit, model call or default continuation dispatch activation.

| Gate | Status | Evidence |
| --- | --- | --- |
| Writer/reader timing counterexample | FAIL | Handle65549 terminal1:1failed/12deselected/1warning/3.99s; real linked review at completion minus1s did not raise. Existing reader requires all events at/after completion, so this admitted unreadable history. Fixed before append/ACK, not by weakening reader or rewriting old events |
| Timing boundary/rollback | PASS | Review/reject/expire before completion each refuse with zero lifecycle events and unchanged indexed status; receipt still readable. Exact boundary each accepted/idempotent with one event. API clock before completion returns409, current ready projection/empty history retained; after boundary approval succeeds |
| Initial ordinary/linked regression | PASS | Handle49612 terminal0:39PASS/2missingURL PG skips/16warnings/20.58s; linked API and existing ordinary event/lifecycle/API behavior |
| Initial native fixture assertion | FAIL | Handle61623 terminal1:1failed/1passed/30deselected/10warnings/34.12s. English native portfolio→approval already passed; policy-fail assertion incorrectly used PolicyCheck.status instead of actual result field. Corrected fixture field, retained actual FAIL requirement; no policy/graph weakening |
| Initial clock API fixture schema | FAIL | Handle71829 terminal1:1failed/6passed/36deselected/7warnings/17.93s. Fixture sent unsupported to_status, correctly received422; fixed to existing action(review/reject/expire) schema, no API schema change |
| Intermediate new matrix | PASS | Handle27357 terminal0:17PASS/36deselected/49warnings/75.34s; eight native portfolio/policy/language cases plus nine timing/API cases. Predates the strengthened actual native-output→authenticated API helper; not final-source acceptance |
| Native original portfolio context | PASS | Eight added real spawned original child/AnalysisEngine/recorder/native graph cases, SQLite owner book with two holdings, original policy and actual stored risk sources. Failed root after durable market pending-write ACK loss; authenticated continuation/lease/dispatch, terminal original loader, exact book/policy/risk transfer, retained allowance/usage and old checkpoint bytes. No fresh live fallback |
| Original graph not cut | PASS | All 4 analysts and 2 research/risk rounds retained. Prefix+suffix actual downstream prompt trace and full published result equal uninterrupted native baseline; explicit STAGES and two Bull/Aggressive visits asserted. Child PID changes, restored SDK clients close and children reaped; old root/job/event/checkpoint history unchanged. Synthetic SDK response patch forbids HTTP send, not a live-provider attestation |
| Native output→authenticated approval | PASS | Valid EN/VI/bilingual candidate uses original owner target .3/current .2 and identical seeded RiskEngine checks. The actual committed native result—not a separately seeded publisher output—is read through TestClient login/CSRF/existing transitions. Two identical approvals return200 with one event/current approved, immutable ready candidate. Verified completion remains readable after approval |
| Invalid output/policy cannot approve | PASS | Original owner request .95 violates unchanged position/turnover policy; candidate REVIEW, target withheld and actual FAIL checks retained. Invalid VI/repair still REVIEW. All five native negative variants remain review/zero events; API409 on repeated approval, direct ready transition refused. No model weight or prose override |
| Final focused/native/legacy suite | PASS | Handle12301 terminal0:433PASS/2missingURL PG skips/167warnings/331.21s. Seven-file command below; all native recorder/spawn and supervised original-graph checkpoint regression plus linked/ordinary lifecycle/risk/API tests. Source unchanged during gate; import I001 mechanically corrected before start |
| Full clean exact-source PostgreSQL | PASS | Handle41705 terminal0:2,606 tests +88 subtests, 2optional-provider skips,307warnings,653.63s. Clean unchanged c04b23e throughout helper; Ruff/pip-check/diff PASS. Actual PG existing admission/approval/concurrent writers/schema cases run, but eight new native+API cases specifically use SQLite—not combined native PG proof |
| Fresh exact tracked install | PASS | Handle26214 terminal0:Git archive c04b23e → owned Build, fresh Packages/venv, noneditable absolute Build[platform] install with managed per-command TMPDIR/PIP_CACHE_DIR. No private env/runtime copy |
| Packaged imports/schema | PASS | Handle36404 terminal0:outside-source Results/clean_install_smoke.py asserts module origins inside fresh venv site-packages for package/CLI/API/worker/report/repository/linked-results/0016. Scoped packaged PG offlineDDL0010:head, owned fresh SQLite base→head0016/full metadata and named constraints parity, pip-check PASS. Known full-base offlineDDL0007 limitation unchanged/not claimed |
| Storage/cleanup | PASS | Managed `/Volumes/Data/codex-builds/TradingAgents/fix-TA-R01-research-quality/20261003T030539Z-46140` completed/exit0 after all handles terminal, retained on verified external SSD. Helper removed only labelled ta-research-qa-1790997718-50683; older exited QA container untouched |
| Runtime/dependency/scanner scope | UNVERIFIED | Full project Python3.14.7/macOS26.5.2 arm64, langgraph1.2.12/core1.6.5/openai1.6.6/pydantic2.13.5/SQLAlchemy2.1.1/Alembic1.20.0. Fresh imports tradingagents0.5.0/langgraph1.2.12/core1.6.6/openai1.6.7/pydantic2.13.5/SQLAlchemy2.1.3/Alembic1.20.0. Not a full fresh-dependency suite, lock or Python matrix; gitleaks/detect-secrets unavailable. Missing langchain_aws and unset live DeepSeek key remain skips |
| Recovery/activation/browser | UNVERIFIED | Actual native PostgreSQL portfolio approval, full stop/cancel/expiry/transport/crash/ACK reconciliation and multi-continuation remain open. Default API/worker/CLI continuation dispatch remains off; no private DB migration/restart/browser journey or default UI activation |
| Financial/VI/product/live | UNVERIFIED | Native mechanics/synthetic translation are not economic accuracy/source-entailment, editorial, investment suitability or browser/operational UX acceptance. Broader ingestion and fresh live BTC/AAPL remain open; no paid/provider call or old private-history rewrite. SEC contact presence-only recheck false |
| NQ=F | BLOCKED | Owner hold pending active-contract/roll metadata unchanged; no provider/substitute added |

Initial timing65549:
`.venv/bin/pytest -q tests/test_linked_approval.py -k nonapproval_event --disable-warnings -x`.
Intermediate matrix27357:
`.venv/bin/pytest -q tests/test_linked_approval.py tests/test_native_recorder_spawn.py -k 'nonapproval or api_clock or linked_portfolio' --disable-warnings -x --tb=short`.
Final focused12301:
`.venv/bin/pytest -q tests/test_linked_approval.py tests/test_native_recorder_spawn.py tests/test_supervised_native_graph.py tests/test_decision_event_persistence.py tests/test_decision_lifecycle.py tests/test_risk_provenance.py tests/test_decision_api.py --disable-warnings -x --tb=short`.
All use per-command TMPDIR below the current managed run. Full41705:
`TMPDIR=/Volumes/Data/codex-builds/TradingAgents/fix-TA-R01-research-quality/20261003T030539Z-46140/Tmp TA_ALLOW_TEST_DB_RESET=1 bash scripts/verify-postgres-local.sh`.
Static precommit Ruff whole repo/pip-check/diff/Ruby issue-template YAML PASS.

README/ProductContract/persistence document writer-side timing semantics in the
source commit. CI remains disabled_manually. No risk/provider/model/endpoint
change, private DB migration/restart/history rewrite, AI/vendor call, broker
action, main merge or deployment. Next characterize actual native PostgreSQL
approval and remaining recovery/reconciliation boundaries before default owner
API/UI activation, then separately authorized live/economic/editorial acceptance.
Full R01–R14 goal remains active; Draft PR7 remains draft.
