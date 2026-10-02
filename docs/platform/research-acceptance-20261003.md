# Research acceptance checkpoint — 2026-10-03

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
