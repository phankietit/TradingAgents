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
