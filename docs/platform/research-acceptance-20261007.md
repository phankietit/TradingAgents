# Research continuation evidence — 2026-10-07

Branch: `fix/TA-R01-research-quality`; Draft PR #7, no release or main merge.

## Recovered full-regression failure

Exact source `213529889a168b517d9397586a4f122de4981f8e`, clean during execution.
Original full disposable PostgreSQL helper88563 no longer has an accessible
terminal handle; process90612 is absent. Retained log includes full pytest
summary and ownership-safe container removal: **FAIL**,8 failed/2993 passed,
2 optional provider skips,88 subtests passed,443 warnings,1525.69 seconds.
No numeric terminal exit status is reconstructed from the missing handle.

Failures: eight `test_native_postgresql_portfolio_output_to_owner_api` cases for
linked_portfolio/linked_portfolio_policy_fail, EN/VI/bilingual valid and invalid
translation. Exact combined native model trace differs at Financial validation,
test_native_recorder_spawn.py:457. The invariant is retained unchanged.

## Corrective source-context ordering

The newly added full financial-review context flattened role dictionaries using
insertion order. PostgreSQL JSONB can change object-key order on durable reload.
Sort role and JSON-object keys when constructing this context; preserve complete
source arrays, timestamps, values, citations and article/candle order. No source
truncation, predicate relaxation, extra model call or CLI behavior change.

Focused local68628 terminal0:36 tests PASS/3.16s, Ruff/pip-check PASS. Explicit
selection: test_financial_validation_stage.py, test_report_compiler.py,
test_research_validation.py. Dirty patch at2135298; not clean-candidate or full
native/PostgreSQL proof. New test compares complete prompts after recursive key
and role reordering while verifying parsed full source and article ordering.

## Remaining acceptance

### Full default-recording baseline and original stopped-job consent

Clean frozen SHA `6fff558d6666fc365a6bfdc1bc20a1e5d1c73f84`:
full helper46603 terminal0, **3,127 tests+88 subtests PASS**,2 skips,
443warnings,3005.82s; Python3.14.7, Ruff/pip-check/diff PASS. Exact command:
`TMPDIR=<owned-run>/Tmp TA_ALLOW_TEST_DB_RESET=1 bash
scripts/verify-postgres-local.sh`, log `<owned-run>/Logs/full-default-recording-6fff558.log`.
Owned run: `/Volumes/Data/codex-builds/TradingAgents/fix-TA-R01-research-quality/20261007T052328Z-89163`.
Source/HEAD stayed unchanged, and only labelled helper-owned PostgreSQL removed.
Skips: Bedrock optional langchain_aws absent; DeepSeek live key unset/placeholder
(local helper deliberately unsets it). Both remain UNVERIFIED.
Full local evidence is not authenticated default continuation, financial/VI
semantic, current provider/data or release proof. Earlier timeout FAIL retained.

External staged `Results/test_default_stopped_consent.py` at this package SHA:
SQLite62224 terminal0,3PASS/3deselected/32warnings/36.06s; command
`PYTHONPATH=<owned-run>/Results:. TMPDIR=<owned-run>/Tmp .venv/bin/python -m
pytest -q <owned-run>/Results/test_default_stopped_consent.py -k sqlite --tb=short`.
Disposable-PG68953 terminal0,6PASS/32warnings/124.77s; same paths plus
`TA_ALLOW_TEST_DB_RESET=1 bash scripts/verify-postgres-local.sh --focused
<owned-run>/Results/test_default_stopped_consent.py`. Both SQLite/PostgreSQL and
EN/VI/bilingual pass. Real canonical default job, original graph/DB checkpoint
and codec, synthetic SDK with callbacks and simulated committed ACK loss.
Original stopped job has exactly1 call/15 reported tokens and a conservative
elapsed upper bound. Session/CSRF/literal-confirmation/idempotency enforce consent;
original run/job/checkpoint/event/accounting remain unchanged. Child reaped,
unknown remote cleanup remains unknown. No reservation/claim/dispatch/resume,
default web journey or actual model invocation is proved.

Retained staged FAILs:84362 terminal1,3FAIL/3deselected/19.47s from callback-off
fixture accounting0 rather than1; existing callback fixture fixes setup without
relaxing1call/15tokens assertion. PG10289 terminal1,2FAIL/4PASS/75.66s because
shared test DB correctly refuses second singleton-owner bootstrap. Per-case
explicit disposable DB isolation fixes fixture, not production auth. Source
now adds this test and strengthens successful-default accounting; integrated
and new full gates remain UNVERIFIED until separately run.

Presence-only SEC check corrects earlier worktree-only statements: root ignored
`.env` has email-shaped SEC_EDGAR_USER_AGENT, active worktree `.env` absent.
No actual contact/key printed, copied or changed. Explicit dotenv-path startup
is already documented; configuration presence is not current live SEC proof.
NQ=F remains owner BLOCKED; broader R01–R14 acceptance is incomplete.

Integrated candidate at6fff plus only two tests/these receipts:81182 terminal0,
**12PASS/115.03s**, no skips; Ruff/pip-check/diff PASS. Exact command:
`TMPDIR=<owned-run>/Tmp TA_ALLOW_TEST_DB_RESET=1 bash
scripts/verify-postgres-local.sh --focused tests/test_default_stopped_consent.py
tests/test_default_recording_native.py`. Source unchanged during QA; only own
labelled PG removed. Successful graph now compares full native model trace with
started calls and15 tokens per call, with no unreported starts and retained
elapsed upper bound. Original stage/checkpoint/report assertions remain intact.
This focused gate is not the new candidate's full suite or default dispatch.

Live read-only SEC80481 terminal0: `PYTHONPATH=. TMPDIR=<owned-run>/Tmp
.venv/bin/python <owned-run>/Results/check_sec_existing_env.py`, log
`<owned-run>/Logs/sec-current-existing-env.log`. The script uses python-dotenv
explicit existing root env before import and sets TRADINGAGENTS_CACHE_DIR to
`<owned-run>/Results/sec-current-cache`; uses approved fetch_current_sec_facts
bounded adapter and catalog AAPL, no monkeypatch/fallback/model/private DB.
Package6fff unchanged; only two tests/docs dirty. Actual requested
2026-10-07T08:37:50.333234Z/retrieved08:37:51.571954Z: **PASS** current acquisition,
OK/eligible_filed_facts,1,159 facts/0 invalid/latest filed2026-07-31. No raw contact,
keys or payload printed/committed; cache stays private. This is not authenticated
web/API storage, historical SEC vintage, AAPL full analysis or editorial proof.

### Default runtime native recording and bounded phase diagnosis

Clean source `939b5868886f90464c2f5d45d1891f097fc39576`:
external phase-only plugin5935 terminal0,48PASS/7PG prerequisite skips/75.27s.
Exact original four-file selection without plugin94109 terminal0,
48PASS/7skips/66.73s. Both use task-owned external TMPDIR and
`.venv/bin/python -m pytest -q tests/test_worker_runtime.py
tests/test_recording_factory.py tests/test_recording_sources.py
tests/test_recording_factory_lease.py --tb=short`; plugin additionally `-p
preflight_timing -s` and external Results on PYTHONPATH. Six measured child
imports5.076–12.692s, graph initialization0.228–0.644s,
fingerprint0.122–0.560s, SDK cleanup0.018–0.064s; clean target returns.
These samples identify import as dominant locally, not the cause of earlier
45-second failures. Original77978 FAIL is retained; limits/fences unchanged.

New `tests/test_default_recording_native.py` exercises actual default
`run_worker` with no engine injection, canonical immutable job payload,
original authenticated handler/source loading/per-run factory, original graph
and real parent checkpoint commits. Synthetic reviewed SDK responses forbid
HTTP; all required STAGES, saved report, original role/source/limit bindings,
original job/attempt checkpoint rows and child reaping are asserted. EN/VI/
bilingual each run on SQLite/PostgreSQL. This is ordinary recording only,
not owner continuation, a real portfolio approval or financial/VI semantics.

Source939b plus that new test, no other source changes during gate:
corrective helper74047 terminal0, **61PASS/377.27s**, Python3.14.7;
Ruff/pip-check/diff PASS, no skips; only labelled helper-owned DB removed.
Command: task-owned external TMPDIR, `TA_ALLOW_TEST_DB_RESET=1 bash
scripts/verify-postgres-local.sh --focused tests/test_default_recording_native.py
tests/test_worker_runtime.py tests/test_recording_factory.py
tests/test_recording_sources.py tests/test_recording_factory_lease.py`.
Initial helper28720 terminal1 failed Ruff test-import ordering before pytest;
correct only import order. Staged external SQLite precursor32108 terminal0:
3PASS/32warnings/75.19s, without later full-stage assertions or PG matrix.
Do not substitute either focused result for the new exact-SHA full baseline.
No owner runtime restart, paid run, provider/risk change, history mutation,
CI/main merge or deployment. NQ stays owner BLOCKED; AAPL SEC awaits actual
owner name/email, no placeholder contact used. Goal R01–R14 remains ACTIVE.

### Default recording integration after the exact preflight baseline

After full17294 finished, move original source loader and per-run factory into
the package. Default local runtime enables ordinary snapshot recording; engine
injection remains an explicit test seam. Handler loads owner original full
Decimal book/policy/risk bytes inside its authenticated run/job loading session,
preserves research.execution_started before preparation and the same observer,
then uses a per-run codec/store/supervisor without mutating its template. Legacy
CLI/live-tool behavior and original human/risk/continuation boundaries remain.
No restore/linked dispatch or paid permission is introduced.

Initial dirty integration at `af56a1e3228b0d5936adb8b22c1f5d4f69ef28da`,
normal focused77978 terminal1: **46PASS,7 PostgreSQL prerequisite skips,
2 setup errors,189.17s**. Selection: test_worker_runtime, test_recording_factory,
test_recording_sources, test_recording_factory_lease; scoped external TMPDIR,
`.venv/bin/python -m pytest -q ... --tb=short`. Ruff/diff PASS. Errors in native
sqlite-worker/sqlite-cancelled fixtures refuse on the initialized preflight's
45-second total ceiling. Children invoke neither model nor network; do not
promote old staged/full proof or rerun selected cases alone as a full acceptance.
Other concurrent machine workloads were observed, not established as the cause.
Next instrument bounded child preparation/fingerprint/cleanup/clean-exit timing
without bypassing admission, cleanup, cancellation or original allowance.
Default production native graph and owner journeys, new PG/full baseline and
financial/VI/live acceptance remain UNVERIFIED. No owner runtime was restarted
by this work, and no paid AI/provider/risk/private-history/CI/main/deploy action.

### Exact initialized preflight full regression and staged factory lease proof

Clean frozen `17294ddeb08f374079497ee1f24e0a132faee6b6`, full disposable
PostgreSQL78779 terminal0: **3,073PASS,88 subtests PASS,2 skips,443warnings,
1211.59s**, Python3.14.7. Command: task-owned external TMPDIR,
`TA_ALLOW_TEST_DB_RESET=1 bash scripts/verify-postgres-local.sh`.
Ruff/pip-check PASS; source/HEAD unchanged throughout and helper removed only
its labelled PostgreSQL. Skipped Bedrock dependency and live DeepSeek remain
UNVERIFIED. This is full local preflight proof, not default recording, owner
recovery/consent, financial/editorial/VI/live or release acceptance.

Staged external original owner source loader: independent corrective PG40080
terminal0,26PASS/5warnings/2.30s, Ruff/pip-check PASS. Includes22 source contract
fixtures and four real SQLite/PostgreSQL repository/blob cases: original book
Decimal, exact policy/risk bytes, owner refusal and unchanged original rows.
Initial PG10970 failed25/1 due duplicate canonical AAPL fixture UUIDs; unique
synthetic aliases fix fixture isolation without resetting history or assertions.
No correlation/coverage/risk-policy approval is inferred from recording input
admission. Staged factory74569:12PASS/5warnings/8.99s; its lease/ACK were mocked.

Expanded real factory lease/ACK56230 terminal0:10PASS/5warnings/59.41s; both
SQLite/PostgreSQL, actual current JobExecutionContext/claimed queue lease,
owner-readable snapshot loading, actual native SDK/graph preflight and parent
PrivateCheckpointStore callback. SDK/network invoke forbidden. Codec fixture
checkpoint commits idempotently, survives reopening, preserves original run,
and does not increment model starts. Expired/foreign-worker/cancelled/failed
heartbeat fences reject both ACK and checkpoint row. This does not execute or
interrupt/resume a real default graph/job, authenticate a browser or prove
financial output. Both candidate helpers remain external/not integrated.

First expanded14859 terminal1:9PASS/1FAIL/5warnings/35.70s, PG reopen failed
because str(SQLAlchemy URL) masks its password. Corrected reopen uses the same
original disposable connection configuration in memory only, not credential
printing/storage or an authentication bypass. Native assertions are retained.
Each helper removed only its labelled owned disposable database, separate from
the full helper. Commands: scoped external TMPDIR/PYTHONPATH,
`TA_ALLOW_TEST_DB_RESET=1 bash scripts/verify-postgres-local.sh --focused
<owned-run>/Results/test_recording_factory_lease.py --tb=short` (same selection
for source-loader file above). No paid AI/provider/risk/history/CI/main/deploy
action. Next integrate authenticated original sources + fresh per-run recording
while preserving entered-attempt uncertainty, original observer/lease/ACK and
explicit human consent; no automatic continuation/prefix rerun is authorized.

### Initialized SDK lifecycle root cause and isolated diagnostic

At clean `9de33344d6b03fc3fd01eff27d3e68a36f8ceef5`, Python3.14.7,
langchain-openai1.6.6/openai3.19.2, synthetic SDK diagnostic7886 terminal0:
distinct OpenAI roots share both sync/async underlying transports with the same
endpoint and timeout600, despite both declared custom transports being absent.
Closing the first closes the second; a third same-key SDK starts closed.
Installed `_client_utils.py` caches default transports using `lru_cache` keyed
by base URL, hashable timeout and socket options. This explains why the staged
cleanup-error injection passes alone but is never exercised after earlier tests
have closed the shared pool. Fresh SDK roots are not proof of transport ownership.
Do not solve this by clearing shared caches, modifying private SDK transports,
injecting custom transports behind the binding refusal or splitting the suite
into isolated cases and declaring the original in-process design safe.

Reproducer, in an isolated diagnostic process only, synthetic key, no request:

```python
import asyncio
from tradingagents.llm_clients.openai_client import NormalizedChatOpenAI
models = []
try:
    for _ in range(2):
        models.append(NormalizedChatOpenAI(model="synthetic", api_key="synthetic-only",
            base_url="https://example.test/v1", timeout=600, max_retries=1))
    assert models[0].root_client is not models[1].root_client
    assert models[0].root_client._client is models[1].root_client._client
    assert models[0].root_async_client._client is models[1].root_async_client._client
    models[0].root_client.close()
    assert models[1].root_client.is_closed()
finally:
    for model in models:
        model.root_client.close()
        asyncio.run(model.root_async_client.close())
```

External staged spawn diagnostic21995 terminal0: two sequential actual original
TradingAgentsGraph constructors plus existing initialized fingerprint binder
produce identical identities from identical synthetic original inputs. Partial
second SDK initialization refuses and disposes the reachable first pair; injected
first synchronous close failure refuses and attempts the other SDKs. Every child
exits0 and is joined; an actual parent SDK pair using the same endpoint/timeout
stays open throughout all four cases. HTTP sends and model invoke are forbidden.
Only test-owned resources are closed; no user runtime or private history changes.
Dummy quick/deep warnings are expected, not evidence of model capability.

Command: `PYTHONPATH=. .venv/bin/python <owned-run>/Results/check_isolated_sdk_preflight.py`.
Owned run: `/Volumes/Data/codex-builds/TradingAgents/fix-TA-R01-research-quality/20261007T052328Z-89163`;
candidate remains external at `Candidates/initialized_preflight.py` and is not
integrated. First harness75955 exit1 had an incorrect injection counter (counted
wrapper creation rather than get_llm); corrected harness counts actual SDK get
attempts, retains the model-count and cleanup-error assertions, then21995 passes.
Ruff PASS. No paid AI, provider/account check, source/code/runtime change.

Next: a bounded spawn-isolated production preflight retaining sanitized actual
identity only, original authenticated input binding, parent-loss handling,
startup/deadline/cancel/cleanup refusal, bounded IPC and child reaping. Then
default per-run recording and explicit owner continuation. The current staged
process test does not cover those integration/control-plane gates; they remain
UNVERIFIED. Existing full6db3053 receipt is unchanged and not promoted to them.

### Exact full corrective regression

#### Initialized preflight implementation after the isolation diagnostic

New internal `analysis/initialized_preflight.py` uses actual original graph/SDK
construction and existing fingerprint validation in a spawned child. Input is
bounded private JSON (4MB), not SDK/callback/DB/pickle; response is bounded JSON
(8KB), only fingerprint and validated node list. Parent validates exact observer
identity (request observer absent or the same object), keeps it out of the child,
and enforces its original time/cancellation/lease boundary plus a 45-second probe
ceiling. No model reservation/call, checkpoint/consent/continuation authority,
parent SDK cleanup or global-cache mutation. Parent-loss guard exits the child;
constructor/cleanup failures withhold identity, clean child exit and reaping are
required before return. Async event-loop callers and unreviewed providers refuse.
Full original immutable book/policy/source values bind after JSON reconstruction,
without converting book Decimal values through the lightweight LLM portfolio.
This prerequisite is not wired to the default handler/runtime or owner routes.

Dirty-source focused77211 terminal1:115PASS/1FAIL/28warnings/71.01s. Nonfinite
config control found Pydantic serializing NaN to null; pre-serialization JSON
validation now refuses the original value. Corrected15551 terminal0:
116PASS/28warnings/31.01s. After additional controls,88216 terminal1:
117PASS/1FAIL/28warnings/29.13s; Decimal fixture incorrectly replaced tuple cash
instead of CashBalance.amount. Fix the field, not its precision assertion.

Final6141 terminal0: **119PASS/28warnings/44.86s**, Python3.14.7, dirty source at
`6d41fc18b40d89e99f863dd62e9b0037992d81af`. Exact command, task-owned external
TMPDIR: `.venv/bin/python -m pytest -q tests/test_initialized_preflight.py
tests/test_initialized_graph_fingerprint.py tests/test_recording_context.py
tests/test_recovery_fingerprint.py --tb=short`. Repository Ruff/pip-check and
diff check PASS. Native cases exercise actual SDK/graph, with send/invoke forbidden,
two sequential identities and open matching parent SDKs, original book Decimal
amount changes below a float ULP, partial SDK initialization, injected close
failure, oversize/duplicate JSON, original observer budget/startup deadline,
owner cancellation after spawn, and child parent-loss guard with simulated dead
parent liveness. The latter is not proof of an OS-killed worker journey.
Invalid parent config, credentials, descriptors, source/observer, nonfinite values,
input cap and event loop refuse before spawn. No paid AI or private runtime change.

New clean-candidate full local/PostgreSQL proof remains UNVERIFIED until the
default full helper finishes. Previous6db3053 proof does not cover this module.
Default per-run recording, authenticated owner consent/linked dispatch, actual
worker-loss browser journey, financial/editorial/VI and live acceptance remain
unfinished. No default activation may skip those existing authority boundaries.

Clean frozen `2c80692b2b278f6272c67cfcb4a8ea7acf3a10d1`, session12988 terminal
exit0: **3,002 PASS,88 subtests PASS,2 optional-provider skips,443 warnings,
1470.92s**, Python3.14.7. Command: `TA_ALLOW_TEST_DB_RESET=1 bash
scripts/verify-postgres-local.sh` with TMPDIR in the task-owned external run.
Ruff/pip-check PASS. The helper removed only its labelled disposable PostgreSQL
container; process90750 is absent. No tracked bytes or HEAD changed during the
gate. Skipped Bedrock dependency and live DeepSeek checks remain UNVERIFIED.
This closes the corrected candidate's local full regression, not financial,
translation, default-owner recovery, live-provider or release acceptance.

### Social fact and word-percentage remediation still pending

At the same exact source, eligible original synthetic StockTwits/Reddit sample
counts compile and validate directly but financial review loses their resolver.
Ten valid draft/canonical count cases fail; two altered payload/manifest cases
are ignored by the review factory rather than reconstructed and refused.
Six unreferenced percent/per cent variants bypass the existing financial-number
lexer; eight date/period/qualitative and existing currency/% controls pass.
All diagnostics use local model/transport stubs, no vendor or paid AI calls.

External staged resolver/lexer modules plus a real eligible context fixture
pass62 focused assertions (36 existing+26 new), but are **not integrated** and
not normal clean-repository/native/full/live proof. Another original compiler
diagnostic accepts a social count as `The price is ${{QA}}.` while refusing `%`.
Therefore resolver parity must be paired with source-owned count meaning/units,
standalone/canonical checks and EN-VI preservation before integration. No
sentence blacklist, assertion relaxation, source/debate truncation or extra
review call. Original source and private history remain unchanged.

### Social count implementation candidate (after the full baseline)

The subsequent candidate adds original validated SocialFacts resolver parity,
source-owned standalone EN/VI count sentences, canonical/source checks and
protected localization. Counts cannot attest money/percent just through scalar
equality. Raw percent/per cent grammar is case insensitive; dates/period controls
remain. The context fixture now uses a real eligible synthetic collection and
manifest, retaining untrusted text and all original context-equality assertions.
No added graph/review call, debate/source cut, provider/policy change or historical
rewrite. This is implementation, not live/editorial/default recovery acceptance.

Dirty patch based on32de260: normal focused33705 exit0,121 PASS/3.60s. Expanded
15644 exit0:229 PASS/11 PostgreSQL prerequisite skips/14.38s; Ruff/pip-check and
diff check PASS. Selection: social_review_parity, financial_number_word_units,
financial_validation_stage, report_compiler, research_validation,
report_localization, social_snapshot_service, social_lookahead, macro_full_graph,
snapshot_macro_facts. Skipped PostgreSQL cases remain UNVERIFIED; new exact-source
native/full baseline still needs proof. Older full2c proof does not cover this
new implementation. Additional tests cover source-owned count translation,
wrong-money reattachment, canonical scalar collision, unknown labels, zero
label counts and bounded localization refusal.

Clean frozen implementation `b2aea55bfc3328e9ce4227df4bc6546cc4e7db61`, focused
disposable PostgreSQL82885 terminal exit0: **250 PASS,40 deselected,50 warnings,
187.18s**, Ruff/pip-check PASS. Same ten focused files above plus
test_native_recorder_spawn.py, selection `not test_native_recorder_spawn or
native_postgresql`. All eleven earlier PostgreSQL prerequisite skips execute
and pass here; ten original native PostgreSQL cases pass, with original trace
assertions unchanged. Forty other native cases were intentionally not selected;
this is not full regression. Source/HEAD stayed unchanged, and only the labelled
helper-owned container was removed. No paid provider/model call. Full regression,
live financial/VI quality and default-owner recovery remain UNVERIFIED/incomplete.

Clean frozen full candidate `6db21f2577e22e72081cea001542b24f183a8538`, default
disposable PostgreSQL61745 terminal exit0: **3,053 PASS,88 subtests PASS,2 optional
provider skips,443 warnings,980.35s**, Python3.14.7, Ruff/pip-check PASS.
`TA_ALLOW_TEST_DB_RESET=1 bash scripts/verify-postgres-local.sh`, with TMPDIR in
the owned external run; source/HEAD unchanged throughout. Only helper-labelled
PostgreSQL container removed. Bedrock dependency/live DeepSeek skips remain
UNVERIFIED. This proves the social/word-percent candidate's local full baseline,
not financial/editorial/live/default-owner or release acceptance.

### Exact native PostgreSQL corrective gate

Clean frozen code candidate `f64984db8338eb0eed69c820ab503bc65818159c`.
Focused helper46431 terminal exit0: **10 PASS,40 deselected,50 warnings,196.91s**,
Python3.14.7, Ruff/pip-check PASS. Selection:
`tests/test_native_recorder_spawn.py -k native_postgresql --tb=short -x`.
No skips in this selection; deselected cases are not a pass for the whole suite.
Exact original-prefix + restored-suffix model trace assertion remains unchanged.
Cases cover native separately restored child, linked portfolio and policy-fail
EN/VI/bilingual valid/invalid output plus cancel/expiry. Original immutable run,
accounting, approval gates and source array ordering are retained. The helper
removed only its labelled disposable PostgreSQL container; process89300 absent.
This confirms the ordering correction in the selected native matrix, not full
baseline, default-worker/browser recovery, live semantic or financial acceptance.

The existing qualitative evidence and translation-intensity diagnostics remain
unresolved. Full source input, numeric correctness and citation identity do not
prove semantic entailment or faithful translation. Default worker does not yet
activate owner-authorized durable continuation; internal native tests are not
default-owner/browser/live-operational proof. NQ=F remains owner BLOCKED without
contract/roll metadata. No paid AI, new provider, risk-limit change, CI, private
history rewrite, broker, public deployment or production-readiness claim.
