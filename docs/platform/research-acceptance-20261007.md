# Research continuation evidence — 2026-10-07

Branch: `fix/TA-R01-research-quality`; Draft PR #7, no release or main merge.

## Isolated recovery UI groundwork — not integrated

### Owner recovery controls and report projection

Source base `9e74a0ed497540c55842976d7c6d847217df2e7a` plus
`web/src/{Analysis,ContinuationPanel,continuationData}` source/tests,
`messages.ts` and `styles.css`; isolated branch `fix/TA-R08-continuation-ui`.
No preparation/reservation on mount. Explicit prepare, literal three-checkbox
consent, one reservation, authenticated discovery/progress/cancel, full linked
completion IDs before report projection. Retain original failed history and
invalid structured-report warning. Do not infer worker activity from a queued
reservation or financial approval from completion. No browser persistence of
consent, report bytes or secrets; existing language preference only.

Web26231 terminal0:26files/158PASS/78.83s:
`npm test -- --maxWorkers=1 --no-file-parallelism`.
Web4916 terminal0:typecheck/lint/build PASS, Vite8.3.1,298modules.
Both use existing shared installed dependencies, not clean-install proof.
Earlier failures are retained:84907/20636 duplicate new-attempt control (remove
duplicate app control, not query relaxation);83607 2FAIL/156PASS (integration
initial loading and untranslated Back);97426 7FAIL/151PASS (integration and
unchanged-module timeouts; no global cause established);69801 serial
1FAIL/157PASS, same new integration assertion while run loading.98063 focused
1PASS/5excluded did not prove full stability.26231 uses async React act for the
integration initial render; original 1s query deadline and assertions unchanged.
All retained fixture status remains failed, the new verified report is separate.

Browser94871 terminal0:loopback5174,1440x1000 desktop and390x844 mobile; original
failed run -> explicit prepare -> consent disabled until all three disclosures
acknowledged -> exactly one reservation -> linked active status -> cancellation
request -> verified completed report -> unchanged failed history -> VI.
Identity/nonblank/no framework overlay/console/overflow/interaction PASS.
Browser plugin not available; bundled regular Playwright fallback. All API and
EventSource are intercepted synthetic fixtures, no real backend/SDK/provider or
paid AI. Screenshots are private local QA artifacts, not cloud financial output.
First browser7182 failed on hidden unvalidated narrative: reader intentionally
keeps it behind explicit inspection. Correct the synthetic script to test the
warning, hidden text, and opening/closing disclosure; no validation gate relaxed.

Remaining before acceptance: complete event-page cursor consumption (current
has_more warning withholds a false partial stage summary), polish VI allowance
terminology and original-attempt labels, owner/refusal/completion/cursor matrix,
combined native/browser/PG and live financial/translation gates. Original full
5639 remains running on frozen clean6f60429 with failure markers; no side-source
integration while live. User8000/private runtime/history/provider/risk untouched.
R01–R14 ACTIVE, NQ owner BLOCKED; no release/main merge.

Additional isolated source base `0a24c70c7dc3af203cdd1fcf2120f8462c85fc0a`:
execution-linked bounded progress route/schema and expanded control tests.
Reads validate actual parent entry linkage plus owner/run/attempt/time, sanitize
to sequence/type/time/attempt/stage, preserve cursor/has_more and expose no raw
payload. Explicit `approval_eligible:false`; original terminal SSE is unchanged.
Local55728 terminal0:4PASS/2PG prerequisite skips UNVERIFIED/20.27s, command:
`python -m pytest -q tests/test_continuation_polling_control.py --tb=short -x`.
Ruff/diff PASS. Includes pagination/no original-attempt replay, unauthenticated/
unknown execution refusal, no preparation call, no read mutation, and corruption
of disposable entry actor rejected with sanitized409. First37286 terminal1:
1FAIL/5deselected/11.99s due newly inserted test capturing the old migration
test's restore lines (`url` undefined/F821). Restore lines returned unchanged
to their original test; no runtime guard/assertion weakened. This is synthetic
SQLite control evidence only; no PG/native/browser/live proof. Entire original
6f60429 full gate remains running with failures and fixed source.

While the full original `6f60429d701fb076104447ee82e0cd4f41e32fdc` gate remains
source-frozen and has emitted FAIL markers, a separate owned worktree/branch
`fix/TA-R08-continuation-ui` prepares the browser foundation without changing that
checkout. Added bounded owner continuation discovery (descending attempt cursor,
limit <=50, has_more), and attempt/report/evidence/decision IDs to the existing
validated state projection. Completion IDs come only from the existing full
completion/report reader. No SDK/model/consent/history mutation or runtime change.

Source base 6f60429 plus api/continuation_routes.py, api/schemas.py,
test_continuation_polling_control.py; matching README/CHANGELOG updated. Focused
SQLite55287 terminal0:1PASS/4deselected/25.99s; command:
`python -m pytest -q tests/test_continuation_polling_control.py -k 'owner_state and False' --tb=short -x`.
Ruff/diff PASS. Explicit module-path diagnostic confirms imports came from the
isolated worktree, not the frozen checkout. This is one synthetic SQLite control
case, not PG/native/full/browser/financial proof. Full original gate failure
tracebacks/totals are still pending; no assertion/deadline weakening or restart.
Discovery auth/error/refusal/completion pagination matrix, linked event projection,
professional UI and rendered journey remain UNVERIFIED. Do not integrate or enable
this candidate until the original frozen gate is terminal and its failures audited.

## Opt-in durable polling and authenticated control

Source base `0bcd76d39c4e9c2e0a2b2276bb7f3fb4562c095e` plus
analysis/linked_execution.py, reserved_preparation.py, preparation_refusals.py,
jobs/linked_worker.py, jobs/runtime.py, api/continuation_routes.py, api/schemas.py,
persistence/models.py, migration 0018, test_continuation_polling_control.py and
test_default_prepared_resume.py. Matching README/CHANGELOG/Product Contract updated.

Explicit `--continuations` consumes a reserved original continuation when ordinary
queue is idle. Default startup does not enable it. Original graph, identity,
allowance, source binding, entry/lease/renewal/ACK/report gates remain intact.
Preclaim refusal has a separate hashed durable receipt and is excluded across
reopen/restart; claimed uncertainty is never relabelled/refunded/requeued. HTTP
prepare/reserve `dispatch_enabled:false` means no direct HTTP model dispatch, not
a promise that an explicitly enabled worker cannot consume the reservation.

Owner status/cancel revalidates consent/run/execution without SDK construction.
Cancel serializes SQLite writes, cancels reserved attempts or requests leased
attempt cancellation; it cannot cancel completion or rewrite original history.
Completed status uses the existing full completion/report reader. Missing/corrupt
facts are review failures, not successful completion. Migration 0018 is additive
and explicit; rollback loses refusal receipts and must not enable retry. Only
disposable test DBs were migrated; real runtime remains unchanged.

Commands (same owned external TMPDIR as below):

```sh
bash scripts/verify-local.sh local --focused tests/test_continuation_polling_control.py tests/test_worker_runtime.py --tb=short -x
TA_ALLOW_TEST_DB_RESET=1 bash scripts/verify-postgres-local.sh --focused tests/test_continuation_polling_control.py tests/test_worker_runtime.py tests/test_linked_execution.py tests/test_continuation_api_contract.py tests/test_default_prepared_resume.py -k 'not manual' --tb=short -x
TA_ALLOW_TEST_DB_RESET=1 bash scripts/verify-postgres-local.sh --focused tests/test_default_prepared_resume.py -k worker --tb=short -x
```

Local59166 terminal0:10PASS/2PG prerequisite skips UNVERIFIED/3.66s.
PG1060 terminal0:76PASS/6manual deselected/12warnings/218.35s, no skips.
Final PG1797 terminal0:6PASS/6manual deselected/12warnings/207.17s, no skips.
The final selection adds authenticated completed-state and cancel-refusal checks
after real original runtime polling, all three languages/both dialects. Exact
original trace/output, retained accounting/history and review authority assertions
remain. Poison-reservation tests use an injected preparation failure (control
proof, not SDK failure proof). Empty migration reversal test is SQLite only.
Python3.14.7/Ruff/pip-check/diff PASS; source frozen during native gates; only
labelled helper-owned PG removed. No paid model/provider/user DB/CI activity.

**UNVERIFIED:** full current regression, rendered recovery controls/SSE journey,
leased-cancel races/all crash/ACK boundaries, semantic financial/VI, live BTC/AAPL,
release. **BLOCKED:** NQ owner contract/roll source. This is not a production-ready
claim. Old failed receipts remain below.

## Trusted worker operation and renewal/stop separation

Dirty source base `ff4d67b4a79340d11d5840485ff1f3019c38f6c0`:
reserved_preparation.py, jobs/linked_worker.py, shared terminal inputs,
linked publication renewal guards, default prepared/terminal tests, linked
publication/stops test expansions. README/CHANGELOG/Product Contract updated.
No stored browser credentials, caller codec or fresh allowance. Server-derived
SDK identity/full consent and original accounting precede separate one-time
claim; original graph, heartbeat, publication and human review stay authoritative.
No default polling/status/cancel/browser dispatch yet.

Final exact focused command:

```sh
TMPDIR=/Volumes/Data/codex-builds/TradingAgents/fix-TA-R01-research-quality/20261007T052328Z-89163/Tmp \
TA_ALLOW_TEST_DB_RESET=1 bash scripts/verify-postgres-local.sh --focused \
tests/test_default_prepared_resume.py tests/test_linked_publication.py \
tests/test_linked_stops.py --tb=short -x
```

PG24826 terminal0: **64 PASS**, no skips,84warnings/510.51s, Python3.14.7,
Ruff/pip-check/diff PASS, source frozen throughout, only owned labelled PG removed.
Original worker/manual EN/VI/bilingual native restore uses both SQLite/PostgreSQL;
full prefix+suffix prompt trace/output matches uninterrupted original graph.
Session revocation after consent does not require saved browser credentials.
Original job/run/checkpoint prefix and full usage/remaining limits preserved;
completion/report are separate, candidate remains REVIEW/human approval required.
Second worker refuses before SDK construction. Stop-native fixtures use SQLite;
command's PG context is not proof of native PG stop behavior.

Renewal uncertainty refuses normal entry/callback/publication, including the
post-write check. Exact binding remains usable only for actual reaped-child/
closed-pipe stop proof; no remote-stop, provider-cost, refund or continuation grant.
New native stopped/cancelled/expired tests require stop receipt with no final
completion/decision under injected renewal uncertainty and unchanged original run.
This is synthetic SDK/real graph and owned DB evidence, no paid model/live source.

Earlier gates: worker44091 SQLite3PASS/9deselected/6warnings/50.13s;
renewal50882 1PASS/1PG skip UNVERIFIED/35deselected/4.45s after F821 fixture
import correction. Broader pre-refinement PG39351:163PASS/24warnings/739.39s,
no skips (prepared resume, terminal/API, publication/execution/consent/preflight).
New stop fixture25474 initially FAIL1/12deselected/5warnings/41.85s because it
expected ordinary successful publication after injected renewal uncertainty.
Corrected new expectation requires exact publication refusal plus stop proof;
no application guard/assertion relaxation. SIM117 formatting corrected.
Corrective12838 3PASS/12deselected/15warnings/20.84s. All old failures retained.

**UNVERIFIED:** current clean full regression, durable polling/default browser
journey, financial/VI semantics, live BTC/AAPL and release. **BLOCKED:** NQ owner
active-contract/roll source. Next durable worker polling/owner status/cancel and
professional rendered recovery UX, then combined candidate/native/browser/full
and explicitly authorized live gates. Goal stays ACTIVE.

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

### Terminal preparation and retained linked factory integration candidate

Full clean frozen `c16620264c0da3e4877511e27c4dfb27d62debfe`, helper1098 exit0:
**3,133 tests+88 subtests PASS**,2 optional-provider skips UNVERIFIED,443warnings,
1536.90s/Python3.14.7; Ruff/pip-check/diff PASS, source/HEAD unchanged, only
own labelled PG removed. Command `TMPDIR=<owned-run>/Tmp TA_ALLOW_TEST_DB_RESET=1
bash scripts/verify-postgres-local.sh`, log
`<owned-run>/Logs/full-default-consent-accounting-c166202.log`. Same Bedrock extra
absent/DeepSeek live key skips as below. Local baseline is not default owner,
live or financial/VI semantic proof. After terminal integrate terminal preparation,
linked factory and tests. New integrated/source full evidence is pending.

External staged package c166, SDK replies synthetic/network forbidden:
38842 SQLite3PASS/3deselected/32warnings/40.14s for setup;95733 resume3PASS/
3deselected/38warnings/134.46s; guarded PG30138 exit0,6PASS/44warnings/326.73s,
both DBs/all languages, own PG cleanup and Ruff/pip-check/diff PASS. Original
default canonical stopped job -> explicit consent/allocation/claim -> staged
factory -> native full restore/completion. Full prefix+suffix model trace and
normalized output match uninterrupted graph. Old terminal run/job/checkpoint
prefix unchanged, exact accounting, separate completion/report and REVIEW/human
approval retained. Wrong context/missing publisher/changed config refuse before
dispatch. Initial52894 collection FAIL exit2/4.70s from wrong fixture import;
correct actual import, no trace/result/history assertion relaxation. Initial
external Ruff import-order FAIL fixed mechanically. Command: external Results
on PYTHONPATH, owned TMPDIR, disposable helper `--focused
<owned-run>/Results/test_default_linked_resume.py`.

Preparation41847 SQLite3PASS/3deselected/32warnings/24.45s; PG2924 exit0,
6PASS/32warnings/144.57s, own labelled PG removed, both dialects/languages;
helper `--focused <owned-run>/Results/test_default_terminal_preparation.py`.
Actual original owner inputs/SDK identity derive codec, not caller hash/codec.
Locked owner/session/CSRF validation changes no last_seen, DB locks released
before SDK work, original source/accounting/authentication rechecked afterwards.
Invalid auth/CSRF/unknown run refuse before SDK, no consent/execution/history
write, incompatible configuration refuses checkpoint. Initial Ruff C408 style
FAIL corrected without assertion changes. Composed87270 SQLite exit0,
3PASS/3deselected/38warnings/57.09s; external Results on PYTHONPATH/owned TMPDIR,
`.venv/bin/python -m pytest -q <owned-run>/Results/test_default_prepared_resume.py
-k sqlite --tb=short`. No fixture-supplied continuation codec, actual canonical
default stop through preparation/consent/claim/factory/full native resume/report.
These results do not prove new integrated source, default API/browser/worker,
portfolio readiness, paid/live or financial/editorial acceptance.

Integrated gate54068 terminal0: **85PASS/12warnings/560.65s**, no skips,
Python3.14.7; Ruff/pip-check/diff PASS, source/HEAD unchanged during QA and only
own labelled PG removed. c166 plus the two new package modules/two new tests
and four matching docs. Exact command `TMPDIR=<owned-run>/Tmp
TA_ALLOW_TEST_DB_RESET=1 bash scripts/verify-postgres-local.sh --focused
tests/test_default_terminal_preparation.py tests/test_default_prepared_resume.py
tests/test_initialized_preflight.py tests/test_default_recording_native.py
tests/test_continuation_consent.py`, log `<owned-run>/Logs/terminal-linked-integrated-pg.log`.
Actual default canonical stop through trusted preparation/consent/claim/factory/
full native restore/completion on both DBs/all languages; original full trace,
normalized result, old history, exact debit and human-approval assertions intact.
No paid/network request or enabled default API/worker/UI. New candidate full
suite UNVERIFIED; c166 full proof is not transferred. Continue default owner
integration, then corresponding exact candidate/native/browser/full gates.

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
# Original continuation API gate

Base `992c7bec75162545fbc62e0e6670b7a76ff4a022`, dirty source: new
`api/continuation_routes.py`, schemas/app mount, continuation store docstring,
native terminal test expansion and new `test_continuation_api_contract.py`.
README/CHANGELOG/Product Contract updated. Authenticated server-derived
preparation and explicit disclosure/consent/idempotent reservation implemented;
dispatch remains disabled. No model, original history or fresh allowance change.

Exact focused command (owned external run TMPDIR):

```sh
TMPDIR=/Volumes/Data/codex-builds/TradingAgents/fix-TA-R01-research-quality/20261007T052328Z-89163/Tmp \
TA_ALLOW_TEST_DB_RESET=1 bash scripts/verify-postgres-local.sh --focused \
tests/test_default_terminal_preparation.py tests/test_continuation_api_contract.py \
tests/test_platform_api.py tests/test_continuation_consent.py --tb=short -x
```

Helper66214 terminal exit0: **101 PASS**, no skips,223.88s. Python3.14.7,
Ruff/pip-check/diff PASS; code unchanged throughout; only helper-owned labelled
PG removed. Genuine original native graph/SDK with synthetic replies and real
SQLite/PostgreSQL auth/storage, all EN/VI/bilingual. No supplied browser codec,
paid SDK invocation or real private data. Original terminal history/accounting
and auth last_seen preserved; one idempotent reservation, no entry/claim/dispatch.
Route refusal before probe and fixed-error redaction tested separately.
Earlier local31429 34PASS/3PG cases deselected/134.51s; corrective85929
17PASS/3.11s. Initial13603 1FAIL/16PASS/3.21s was an invalid synthetic fixture
owner rewrite: immutable guard correctly refused. New distinct fixture run
corrects setup, not application policy. Initial F811 lint annotation corrected.

**UNVERIFIED:** current clean full suite, default linked worker/browser flow,
financial/VI semantics, live BTC/AAPL and release. **BLOCKED:** owner-selected
NQ active-contract/roll metadata. Goal remains ACTIVE; previous fullc166 is not
promoted to this candidate. Next wire trusted durable linked worker, owner
status/cancel/report and rendered UX, then combined exact-source gates.
