# TradingAgents — bàn giao 2026-09-27, tiếp nối 2026-10-03

## Cập nhật đang triển khai · 2026-10-03

**Isolated completed-continuation UI hierarchy (2026-10-07):** side worktree
`/Volumes/Data/codex/worktrees/ta-r08-recovery-ui/TradingAgents`, branch
`fix/TA-R08-continuation-ui`, dirty source on
`9c891f5a4c4b2af398d30d2b90f624db2cbacb5f`; primary full25685 source remains
frozen/unchanged. Fresh synthetic desktop1440×1000/mobile390×844 screenshots
showed the completed operational panel pushing the report down. Keep completed
heading/nonapproval notice visible; collapse explanation/selector/refresh into
native details with EN/VI label. Active/preparation/consent/cancel states and
validated report IDs, polling, all disclosures and backend authority unchanged.
Web3602 terminal0:typecheck/lint/164tests(27files)/build(299modules)/diff PASS,
Vitest14.31s. Browser plugin absent; existing Playwright, loopback5174 only,
all API/EventSource synthetic, no owner DB/model/provider request. Browser35385
terminal0:page identity/title/content, no overlay/errors/overflow, disclosure
open/close/refresh visibility, consent3/one reservation,101event paging,
cancel/completed/unvalidated report collapse and VI PASS on both viewports.
Completed panel height193.59desktop/249.59mobile; report heading y595.27/y1052.05.
Mobile report remains below first viewport; do not call the whole journey done.
First browser40479 FAIL used the English region name after switching to VI;
corrected only that fixture locator, no product guard loosened. Fresh screenshots
remain external under Logs/recovery-compact-{desktop,mobile}-completed-vi.png;
source/native/backend/live/editorial acceptance are separate. Goal ACTIVE.

**Exact93 recovery matrix PASS (2026-10-07):** clean frozen
`93cc6eab7f2a83b63770383de314a2cac33be9fc`, gate68162:
`TA_ALLOW_TEST_DB_RESET=1 bash scripts/verify-postgres-local.sh --focused tests/test_default_prepared_resume.py --tb=short -x`
terminal0:13PASS/24warnings/288.73s, Python3.14.7; Ruff/pip/diff PASS, no skips.
Covers the default stopped graph through explicit authenticated consent and
manual/worker continuation, EN/VI/bilingual × SQLite/PostgreSQL, exact full
trace/output/accounting/checkpoint/history/reaping plus linked authenticated
discovery/report IDs/events, and safe diagnostic redaction. Original deadlines,
source bindings, guards and human REVIEW remain. Only labelled helper-owned
disposable PostgreSQL was removed. TMP/logs stayed in the external managed run;
no live/paid model call or user history change. Source/HEAD unchanged throughout.
Full5894 remains FAIL and its preparation cause UNVERIFIED: the isolated/matrix
success is not proof of resolution. The next full clean candidate includes the
corrected canonical social review assertions and bounded preparation diagnostics.
Do not infer financial/editorial, actual browser/backend, live or release
acceptance from this synthetic native integration gate. Goal ACTIVE.

**Full5894 follow-up diagnostics (2026-10-07):** owned dirty candidate on
`5894be8295992040b9d761f4d70767f19f0dd771`; no production changes.
`python -m pytest -q tests/test_social_review_parity.py tests/test_financial_validation_stage.py --tb=short -x`
gate70007 terminal0:46PASS/1.95s. Canonical/draft social cases now require the
same full reviewed result and immutable source context, not a no-review shortcut.
`TA_ALLOW_TEST_DB_RESET=1 bash scripts/verify-postgres-local.sh --focused 'tests/test_default_prepared_resume.py::test_default_stopped_job_to_authenticated_consent[postgresql-en-vi-worker]' --tb=short -x`
gate63980 terminal0:1PASS/2warnings/73.07s, Python3.14.7, Ruff/pip/diff PASS;
only helper-owned disposable PG removed. Logs/TMP stayed in the managed external
run, with disposable connection URLs redacted. Native SDK/model fixtures are
synthetic; no paid/live call or private-history rewrite. Source/HEAD frozen for
the entire case. The full5894 preparation failure did not recur, so its root
cause remains UNVERIFIED; this is not a stability fix or replacement full gate.
Tracked test-only bounded exception-chain diagnostics are retained for the next
matrix/full run. Goal ACTIVE; financial/editorial/browser/live gates unchanged.
Final dirty5894 test-only gate78206:
`.venv/bin/python -m ruff check tests/test_default_prepared_resume.py tests/test_social_review_parity.py && .venv/bin/python -m pytest -q tests/test_social_review_parity.py tests/test_financial_validation_stage.py tests/test_default_prepared_resume.py::test_safe_exception_chain_omits_private_messages_and_locals --tb=short -x && git diff --check`
terminal0:47PASS/5.14s, Ruff/diff PASS. A preliminary bare `python` invocation
was unavailable in the shell; the repository's configured virtualenv was used
for the successful gate. This receipt is not an exact-clean-SHA full regression.

**Full5894 terminal FAIL (2026-10-07):** clean frozen
`5894be8295992040b9d761f4d70767f19f0dd771`, full PostgreSQL local helper10083,
Python3.14.7:6FAIL/3194PASS/2optional skips UNVERIFIED/480warnings/88subtestsPASS,
2756.02s, exit1. Ruff/pip PASS; script's post-pytest diff gate was not reached.
Source/HEAD unchanged throughout; helper-owned disposable PG removed. Log used
short traceback and redacted disposable DB URLs; raw QA data remains outside Git.
Five canonical social parity cases still expected an empty result/no review,
contradicting the newly approved mandatory canonical Financial validation path.
Update them to require exactly one structured review, exact complete canonical
output, unchanged social count statements/units/refs, original candidate retention,
empty diagnostics and full immutable source context for both draft/canonical.
No production source or review bound is changed by this test-contract update.

The sixth FAIL is
`test_default_stopped_job_to_authenticated_consent[postgresql-en-vi-worker]`:
`prepare_terminal_continuation` refused BEFORE consent/linked dispatch. It is not
the old consent-idempotency failure or an observed heartbeat failure. Root cause
UNVERIFIED; do not label it CPU/timeout solely from isolated success. Add the
existing safe exception-chain test diagnostic at terminal preparation: bounded
exception types/code locations only, no message/locals/credentials/input values,
and preserve actual SDK/DB/owner/accounting/clock/lease/budget behavior. Full
candidate remains FAIL; focused reproducer cannot replace it. Goal ACTIVE.

**R07 canonical review bypass removed; recovery exact gate PASS (2026-10-07):**
clean source `51be8f1e259bd0a5cc147038e355d0e525d4889e` recovery matrix90991
terminal0:94PASS/24warnings/467.29s, Python3.14.7, Ruff/pip/diff PASS. Covers
lease/publication and all default stopped/resumed EN/VI/bilingual × SQLite/PG ×
manual/worker, exact full trace/output/accounting/history/reaping plus authenticated
linked discovery/report IDs/events. Helper-owned PG removed. Synthetic SDK/model
only; this focused gate does not replace the earlier full6f consent FAIL or prove
live finance/editorial quality, combined actual browser runtime, or underlying
native heartbeat cause. Candidate source was unchanged until this gate ended.

Next R07 slice removes the legacy canonical early-return after mechanical checks.
Both canonical and draft reports now receive the existing Financial validation
review with complete immutable source context, strict same report schema and the
same bounded repair. No graph role/round/schema/evidence/source or risk limit is
removed; no history/checkpoint is rewritten. Default draft path has no added
call. A legacy canonical input formerly made zero review calls: now normally one
logical review, at most the existing second JSON-format repair, within original
caps. Transport/auth errors still propagate rather than funding format retries.
No paid run is authorized by this change; current provider/model unchanged.

Focused79319 on dirty51+R07 terminal0:418PASS/191.24s (financial validation,
compiler/localization and supervised full-graph fixtures). Cases prove that a
mechanically valid cited tax-causality claim cannot bypass review, invalid review
output cannot retain a ready canonical decision, and missing input stays missing.
The corrected review is a fixture response, NOT an actual model/editorial verdict.
Initial fixture FAILs were an extra nonmaterial evidence claim and a raw dict
standing in for schema-parsed SDK output; tests were corrected to obey existing
contracts, not by weakening publication checks. Full regression of the next clean
candidate remains UNVERIFIED until its exact gate ends. Goal ACTIVE.

**R08 lease lock-time race; verification incomplete (2026-10-07):** source base
`a33f19d7d0ed068fb76ba04b09509a0503bc6338`, owned dirty candidate. Integrated
native/API matrix83942:9PASS/1FAIL/436.07s, stopped early on PostgreSQL/VI/worker
trace assertion. Exact-case diagnostic68864:FAIL/142.34s; result was an execution
UUID, no new child, stale original trace. Diagnostic88843:FAIL/157.94s; new child
made9calls then stopped, preparation succeeded. Diagnostic2372:FAIL/186.08s;
new child made8calls, publication rejected `_renewal_failed`. Diagnostic46102:
1PASS/101.47s, no renewal failure observed. None proves a native stability fix.
All used synthetic SDK/model responses; no paid request or private history change.

A separate deterministic PostgreSQL interleaving proves a real fence bug:
heartbeat samples time, then another valid lease transaction commits before the
owner lock is acquired; the committed `updated_at` is incorrectly judged future
relative to the pre-lock instant. Original-source PG repro24569:1FAIL/3.10s.
Candidate refreshes the clock after owner/job/run locks, before execution-row
validation; rollback/future-time/expiry/token/original-budget checks remain.
Lease/publication gate8911:81PASS/36.78s on SQLite/PostgreSQL, including explicit
true-future refusal. First race fixture also selected SQLite and failed because
BEGIN IMMEDIATE already holds its writer fence; that invalid interleaving was
removed, not called evidence of the PostgreSQL bug. Source restored to the fixed
candidate after the original-source comparison; all gates terminal, helper-owned
databases removed. The observed native heartbeat exception's underlying cause
is still UNVERIFIED; do not equate it with this separately proven race.

Test-only diagnostics now report consent predicate booleans and bounded exception
types/code locations, never exception messages, locals, credentials or payloads.
Worker return type is checked before comparing stale/partial model traces.
Full6f consent-idempotency FAIL is still unresolved. Current full regression,
combined backend/browser/native and live financial/editorial acceptance remain
UNVERIFIED/FAIL as applicable; NQ remains owner-BLOCKED. Goal ACTIVE.

**R08 source integrated; consent failure still unresolved (2026-10-07):** after
both original full5639 and side native14008 were terminal, clean owned R01 branch
fast-forwarded to `a33f19d7d0ed068fb76ba04b09509a0503bc6338`. Main/release branch
not changed. R08 remote/history preserved. No port8000 listener at inventory,
no runtime or worker started; no private DB migration/history or paid provider.
README/coordination now distinguish integrated source from runtime acceptance.

External diagnostic46358 on exact clean6f:1PASS/11deselected/34warnings/27.21s;
existing consent-refusal hook logs predicate booleans only, no changed guard.
External numeric32174:1PASS/1.74s,208JSONB numeric samples, only negative-zero
representation hash drift observed. This is NOT proof that negative zero caused
the full native failure; full FAIL remains. Both helper-owned PGs removed.
Add tracked test-only predicate diagnostics to the existing duplicate-consent
assertion: capture the same real clock value used by record, compare row/source/
checkpoint/sequence/hash/payload/time flags if refused, then FAIL with flags only.
Do not print values/tokens/DB URLs, alter production code, relax fences, change
the equality assertion or substitute focused PASS for full FAIL. Next native
matrix/full rerun must establish the actual failing criterion or remain unresolved.

**Native linked reader matrix and full regression FAIL (2026-10-07):** isolated
base `d9030a361a7c6b399bb43195c3545cb03a667bc1` plus assertions in existing
default prepared worker test. Actual default worker resume, reaped child/full
trace/output/accounting/history/human REVIEW remain unchanged. Authenticated
discovery must return exact completed state/report/decision IDs; paginate real
linked events, only attempt2/sanitized fields, actual Portfolio Manager complete,
strict monotonic cursor and no extra SDK child.14008 terminal0:6PASS/6manual
deselected/12warnings/319.26s, EN/VI/bilingual × SQLite/PostgreSQL. Python3.14.7,
Ruff/pip/diff PASS, source/HEAD frozen, only owned helper PG removed. Native SDK/
model fixtures are synthetic, not paid provider or financial/browser acceptance.

Original full5639 terminal1 on clean frozen6f60429:3176PASS/88subtestsPASS,
1FAIL/2optional skips UNVERIFIED/480warnings/5209.66s. Exact failure:
`test_default_stopped_job_to_authenticated_consent[postgresql-en-vi-manual]`,
second identical `consents.record(**values)` refuses at continuation.py237
(existing-row integrity/time checks), not a preflight/SDK timeout. Root cause
not yet established; do not weaken timestamp/hash/payload/owner/budget fences
or declare it resource-only from focused success. Main6f targeted clean
reproducer started; preserve that source/HEAD while running, no side integration
yet. Full failure/raw runtime logs remain private external artifacts, not Git.
Full helper-owned PG removed; user DB/runtime/history untouched. Goal ACTIVE.

**Owner recovery reader contract (2026-10-07):** base
`43eada49b9d2cc58d85c86b88c0a1649b3b0a513` plus new
`tests/test_continuation_reader_contract.py`; no production source changes.
Foreign run hidden on discovery/state/events; expired/revoked/disabled auth
refused before SDK preparation; valid refusal visible, corrupt refusal sanitized
409; completion IDs require full report/decision/actor integrity. Original
run/job/events/checkpoint history unchanged by reads. Writer stop fixtures are
fabricated unit-only, not native or live evidence.
31915 terminal0:5PASS/4PG prerequisite skips UNVERIFIED/33.28s before adding auth
matrix.30565 terminal0:21PASS/114.66s, no skips, reader contract plus polling/control
on SQLite/PostgreSQL using labelled disposable helper DB. Python3.14.7/Ruff/pip
check/diff PASS; source frozen throughout; only helper-owned PG removed.
Original full5639 remains live/frozen6f with earlier failure markers. Combined
native/browser, wider corruption/race/restart coverage and live financial/VI
acceptance still pending; do not integrate while original gate is live. ACTIVE.

**Complete cursor UI reader (2026-10-07):** isolated base
`e1e1985d0ae93ec7804cc734271da3a2244d1e96`, not integrated into frozen R01.
Read all event pages; validate monotonic cross-page sequence/attempt and bounded
individual response bytes; no total-event truncation. Poll after validated cursor,
coalesce refresh during long reads instead of aborting them every interval. Only
selection/unmount aborts; error clears display/cache and retry starts from zero.
No private persistence, model/provider call or original-history change. Replace
VI allowance jargon with retained time/calls and label completed-linked original
detail as original attempt, not successful original processing. Long timeline
summary uses reduce, not unbounded Math.max argument spread.
Web3520 terminal0:type/lint +163PASS/27files/43.53s. Final68770 terminal0:
type/lint/build +164PASS/27files/40.26s,299modules. New cases cover101events across
pages/incremental cursor/repeated page/later failure/abort/coalescing/identity
isolation/error reset and150001event summary without truncation.
First type38746 failed new mock tuple typing, corrected signature;86009 lint
failed unused argument, corrected meaningful request-path assertion, no runtime
validation/assertion deadline relaxed. Original full5639 still live/frozen6f
with failure markers; exact terminal failure audit, native owner/browser/PG and
live financial/VI gates remain. Goal ACTIVE; NQ owner BLOCKED.

**Isolated recovery UI checkpoint (2026-10-07):** side branch
`fix/TA-R08-continuation-ui`, base `9e74a0ed497540c55842976d7c6d847217df2e7a`
plus the UI changes in the dated acceptance receipt. Explicit owner consent,
linked status/cancel and verified report projection preserve original failed
history and invalid-report warnings. Serial web26231 terminal0:158PASS/26files,
78.83s. Prior full serial69801 terminal1:157PASS/1FAIL; the new integration test
asserted before the history/detail/continuation promise chain settled. Use async
React act around its initial render, without deadline/assertion/fixture status
relaxation; browser94871 terminal0 both desktop/mobile synthetic EN/VI journeys.
All API/EventSource intercepted: no real SDK, paid AI or provider/worker evidence.
Original full5639 is still live on frozen clean6f60429, with earlier failure
markers, not a PASS. Do not integrate this side branch while that gate is live.
Remaining: consume all progress cursor pages (current warning is honest but
incomplete), polish VI allowance terminology/original-attempt labels, combined
native authenticated browser/PG tests and full original failure diagnosis.
R01–R14 remains ACTIVE; no main merge/deploy/runtime restart/history mutation.

**Opt-in polling and owner status/cancel (2026-10-07):** source base
`0bcd76d39c4e9c2e0a2b2276bb7f3fb4562c095e` plus polling/control/refusal changes
listed in `docs/platform/research-acceptance-20261007.md`. Explicit operator
`--continuations` uses the original trusted worker after ordinary queue priority;
default startup remains ordinary-only. Durable preclaim refusal prevents repeated
polling/claim across restart. Owner status/cancel requires authentication, mutation
CSRF/Origin; no SDK for control. Completed status requires full separate report/
receipt validation; cancel cannot change a completed result. Original history,
accounting, graph and human approval remain unchanged. Migration 0018 is additive,
explicit, and not applied to the user's runtime here.

Local59166 terminal0:10PASS/2PG prerequisite skips UNVERIFIED/3.66s.
PG1060 terminal0:76PASS/6manual cases deselected/12warnings/218.35s, no skips.
Final PG1797 terminal0:6PASS/6manual cases deselected/12warnings/207.17s;
actual default runtime polling and post-completion authenticated API assertions
run EN/VI/bilingual on SQLite/PostgreSQL. Python3.14.7/Ruff/pip-check/diff PASS,
source frozen during each native gate, only helper-owned PG removed. This is
dirty-source focused evidence, not full current regression, live financial/VI,
browser journey, release or operational acceptance. Prior fullc166 not promoted.
No paid AI, user runtime restart/history mutation, CI/provider/risk/main/deploy.
Next professional browser recovery controls/status/layout and original-terminal
versus linked-active event projection, then combined/full/native/browser gates.
Goal R01–R14 ACTIVE; NQ owner BLOCKED.

**Trusted single-execution worker continuation (2026-10-07):** base
`ff4d67b4a79340d11d5840485ff1f3019c38f6c0` plus reserved_preparation.py,
jobs/linked_worker.py, shared original terminal input loader, renewal guards and
four existing test expansions. Durable reservation preparation needs no browser
session token: recheck active owner/original job/run/inputs/full accounting,
derive actual SDK identity, then validate full consent/checkpoint observation
before a separate one-time claim. Worker assembles retained context/original
sources/bound publisher/factory, heartbeat, original graph restore and separate
report. ACK uncertainty never grants retry; original terminal history and caps
are unchanged. Default polling/status/cancel/browser dispatch remain unfinished.

SQLite worker44091 terminal0:3PASS/9deselected/6warnings/50.13s, full prompt
trace/output equals uninterrupted baseline, login revoked after consent, exact
aggregate usage, original history/checkpoint prefix, REVIEW/human approval and
second-worker refusal retained. First renewal helper failed at F821 (wrong test
exception import), corrected existing CheckpointStoreError without runtime change;
50882 terminal0:1PASS/1PG skip UNVERIFIED/35deselected/4.45s. Broader PG39351
terminal0:163PASS/24warnings/739.39s, no skips, before stop-control refinement.
Selection: default prepared resume, default terminal/API preparation, linked
publication/execution, continuation consent and initialized preflight.

Renewal uncertainty is now a normal-entry/callback/publication gate, not a
binding-identity failure: actual child reaping/pipe shutdown can still produce
control-only stop proof. First SIM117 lint refusal corrected mechanically.
25474 terminal1:1FAIL/12deselected/5warnings/41.85s: new successful-stop fixture
injected renewal failure before final publication and correctly got
RESEARCH_EXECUTION_FAILED instead of its usual success. Corrected that new case
to require exact publication refusal, no completion/decision and unchanged
original run; cancellation/expiry and existing assertions unchanged. Corrective
12838 terminal0:3PASS/12deselected/15warnings/20.84s, actual stopped/cancelled/
expired child stop proof with no continuation/provider-cost authority.

Final source-frozen PG24826 terminal0:64PASS/84warnings/510.51s, no skips;
Python3.14.7, Ruff/pip-check/diff PASS; only labelled helper-owned PG removed.
Selection: default_prepared_resume, linked_publication, linked_stops (--tb=short
-x). Worker/manual EN/VI/bilingual restore runs both DBs; stop-native fixtures
are SQLite and are not promoted to PG native-stop proof. This is dirty-source
focused evidence, not clean full regression, default polling/browser recovery,
semantic financial/VI, live BTC/AAPL or release acceptance. Full current candidate
UNVERIFIED, previous fullc166 not promoted. No paid AI, market-provider/risk/model/CI/
private-history/main/deploy change. R01–R14 ACTIVE, NQ owner BLOCKED.

**Original continuation API integration (2026-10-07):** source base
`992c7bec75162545fbc62e0e6670b7a76ff4a022` plus continuation_routes.py,
strict schemas/app mount, continuation store docstring, native API journey and
test_continuation_api_contract.py; README/CHANGELOG/Product Contract updated.
Owner preparation closes read-only auth locks before actual bounded SDK identity;
reservation rederives identity and requires current digest, idempotency UUID,
literal confirmation and all three disclosures. Original immutable sources,
allowance/accounting/history stay unchanged; dispatch_enabled false. No default
linked worker/browser control or decision approval is enabled.

Local31429 terminal0:34PASS/3PG cases deselected/134.51s. Extra refusal schema
85929 terminal0:17PASS/3.11s. Initial13603 FAIL1/16PASS/3.21s: fixture attempted
to change original run owner and immutable-record guard correctly refused;
corrected by creating a distinct synthetic run, no guard/assertion relaxation.
Initial Ruff F811 import/fixture naming corrected with explicit pytest fixture
annotation. PostgreSQL helper66214 terminal0:101PASS/223.88s, no skips,
Python3.14.7/Ruff/pip-check/diff PASS; source unchanged during gate, only labelled
helper-owned disposable PG removed. Selection: default_terminal_preparation,
continuation_api_contract, platform_api, continuation_consent (--tb=short -x).
Actual original graph/native SDK synthetic replies, both DBs/all languages:
auth/Origin/CSRF/unknown/foreign run refusal, strict disclosures, stale digest,
idempotent single reservation, unchanged last_seen/original run/job/checkpoints/
events/accounting; no paid AI. This is dirty-source focused API/native evidence,
not clean full-candidate regression, rendered browser recovery, financial/VI
semantics, live BTC/AAPL or release. Full current candidate UNVERIFIED; previous
fullc166 not promoted. Next trusted durable linked worker (no stored browser
session token), status/cancel/report and professional owner UX, then combined
native/browser/full gates. R01–R14 ACTIVE, NQ owner BLOCKED.

**Terminal preparation / linked factory integration (2026-10-07):** clean frozen
`c16620264c0da3e4877511e27c4dfb27d62debfe`, full PG1098 terminal0:
3,133 tests+88 subtests PASS/2 optional-provider skips UNVERIFIED/443warnings/
1536.90s; Python3.14.7, Ruff/pip-check/diff PASS. Source/HEAD unchanged, only
labelled helper-owned PG removed. This is full local baseline, not default owner
continuation, financial/VI/live or release proof. After terminal, integrate
analysis/terminal_preparation.py, analysis/linked_factory.py and actual default
native tests. Original authenticated inputs/actual SDK-derived codec, no last_seen
update/DB locks across SDK work, source/accounting/auth recheck; linked factory
requires retained observer/private lease/exact identity/bound result publisher.
No default API/linked worker/UI route yet. New integrated/full gates pending.

Staged c166: setup38842 SQLite3PASS/3deselected/32warnings/40.14s; native resume
95733 SQLite3PASS/3deselected/38warnings/134.46s; guarded PG30138 terminal0,
6PASS/44warnings/326.73s (both dialects/all languages, only own PG removed).
Complete prefix+suffix trace/result match uninterrupted original graph, original
terminal run/job/checkpoint prefix preserved, exact accounting and separate
completion/report; REVIEW/human approval retained. Initial52894 wrong fixture
import collection FAIL exit2/4.70s; corrected actual import, no assertion relaxation.
Initial external Ruff import-order FAIL corrected mechanically.
Terminal preparation41847 SQLite3PASS/3deselected/32warnings/24.45s; guarded
PG2924 terminal0,6PASS/32warnings/144.57s (auth/CSRF/unknown-run refusal before
SDK, unchanged last_seen/no consent/execution, changed-config refusal). Initial
Ruff C408 style FAIL corrected without assertion change. Composed87270 SQLite
3PASS/3deselected/38warnings/57.09s: no fixture-supplied continuation codec,
actual default stop -> preparation -> consent/claim -> native full resume/report.
All SDK responses synthetic/network forbidden. Package unchanged during staging;
new integrated proof pending. No paid AI/provider/risk/CI/private-history/main/
deploy change. R01–R14 ACTIVE, NQ owner BLOCKED. Next integrated PG/source gate,
trusted API observation/consent, durable linked worker/status/cancel and owner UX.

Integrated corrective source gate54068 terminal0:85PASS/12warnings/560.65s,
no skips; Python3.14.7, Ruff/pip-check/diff PASS, only own labelled PG removed.
Exact source: c166 plus new linked_factory/terminal_preparation, two default
native tests and these four docs; unchanged throughout. Selection: default
terminal preparation, default prepared full resume, initialized preflight,
default ordinary recording and continuation consent. Both DBs/all languages
run in new native tests; full trace/output equality and original authority/
history/accounting assertions retained. New clean candidate full suite remains
UNVERIFIED; old fullc166 is not promoted. Continue API/worker integration next,
then its candidate/native/browser/full gates before owner/live acceptance.

**Full default recording baseline and stopped-consent bridge (2026-10-07):**
clean frozen `6fff558d6666fc365a6bfdc1bc20a1e5d1c73f84`, full disposable-PG
helper46603 terminal0: 3,127 tests+88 subtests PASS,2 optional-provider skips
UNVERIFIED,443warnings/3005.82s; Python3.14.7, Ruff/pip-check/diff PASS.
Source/HEAD unchanged throughout; only helper-owned labelled PG removed.
This proves the full local baseline, not financial/VI semantics, live providers
or default owner continuation. Earlier77978 timeout FAIL remains retained.

External actual default stopped-job candidate at that SHA: corrected
SQLite62224 terminal0,3PASS/3deselected/32warnings/36.06s; isolated PG68953
terminal0,6PASS/32warnings/124.77s, both dialects/all three languages.
Real original graph/checkpoint commits, synthetic SDK and post-commit ACK loss;
accounting retains exactly1 started call/15 tokens, terminal history/checkpoint
bytes unchanged by explicit authenticated/idempotent consent. Invalid CSRF and
false confirmation refuse. No allocation/claim/dispatch/resume or paid grant.
Initial84362 FAIL3: callback-disabled synthetic fixture reported0 calls; use
existing callback fixture, retaining1/15 assertions. Initial PG10289 FAIL2/
4PASS/75.66s: shared QA DB correctly refused a second owner bootstrap; isolate
explicit disposable DB between cases, no auth relaxation. Candidate now added
as `tests/test_default_stopped_consent.py`; successful default graph test now
adds callback/trace/accounting equality. New integrated/full evidence pending.

Integrated two-file disposable-PG81182 terminal0:12PASS/115.03s, no skips;
Ruff/pip-check/diff PASS, source6fff plus only these two tests and receipts,
unchanged throughout QA. Successful default graph accounting matches complete
native trace/15 tokens per callback in all languages/dialects; original stages
and checkpoint/report assertions retained. New candidate full gate still pending.

SEC configuration correction: presence-only inspection on2026-10-07 finds an
email-shaped SEC_EDGAR_USER_AGENT in the root checkout's ignored `.env`, while
the active worktree has no `.env`. Earlier worktree-only absence is not evidence
the owner never supplied contact. Existing explicit dotenv-path startup procedure
in `docs/platform/local-web-startup.md` applies; no populated env copied, raw value
printed, runtime restarted or current live SEC access established. R01–R14 stays
ACTIVE; NQ remains owner BLOCKED. No paid run/provider/risk/CI/main/deploy change.

Read-only live SEC80481 terminal0 subsequently used the existing explicit root
dotenv path and isolated external QA cache through the approved bounded adapter:
2026-10-07T08:37:50.333234Z–08:37:51.571954Z, AAPL OK/eligible_filed_facts,
1,159 facts/0 invalid/latest filed2026-07-31. No mock, fallback, AI invocation,
owner DB/snapshot mutation or raw contact/key output. Package source remains6fff;
only tests/docs dirty. This proves current SEC acquisition, NOT authenticated
web preparation, AAPL full graph/output, historical vintage or semantic quality.

**Default runtime native proof (2026-10-07):** source
`939b5868886f90464c2f5d45d1891f097fc39576` plus new
`tests/test_default_recording_native.py`, otherwise unchanged during QA.
Corrective disposable-PG helper74047 terminal0:61PASS/377.27s; Ruff/pip-check/
diff PASS; only its labelled container removed. Actual default run_worker,
canonical original job payload, original handler/factory/graph and real parent
checkpoint DB/ACK run in EN/VI/bilingual on both SQLite/PostgreSQL. All required
STAGES complete, checkpoint rows bind original job/attempt, sources/limits/roles
stay bound, report saved and owned children reaped. SDK replies are synthetic;
no provider/network invocation, engine injection or continuation grant.
Initial helper28720 failed at Ruff import ordering before pytest; corrected
test imports, no runtime/assertion/timeout relaxation. Full current baseline,
owner recovery and financial/VI/live acceptance remain UNVERIFIED.

Timeout investigation on clean939b: instrumented5935 terminal0,48PASS/7PG
prerequisite skips/75.27s; exact uninstrumented94109 terminal0,48PASS/7skips/
66.73s. Six child imports5.076–12.692s, graph0.228–0.644s,
fingerprint0.122–0.560s, cleanup0.018–0.064s. No previous45s refusal reproduced;
import dominated these samples but earlier timeout causality remains unknown.
Retain original77978 FAIL; no deadline increase, caching bypass or partial-flow
claim. External diagnostic/logs remain private, not Git. See dated receipt.

**Default recording integration candidate (2026-10-07):** after full17294
terminal0, integrate staged original source loader/factory and tests into repo.
Default runtime enables recording for snapshot jobs; explicit engine injection
retains its testing seam. Handler loads original owner book/policy/risk bytes,
keeps entered research fence + same observer, creates per-run engine/codec and
parent-fenced store callback; template/CLI/legacy tools/history unchanged.
Dirty source ataf56a1e: first normal77978 terminal1,46PASS/7PG prerequisite
skips/2 setup errors/189.17s. Both errors are 45-second initialized preflight
deadline refusal in sqlite worker/cancel lease fixtures; no provider invoke.
All skipped PG cases UNVERIFIED. Repository Ruff/diff PASS. Do NOT hide errors,
relax deadline/fences or call this default-flow acceptance. Machine parallel load
was observed but causality is not established. Next measure child constructor/
fingerprint/cleanup/exit timing, fix actual cause, then production-path native,
PG/full and owner browser recovery gates. No user runtime restart, paid run,
provider/risk/history/CI/main/deploy action; goal ACTIVE.

**Initialized preflight full baseline (2026-10-07):** clean frozen
`17294ddeb08f374079497ee1f24e0a132faee6b6`, helper78779 terminal0:
3,073 tests+88 subtests PASS/2 optional-provider skips UNVERIFIED/443warnings/
1211.59s; Ruff/pip-check PASS. Tracked source/HEAD unchanged throughout;
only helper-owned labelled PostgreSQL removed. This closes the initialized
preflight's local full baseline, not default recording/owner continuation or
financial/VI/live acceptance. Source can now change for the next integration.
Staged original source loader: corrective independent PG40080 terminal0,
26PASS/5warnings/2.30s, including four real SQLite/PostgreSQL owner/Decimal/blob
cases. Staged factory:12PASS; real lease/DB/ACK factory56230 terminal0,
10PASS/5warnings/59.41s, native SDK preflight and both DB dialects. Real lost
lease/worker/cancel/heartbeat fences refuse rows/ACK, idempotent checkpoint
survives reopen, original run unchanged and no model starts. Checkpoint bytes
are codec fixtures, not generated by a default job or a resumed graph. Reopen
fixture correction retains original connection configuration in memory, never
prints credentials. Both candidates remain external/not integrated. Next wire
original authenticated inputs and per-run factory into default handler/runtime,
then actual default native graph and owner journeys. No paid run, CI/provider/
risk/private-history/main/deploy action; R01–R14 ACTIVE, NQ owner BLOCKED.

**Initialized identity implementation (2026-10-07):** internal
`analysis/initialized_preflight.py` now stages the actual graph/client identity
in a spawn-only child, bounded JSON4MB/reply8KB, 45-second preparation ceiling
within the original observer allowance, cancellation/lease checks and reaping.
Cleanup and clean exit must precede acceptance; no SDK crosses to/gets closed
in the parent. Parent-loss guard and fixed errors; no model call/paid grant.
Default per-run recording/owner dispatch are NOT integrated. First expanded
focused77211 FAIL:1/115PASS, caught nonfinite config normalization; corrected
pre-serialization finite/JSON refusal. Focused15551 terminal0:116PASS/28warnings/
31.01s, Ruff/pip-check PASS, dirty source at6d41fc1. Final6141 terminal0:
119PASS/28warnings/44.86s; repository Ruff/pip-check/diff PASS. Includes native
original-book Decimal precision and parent observer preservation, codec-node,
event-loop, input-cap, deadline/cancel/parent-loss/IPC and SDK cleanup controls.
One intermediate88216 FAIL was a test fixture assigning Decimal to tuple cash;
corrected the actual CashBalance.amount, retaining exact precision assertion.
This remains dirty-source focused evidence until a new clean full gate;
older full6db3053 is not promoted. Source baseline/local native/default
owner/financial/VI/live acceptance remain separate and incomplete.

**Social count full baseline:** clean frozen
`6db21f2577e22e72081cea001542b24f183a8538`, full PG61745 terminal0:
3,053 tests+88 subtests PASS/2 optional-provider skips UNVERIFIED/443warnings/
980.35s; Ruff/pip-check PASS. Source/HEAD unchanged, only helper-owned PG removed.
Social/word-percent code now has full local baseline; no promotion to broader
semantic financial/VI, default-owner recovery or live acceptance. Default worker
still lacks per-run recording configuration. A real synthetic partial SDK-init
diagnostic leaves reachable sync/async clients open; diagnostic cleans its own
resources. External owned-preflight candidate is not integrated: its failing
cleanup case exposed cached shared HTTP transports in langchain-openai1.6.6.
Fresh SDK roots do not own independent pools; closing one closes another and
the next same-endpoint/timeout SDK starts closed. Never close a parent probe's
default pools or clear global caches to hide this. Spawn diagnostic21995 exit0
uses actual graph/client binding: two sequential identities match, partial-init
and cleanup-error paths refuse, each child is reaped and a parent borrowed
sync/async SDK stays open. This is local diagnostic evidence, not integrated
worker, cancellation/deadline/IPC/consent or live acceptance. Next implement
bounded isolated initialized preflight, integrate per-run
authenticated recording and preserve consent/lease/ACK/usage/history boundaries.
NQ owner BLOCKED; no paid AI/provider/risk/CI/history/main/deploy action.

**2026-10-07 social count candidate:** compiler/review now share eligible original
SocialFacts; complete source-owned EN/VI count sentences retain vendor/sample/
user-label meaning, reject reattached money/probability/neutral meanings and are
rechecked in canonical publication and protected localization. Counts cannot
attest monetary/percentage observations through scalar equality. Word-percent
lexer covers percent/per cent without matching dates/periods. Complete-source
fixture uses a real eligible collection/manifest; original assertions retained.
Dirty patch at32de260: focused33705 terminal0,121 PASS/3.60s; expanded15644 terminal0,
229 PASS/11 PG prerequisite skips/14.38s; Ruff/pip-check/diff PASS. New exact-source
PG/native/full proof remains UNVERIFIED, prior full2c is not promoted. Remaining
financial/translation/default-owner/live/R01–R14 gates stay open. No paid AI,
provider/risk/graph change, history rewrite, CI, merge or deployment.

**Social count exact-source PostgreSQL/native proof:** clean frozen code
`b2aea55bfc3328e9ce4227df4bc6546cc4e7db61`, focused82885 terminal0:
250 PASS/40 deselected/50warnings/187.18s, Ruff/pip-check PASS. Ten focused
validation/source/translation/macro files plus original native_postgresql matrix;
all11 earlier PG prerequisite skips run here, selected native10 pass with original
trace assertions. Source/HEAD stayed fixed, only helper-owned PG removed. Other40
native cases and new full baseline are not proven by this selection. R01–R14
financial/VI semantic, default-owner recovery and live acceptance stay open; NQ
owner BLOCKED. See receipt20261007 for exact selection and limitations.

**2026-10-07 full corrective baseline:** clean frozen
`2c80692b2b278f6272c67cfcb4a8ea7acf3a10d1`, full local PG12988 terminal0:
3,002 tests+88 subtests PASS,2 optional-provider skips UNVERIFIED,443warnings,
1470.92s; Ruff/pip-check PASS. Only labelled helper-owned PG removed, process90750
absent; source/HEAD unchanged throughout. This closes the ordering correction's
full local regression, not financial/translation/live/default-owner acceptance.
New synthetic diagnostics: review omits admitted SocialFacts resolver (10 valid
count cases rejected;2 malformed-source controls ignored);6 percent/per cent
spellings evade raw-number gate (8 controls pass). External staged modules pass
62 focused assertions but are not integrated. Compiler also permits a social
count as a price amount: do not integrate resolver-only correction. Next pair
validated resolver parity with source-owned social count statements, canonical
and EN-VI preservation, plus word-percent lexer/tests; then normal source gates.
Remaining R01–R14 is ACTIVE, NQ owner BLOCKED. No paid AI, provider/risk/graph cut,
history rewrite, CI, merge or deployment. See receipt20261007 and PR7 comments.

**2026-10-07 corrective native proof:** clean frozen
`f64984db8338eb0eed69c820ab503bc65818159c`, focused PG46431 terminal0,
10 PASS/40 deselected/50warnings/196.91s; Ruff/pip-check PASS. Exact model-trace
parity assertions were not changed. EN/VI/bilingual linked portfolio/policy-fail
and cancel/expiry cases pass; only owned QA container removed. Old full2135298
FAIL is preserved below. Full baseline for the corrected candidate remains
UNVERIFIED until a new default full gate finishes; no promotion to default-owner,
financial, translation or live acceptance. See dated receipt20261007.

**2026-10-07 regression recovery:** old full88563 handle is now missing and no
process90612 remains. Retained exact2135298 log reports **FAIL:8 failed,2993
passed,2 skips,+88 subtests,443warnings,1525.69s**, helper-owned PG removed.
All failures are native linked-portfolio PostgreSQL prompt-trace parity at
test_native_recorder_spawn.py:457, financial-review index17. Do not describe this
candidate as full-regression PASS. Combined review sources previously flattened
role dictionaries in insertion order; PostgreSQL JSONB reload can reorder those
keys. Candidate fix sorts role/object keys, not record arrays or source values;
adds exact prompt-equality/reordered-key and retained article-order regression.
Focused68628 terminal0:36 PASS/3.16s, Ruff/pip-check PASS. Native PG trace gate
and full baseline still require new exact-source proof; no assertion relaxed.
Semantic price-only claim and translation-qualifier diagnostics remain FAIL
editorially despite mechanical acceptance, as recorded in PR7 comments5971022650
and5971047550. Default worker still does not activate checkpoint continuation;
R01–R14 stays ACTIVE, NQ owner BLOCKED. No paid retry, private-history change,
provider/model/risk change, CI, merge or deployment.

**Financial-review source context checkpoint:** review previously received the
draft/instrument fact catalog but not complete selected source records. The
existing review prompt now includes all original immutable records as explicitly
untrusted evidence, without truncating history/posts/articles or adding a call.
Prompt distinguishes facts/opinions/hypotheses and forbids interpreting citation
existence as entailment. Focused69501 terminal0:35 PASS/3.21s, Ruff/pip-check PASS.
Test checks exact parsed source equality, complete long article tail, all price
rows/social text, unchanged one-call draft path. This is input-contract proof,
not successful live entailment or prompt-injection resistance. Larger review
context may increase input tokens; model/provider/graph/approval remain unchanged.
Full exact-source gate must finish before new acceptance or financial claims.

**Compact preparation checkpoint:** instrument/time/language share one row;
Exact clean candidate `7a5a3c56b304fc119e6fa6d48ef044f10a63f547` is on origin;
post-commit web70101 terminal0: typecheck/lint/152 tests PASS,9.31s.
optional sources use a responsive grid. Choose saved sources opens and focuses
the existing inspector without collecting/selecting/authorizing. Web28750
terminal0: typecheck/lint/152 tests/build PASS (8.45s tests), output setup-web in
managed run20261003T155818Z-87783. Native in-app real owner API/synthetic QA on8019
observed focus transfer, explicit price selection/consent, fixture source failure
retaining prices and resetting consent/disabled Queue; no job submitted. VI mobile
390×844 scrollWidth390, no console errors. No model/vendor, backend or user8000
change. This is scoped UX evidence, not full R01–R14/professional/financial acceptance.
Full backend proof remains at f7bca47; NQ remains owner BLOCKED.

**Exact web candidate verified:** clean
`52e7d9b24d05955fe14f95b7850a3b6ad53aa17b`, Node26.8.1; final web78992 terminal0
typecheck/lint/**150 tests PASS**/build. Output review-exact-web is byte-identical
to the review-web assets inspected above/below via in-app browser (diff -rq exit0).
No Python/package/dependency change in this UI slice; full backend receipt stays
bound to f7bca47. No production-ready claim or user8000 restart. See PR7's exact
continuation checkpoint; current tracked docs preserve previous source receipts.

**Report/review UX implementation checkpoint · 2026-10-03:** the candidate
containing this entry moves review readiness/actions before the saved report,
keeps missing-risk/run-mismatch refusal visible, removes duplicate report heading
and Decisions self-link, and reduces nested reader panels/padding. The exact
canApprove expression, explicit confirmation/reason/idempotency and backend
authority remain unchanged. Analysis keeps its bound decision link; source
coverage, saved EN/VI prose and Verification stay available. Web37463 terminal0:
150 tests/typecheck/lint PASS; build84487 terminal0 to owned review-web output.
Fresh in-app real API/synthetic saved report at8019: desktop1280×720 and
mobile390×844, readiness before report/disabled approval/no self-link, saved VI
→EN/198.02 unchanged and Verification→Summary PASS; no overlay/console error,
mobile scrollWidth390. Six accepted current screenshots13–18 remain private.
Owned viewer72893 stopped terminal0, viewport reset and temporary tab closed.
No model/vendor/transition action, user runtime unchanged. These are scoped UX
improvements, not professional acceptance or live financial/VI acceptance.
Next compact the long preparation flow, improve first-fold context/navigation,
and continue full R01–R14/default-owner/recovery/financial/live gates. NQ=F stays
owner BLOCKED; no provider/policy/consent/graph cut, CI, merge or public deploy.

**Social exact-source checkpoint · 2026-10-03 15:36 UTC:** clean frozen source
`f7bca474fa44c9ff053b013bac79fa9a0eadd91c`, full local PostgreSQL gate5479
terminal0: **3,000 tests +88 subtests PASS**,2 optional-provider skips,
443warnings,1307.90s. Ruff/pip-check PASS; only helper-owned disposable PG removed.
The interrupted earlier full handle82036 has no recoverable terminal result and
remains UNVERIFIED; this fresh run retained its log and exact-source exit marker.
Fresh noneditable install13505 and packaged smoke33335 terminal0 verify
site-packages entrypoints/native social refusal, not live financial acceptance.
Actual default installed-source probe71036 acquired StockTwits30/30 eligible
posts, full text/hash/manifest owner readback and reuse PASS; labels7 bullish,
0 bearish,23 unlabeled are sample opinions, not probabilities. Reddit returned
UNAVAILABLE/unknown received count; immutable failure readback PASS, eligible
acquisition UNVERIFIED. No AI jobs or private history changes.
In-app UX audit at isolated8019 used real owner API/worker/storage but explicit
synthetic prices/graph. Saved VI/EN report switching and linked REVIEW decision
were observed; missing risk checks disable approval. Preparation remains long,
report summary starts below the desktop fold, and review controls are buried.
This is not professional UX, live graph, finance or translation acceptance.
Owned server63407 stopped terminal0 and temporary tabs closed; port8000 untouched.
Detailed source receipt and remediation priorities are in receipt20261003 below.
R01–R14 remains active; next implement compact preparation/report/review layout
without hiding coverage, shortening the graph or changing consent/policy.

**Original social preparation checkpoint · 2026-10-03:** the candidate containing
this entry adds structured original StockTwits/Reddit public feeds, bounded fixed
transport/child acquisition, independent authenticated owner preparation,
immutable full-text snapshots and original Sentiment/fact admission. Publication,
Reddit edit cutoff, full identity/hash/manifest and distinct failure states refuse
invalid data; recent samples/user labels are not historical coverage, market
probabilities or neutral absence. No CLI/default/provider/role/policy/approval cut.
Current local focused PG2371 terminal0 covers182 cases, including actual synthetic
child stdio, threaded shared acquisition lock, full graph EN/VI fixtures and
SQLite/PG storage. Final focused rerun86289 terminal0:182 PASS,1warning,31.69s
after test-ID-only shortening to avoid megabyte fixture identifiers; Ruff and
pip-check PASS, only helper-owned labelled PG removed. Web56263 terminal0:
148 tests/typecheck/lint/build. Final
synthetic browser12609 terminal0: real owner HTTP/API on127.0.0.1:8018,
desktop1440×1000/mobile390×844, both feeds retained, consent reset, no job, EN/VI,
language pressed-state and console/overlay/overflow checks; four screenshots
reviewed. QA corrected translated-heading lookup and waited for the CSS language
transition before capture, not a product/policy bypass. Owned servers99878/34799/
15944 terminal0; private application/browser/runtime not restarted. Managed
20261003T083034Z-76016 remains prepared. Whole exact-source baseline, fresh package
and actual new social acquisition are still UNVERIFIED at this checkpoint.
Do not promote original HTTP endpoint diagnostic200 into structured live proof.
The preparation form remains long and text-heavy; passing viewport/interactions
does not accept broader professional process/report UX. See receipt20261003,
section **Original public social preparation and retained full-text research**.
Keep the full R01–R14 objective active: recovery/default-owner journey, financial/
source-entailment/VI quality, operational/report UX and fresh BTC/AAPL acceptance
remain open; NQ=F remains owner BLOCKED without approved roll/contract metadata.
No paid model run, CI, history rewrite, provider/risk change, main merge or deploy.

**Latest exact-source receipt · 2026-10-03 08:21 UTC:** tested source
`f900afaf64f1eb42705583aa38a7397b1f63c41f`, clean and unchanged throughout full
regression76717, terminal0: **2,906 tests +88 subtests PASS**,2 optional-provider
skips,442warnings,1234.19s. Ruff/pip-check PASS; helper removed only its labelled
disposable PostgreSQL container. Fresh noneditable tracked install21115 and
packaged smoke10514 terminal0, including site-packages imports, native fixed FRED
child/missing-key refusal, authenticated synthetic API reuse/no job, SQLite
head0017/ORM parity and scoped offline PostgreSQL DDL. Final browser66203 terminal0
includes first and target desktop1440×1000/mobile390×844 screenshots, EN/VI and
multi-source interactions; synthetic sources, no AI job, all task-owned QA servers
stopped. Previous pending statements below retain their earlier checkpoint scope.

**Existing source credentials / live acquisition now verified:** worktree `.env`
still lacks SEC contact/FRED key, but presence-only inspection found both in the
root checkout's ignored `.env`. No name/email resubmission is needed. Probe92365
loaded only those two existing values into its own process, with a fresh managed
cache, owner database and artifact store; no env file was copied or changed.
Actual authenticated AAPL SEC API preparation returned **1,159 eligible facts**,
zero invalid records, last filing2026-07-31. Actual FRED DGS10/1825-day preparation
returned **1,304 observations**,56 explicit missing values, native unit Percent,
completed Chicago vintage2026-10-02. Owner integrity readback, full macro history/
fact replay, filed-date fact catalog and exact-source API reuse PASS. No AI job or
model token use; no private runtime/history mutation. This verifies source
acquisition, not complete fundamentals/macro, economic interpretation, report
quality, financial/VI acceptance or production readiness. Details and commands:
`docs/platform/research-acceptance-20261003.md`, section **Bounded FRED web flow
and actual existing-source acquisition**.

Next retain the entire R01–R14 scope: structured social/other-asset source
coverage, actual repeated-continuation/all-stage/crash/transport/ACK and default
owner journey, financial/source-entailment/VI quality, operational/report UX and
fresh complete BTC/AAPL acceptance. No unapproved paid retry, shortened graph,
provider/risk change or historical fingerprint rebinding. NQ=F remains owner
BLOCKED without active-contract/roll metadata or a substitute. Draft PR7 stays
open/draft; no CI, broker, main merge or public deployment.

**R04 current macro preparation checkpoint 2026-10-03:** candidate containing
this checkpoint implements the existing FRED series/window transport, supervised
75-second child acquisition with bounded response/output and kill/reap/pipe joins,
owner/CSRF API, immutable failure auditing and exact-vintage/window reuse.
No legacy CLI/provider/default change, new schema, AI call or history rewrite.
Web EN/VI economic-context controls retain headlines/other indicators when
replacing only the same dataset/series, explicitly refuse selection overflow,
reset paid consent and show native observation/vintage scope. One acquisition
at a time; process-local cooldown is not multi-process/public-deployment proof.
Focused PG85438:284 PASS/58.73s (before one additional lock test); final API5662:
26 PASS/47.22s. Native transport processes cover hang/trickle/nonzero/oversize,
thread construction/start failure and actual pipe closure/reaping, no vendor call.
Final web86973:144 PASS, typecheck/lint/build PASS. Browser90062 terminal0 uses
bundled Playwright1.62.1 (Browser plugin absent), synthetic owner HTTP/API on
127.0.0.1:8017; desktop1440×1000/mobile390×844 EN/VI, DGS10 1825days + independent
headlines + UNRATE retained, paid consent only/no job; identity/nonblank/overlay/
console/interactions/screenshots PASS. Browser fixture identity timestamps and
test locator fixes are diagnostics, not provider or policy bypass. Screenshot
review finds no target clipping/horizontal overflow; broader process/report UX
remains unfinished. Task-owned server handles28927/97900 terminal0; private
application/runtime not touched. Managed20261003T072641Z-47907 is still prepared;
full exact-SHA regression and fresh packaged smoke for this candidate are next,
currently UNVERIFIED, not replaced by focused/browser evidence.
Presence-only SEC contact/FRED key both absent; no actual name/email supplied,
no key printed/copied. Live FRED/SEC/BTC/AAPL/financial/VI/editorial remain open;
NQ=F owner BLOCKED/no provider/substitute unchanged. R01–R14/Draft PR7 stay active,
including recovery/all-stage/crash/ACK/default owner journey, social/other-asset
ingestion and operational/report UX. Preserve all older receipts/history below;
new source bytes invalidate old checkpoint fingerprints, never rebind/reset them.

**R04 stored macro → original research/report flow 2026-10-03:** tested clean
source `c7fd0465979e9eeb64a7e2f80e4c057361b3e6c9`. Stored eligible FRED sources
now join the existing news analyst, never as headlines/social/company statements.
Owner loader and engine recheck full instrument identity before graph/client
construction; collection/manifest/hash/PIT checks remain. Read-only full-history
paging and exact native-unit/period/denominator/vintage facts preserve missing
versus zero. Owned full EN/VI statements prevent unit/meaning/anchor substitution.
No original role/round, financial review, bounded repair, risk or approval cut.
12 original full-graph fixtures cover EN/VI/bilingual, invalid binding, macro-only
and independent macro+headline sources. Synthetic SDK/data, not live finance/MT.
Final precommit focused96437 **273 PASS**,40.08s; full unchanged clean c7fd046
handle81897 **2,841 +88 subtests PASS**,2 optional-provider skips,442warnings,
1262.32s,terminal0. Fresh tracked noneditable install37299, packaged smoke65695
and three independent packaged import entrypoints22850 terminal0. Owner macro
load/fact/report/protected localization, SQLite head0017/ORM parity and scoped
PG DDL0010:head PASS; not full fresh-dependency/Python matrix or macro-specific
native/financial/editorial/browser acceptance. Ruff/pip-check/diff/templates PASS.
Managed20261003T062502Z-11211 completed/exit0 after all handles terminal, retained;
helper removed only its labelled PG; old exited QA container untouched.
Receipt20261003 section **Stored macro admission and protected report flow**
contains commands, earlier failed diagnostics and exact remaining scope.
Next: bounded FRED transport/whole-acquisition supervision, authenticated API/web
preparation and multi-source selection without replacing headline/macro IDs.
No web macro acquisition yet. Broader recovery/all-stage/crash/ACK/repeated
continuation, social/other-asset ingestion, finance/source-entailment/VI,
operational/report UX and fresh BTC/AAPL remain open. SEC contact/FRED key absent
by presence-only check; actual name/email not supplied. NQ=F owner BLOCKED/no
provider/substitute unchanged. Source-byte changes invalidate older checkpoint
fingerprints; restore original runtime, never rebind private history or reset
allowance. No CI, paid/vendor call, private DB migration/restart/history rewrite,
provider/risk change, broker, main merge/deploy. Full goal/Draft PR7 remain open;
older sections below retain their original SHA scope and macro-exclusion status.

**R04 structured FRED prerequisite 2026-10-03:** tested clean source
`b4d48170e2b5333b09be8775c72b49523c1030c7`. Existing FRED request/key and CLI
defaults stay unchanged. One explicit series/window retains full native-unit
observations (including missing values), pins metadata/values to a fully elapsed
Chicago vintage day, and checks native-frequency observation freshness separately
from vintage time. Immutable owner-readable storage verifies whole payload/manifest
parity, identity/hash/cutoff; SQLite and disposable PostgreSQL fixtures cover
idempotency, tamper/corrupt bytes, failed storage rollback and owner refusal.
Macro remains excluded from analyst admission. This is not web acquisition,
complete macro coverage, live FRED, financial or UI acceptance. Existing request
buffers JSON before parser limit: bounded whole-acquisition transport/supervision,
canonical fact/unit/period replay, authenticated API and web flow remain open.
Final precommit focused43611 **140 PASS**,18.96s; full unchanged b4d4817
handle76974 **2,762 +88 subtests PASS**,2 optional-provider skips,442warnings,
1040.04s,terminal0. Ruff/pip-check/diff/templates PASS. Exact tracked archive/fresh
noneditable install17910 and outside-source packaged smoke14109 terminal0:
site-packages imports, synthetic macro SQLite roundtrip, head0017/ORM parity,
scoped packaged PostgreSQL DDL0010:head PASS. Not full fresh-dependency/Python
matrix. Managed20261003T053342Z-94186 completed/exit0, retained; helper containers
removed only by their own labels, old exited QA container left alone.
Detailed commands/initial lint failures and follow-up scope: receipt20261003,
section **Structured FRED acquisition/storage prerequisite**. New package Python
bytes conservatively invalidate older checkpoint fingerprints; never rebind old
private checkpoint history to a different runtime. Exact old runtime is required.
Presence-only `.env` check in this worktree: SEC_EDGAR_USER_AGENT and FRED_API_KEY
both absent; no actual contact supplied, no key displayed/copied to Git. No CI,
paid/live-provider call, private DB migration/restart/history rewrite, provider/
risk change, broker, merge or deployment. Entire R01–R14 goal/Draft PR7 stay open:
actual multi-continuation/all-stage/crash/transport/ACK and owner API/UI journey,
macro/social/other-asset ingestion, finance/source-entailment/VI quality and
operational/report UX remain unfinished. Fresh BTC/AAPL acceptance remains open;
NQ=F owner BLOCKED/no provider/substitute unchanged.

**Actual linked local-stop reconciliation 2026-10-03:** tested clean source
`89c789d25af5b11f4efcde367883aedd500fafb6`. Additive0017 records only an actual
joined original child with closed pipes/reader, bound context/request/observer,
private lease and owner/root/entry/dispatch/checkpoint/accounting provenance.
Cancellation/expiry permits this separate fact, not normal publication, allowance
refund, provider billing/termination or continuation/approval authority. Original
FAILED root/job/history and all graph/risk/approval fences remain intact.
Recorded immutable accounting prefix keeps the old stop readable after later
appends; consent/recheck/allowance still use full latest accounting. Native
SQLite EN/VI/bilingual/invalid-VI cancellation/expiry plus actual PG owner-book
cancel/expiry cases run. Actual SQLite rollback/lost-ACK and private scope/tamper
fixtures preserve uncertainty and refuse forged evidence. Later-attempt prefix
fixture is accounting-only, not actual multi-continuation acceptance.
Final precommit focused PG handle6691 **258 PASS**,318warnings,720.19s; final
extra oversized-JSON reader handle32239 **1 PASS**,11deselected,5warnings,12.30s.
Full clean unchanged89c789d handle47021 **2,648 +88 subtests PASS**,2optional
skips,442warnings,1380.77s,terminal0. Ruff/pip-check/diff/templates/bash syntax
PASS. Exact tracked archive/fresh noneditable install4459 and packaged smoke
26087 terminal0:site-packages imports, scoped PG JSONB/FK DDL0010:head and owned
fresh SQLite head0017/full metadata parity PASS. Not full fresh-dependency/Python
matrix or live financial/browser acceptance. Managed20261003T041447Z-66818
completed/exit0, retained; helpers removed only their own labelled containers,
older exited QA unchanged. Initial invocation/test-author failures are retained
in receipt20261003 **Actual linked local-stop reconciliation** section.
Next: remaining all-stage/crash/transport/ACK and actual multi-continuation,
then default authenticated owner API/worker/CLI/UI journey. Broader ingestion,
finance/source-entailment/VI quality, operational/report UX and fresh BTC/AAPL
remain open. SEC contact presence-only check still false; no contact supplied.
NQ=F owner BLOCKED/no provider/substitute unchanged. No CI, paid/vendor call,
private DB migration/restart/history rewrite, provider/risk change, broker,
merge/deploy. Full goal and Draft PR7 remain open.

**Native PostgreSQL portfolio → approval / focused local QA 2026-10-03:**
tested clean source `6ae34c94e1e7a32a800cc9a47e1ef5c8bb167417`.
Eight actual PostgreSQL native-spawn cases reuse every original SQLite graph,
checkpoint, retained-budget, original owner book/risk and authenticated API
assertion. Three valid EN/VI/bilingual outputs approve idempotently with one
event; invalid VI and all four original-policy-failure variants remain REVIEW,
target withheld, API409. All roles/rounds and uninterrupted baseline comparison
remain intact; old FAILED root/job/history unchanged. SDK responses are synthetic
and HTTP refused: local PG/native/API proof, not live financial/browser acceptance.
Focused helpers require explicit `--focused` selection, retain full default mode,
and label narrow evidence separately. Four malformed-selection tests reject
before runtime/database allocation. Owned disposable PG lifecycle is unchanged;
no existing application database may be used.
Initial focused dirty-patch handle19620 **8 PASS**,32 deselected,40 warnings,
209.71s; CLI precommit handle92824 **4 PASS**,0.14s. Full unchanged clean source
handle63423 **2,618 +88 subtests PASS**,2 optional-provider skips,347 warnings,
879.76s,terminal0; Ruff/pip-check/diff/templates/shell syntax PASS.
Managed evidence at `20261003T034122Z-53739` completed/exit0, retained on verified external SSD;
helper removed only its current labelled container, older QA container untouched.
No package/CLI/dependency surface changed; their source trees equal c04b23e,
whose fresh-install receipt remains source-scoped, not a new install claim.
Next: actual native cancel/expiry/ACK boundaries and durable, non-authorizing
stop reconciliation, multi-continuation, then default owner continuation API/UI.
Broader macro/social/other-asset ingestion, financial/editorial/VI quality and
operational/report UX remain open. Fresh BTC/AAPL require appropriate live
authorization and prerequisites; SEC contact presence-only check is still false.
NQ=F owner BLOCKED/no new provider unchanged. No CI, paid/vendor call, risk/provider
change, private DB migration/restart/history rewrite, broker, merge/deploy.
Full goal and Draft PR7 remain open. Exact commands/limitations: receipt20261003,
section **Native PostgreSQL portfolio approval and explicit focused local QA**.

**Native portfolio → authenticated approval / lifecycle timing 2026-10-03:**
tested source `c04b23e3bf88a71b594c57fdb7db3b0e07a132f8`. Reproduced actual
writer/reader inconsistency: linked review could be written before completion,
then rejected by the integrity reader. All linked lifecycle transitions now
check completion time before write/cached ACK; equality allowed, later history
ordering still strict. Ordinary non-approval behavior and approval/risk/owner
gates unchanged, no policy override or history rewrite.
Eight added native spawned-child cases retain 4 analysts and 2 research/risk
rounds, transfer actual fixture owner book/policy/risk bytes into the terminal
original context, and compare interrupted prefix+restored suffix/full result
to the original uninterrupted native baseline. EN/VI/bilingual valid output
goes through existing authenticated API login/CSRF/approve: exactly one lifecycle
event, immutable ready candidate and old FAILED root/job/history retained.
Original policy violation (owner target .95) or invalid VI remains REVIEW,
weight withheld, API409; no model/risk/translation gate cut. Local SQLite/synthetic
SDK proof only, not live finance or native PostgreSQL end-to-end acceptance.
Final focused **433 PASS**, 2 missing-URL PG skips, 167 warnings, 331.21s.
Full clean unchanged c04b23e disposable PG gate **2,606 +88 subtests PASS**,
2 optional-provider skips, 307 warnings, 653.63s, terminal0. Ruff/pip-check/diff/
templates PASS; exact tracked-archive fresh noneditable install/site-packages
imports, scoped PG DDL0010:head and owned SQLite head0016/metadata parity PASS.
Managed evidence completed/exit0 and retained; only current labelled PG removed.
Initial real timing FAIL plus two test-author/schema failures are retained in
receipt20261003, not hidden or mistaken for financial acceptance.
Next: actual native PostgreSQL approval and remaining stop/cancel/expiry/ACK
reconciliation/multi-continuation, then default owner continuation API/UI journey.
Broader ingestion/finance/VI/UX and fresh BTC/AAPL remain unverified; SEC contact
still absent, NQ=F owner hold unchanged. No CI, provider/risk change, paid/vendor
call, private DB migration/restart/history rewrite, merge/deploy. Goal/PR7 open.

**Verified linked completion → human review/approval 2026-10-03:** tested source
`bb738a7205aac9e6d10e455959e8c07368bfbe98`. Existing authenticated decision
transition route accepts only a fully verified linked completion, without
relabeling the FAILED/CANCELLED root/job or altering immutable candidate payload.
Actual source bytes/columns/PIT, receipt/checkpoint/report/accounting bindings,
indexed run/decision/lifecycle parity and original deterministic risk replay are
checked. Approval before completion, missing/corrupt receipts, wrong owner/policy,
forged lifecycle/status, modified source/risk policy and blob corruption refuse;
even idempotent approval ACK revalidates the receipt. Existing human actor,
CSRF, lifecycle/CAS and ordinary successful-run approval gates remain intact.
Final focused **110 PASS**, 6 missing-URL PG skips, 131 warnings, 163.63 s.
Full unchanged clean bb738a7 disposable PostgreSQL gate **2,589 +88 subtests
PASS**, 2 optional-provider skips, 258 warnings, 730.85 s, terminal exit 0;
includes actual PG competing/same-event writers and approval, native regression.
Ruff/pip-check/diff/templates and exact tracked-archive fresh noneditable install,
site-packages origins, scoped PG DDL `0010:head` and owned SQLite head0016/full
metadata parity PASS. Managed build completed/exit0 and retained; only the
current labelled PG container removed. Initial import lint failures corrected
before source commit, intermediate gates preserved in receipt20261003.
Local API/seeded risk fixtures are not browser or native portfolio-ready/live
financial acceptance. Default continuation API/worker/CLI dispatch stays off;
full stop/cancel/expiry/ACK reconciliation, multi-continuation, native portfolio
approval and operational API/UI journey remain open. Broader ingestion/finance/
VI/UI and fresh BTC/AAPL still open. SEC contact remains absent; NQ=F owner hold
unchanged. No private DB migration/restart/history rewrite, provider/risk change,
CI, paid AI/vendor call, merge/deploy. Goal and Draft PR #7 remain open.

**Linked stage/report/decision completion 2026-10-03:** final tested source
`f107b18e3c8f86e45328fce57271b3274289375b` (implementation `02e956e`, schema
parity fix `e9cc2fa`). Exact bound parent publisher retains allowlisted,
unvalidated stage text and atomically appends the ordinary report/evidence/
deterministic-risk candidate plus separate additive `0016` completion receipt.
Same extracted report projection/decision pipeline as the ordinary handler;
no graph/financial/translation/risk gate cut. Original FAILED/CANCELLED root/job
remains unchanged. Actual owner-readable sources and actor/hash/accounting
bindings are rechecked; receipt reader resolves committed ACK loss without a
model or live lease. Completion fences further writes/heartbeat/cancel.
Native result is published only after clean child exit/reaping, reader shutdown
and durable stopped accounting. A reproduced one-second cleanup cutoff was
fixed by polling within the original retained allowance/cancel/lease checks;
deadline/nonzero exit still refuses completion. No budget reset or paid call.
Final focused **163 PASS**, 8 missing-URL PG skips, 109 warnings, 328.51 s.
Full clean exact-source disposable PostgreSQL gate **2,564 +88 subtests PASS**,
2 optional-provider skips, 233 warnings, 832.32 s, terminal exit 0. Ruff,
pip check, diff/templates and fresh noneditable tracked-archive install/import,
packaged PG DDL `0010:head`, owned SQLite head0016/metadata parity PASS.
Initial schema FAIL, subsequent native-publication FAIL, deterministic slow-exit
counterexample and earlier contaminated gate are retained in receipt 20261003.
Managed build evidence retained; only this task's labelled PG container removed.
Next: integrate verified completion with human review/approval (currently still
requires root SUCCEEDED), preserving immutable candidate evidence and append-only
lifecycle; stop/cancel/expiry/ACK reconciliation, multi-continuation and default
API/UI journey remain open. Native fixtures use synthetic SDKs, not live finance
or cost evidence. Broader ingestion/UX/financial/VI and fresh BTC/AAPL still open;
SEC contact was not actually supplied, NQ=F remains owner-BLOCKED. No private DB
migration/restart/history rewrite, provider/risk change, CI, paid AI/vendor call,
merge/deploy. Full goal and Draft PR #7 remain open.

**Terminal original-context / single-use linked native dispatch 2026-10-03:**
source `27e969bd18b389854ebdb5b6c6b0af934b6cac10`. Internal loader giữ nguyên
full FAILED/CANCELLED manifest/error/completed_at; ordinary context vẫn từ chối
terminal. Reload owner-readable analyst/risk bytes, indexed columns ↔ manifest,
book/policy và pinned original checkpoint trong linked parent fence, rồi kiểm tra
lại trước dispatch. Không fallback live, fresh observer, budget reset hay đổi
thread/fingerprint. Additive `0015` append one consumed-dispatch marker trước
Process construction; lost committed ACK không respawn. Child chỉ nhận JSON/
checkpoint, không DB/lease nonce/session/CSRF/callback. Bound checkpoint callback
và unused retained observer được recheck; prestart kiểm tra deadline còn lại.
Real monotonic usage validation sửa đối chiếu duration đã capture ≤ fresh read,
counters/flags vẫn exact, cumulative accounting không chấp nhận reset/decrease.
4 actual native EN/VI/bilingual/invalid-VI fixtures đi qua stopped original child,
immutable FAILED root, authenticated consent/lease và linked restored child;
prefix + suffix và result fields khớp uninterrupted original baseline. Old root/
job/event/checkpoint không đổi, new actor links attempt 2; invalid VI vẫn fail.
Synthetic SDK/local graph evidence, không live provider/finance/cost acceptance.
Final combined focused **145 PASS**, 4 missing-URL PG skips, 88 warnings, 128,63 s.
Full clean exact-source qua disposable PostgreSQL helper **2.522 +88 subtests
PASS**, 2 optional-provider skips, 212 warnings, 408,24 s, terminal exit 0.
Ruff/pip-check/diff/templates PASS; task-only container đã dọn. Clean noneditable
tracked Git archive install/import + packaged PG DDL `0010:head` + owned fresh
SQLite head 0015 PASS; managed external evidence retained. Không claim full-chain
offline DDL (known migration 0007 limitation), fresh-dependency full test/matrix
hay secret/vulnerability scanner. Initial fixture FAIL (root error_message None)
và real artifact column/manifest mismatch FAIL giữ trong receipt 20261003.
Next: linked report/decision finalization, stop/cancel/expiry reconciliation và
all crash/ACK boundaries, multi-continuation, rồi default API/UI activation.
Không private DB migration/restart/history rewrite, paid AI/vendor call, provider/
risk change, CI, merge/deploy. UI/ingestion/finance/VI/live BTC/AAPL còn mở;
SEC tên/email chưa được cung cấp, NQ=F giữ BLOCKED theo owner. Goal/PR #7 mở.

**Linked parent publication / accounting prerequisite 2026-10-03:** source
`b089fe599a45655fe503119e162683caf5bc4294`. Internal context build exact retained
observer rồi recheck full consent high-water dưới owner/job/run/execution locks
trước một actual parent entry; lost ACK không cho re-enter. Usage/stage events và
private checkpoint commit cùng actor links của additive `0014`, không rebuild/
backfill bảng cũ. Root run/job/thread không đổi; checkpoint mới attempt 2, không
lấy attempt 1 của terminal job. Old identical checkpoint ACK giữ nguyên provenance.
Nonce/identity/cancel/expiry fence trong transaction và sau flush; expiry trong
lúc lấy source locks không thể được heartbeat hồi sinh. Full accounting cộng mỗi
attempt một lần, chặn tổng logical starts vượt original cap; claim/prepare time
được debit. Stop hook chỉ từ bound observer còn lease; late cancel/expiry stop
giữ upper bound unknown, không giả stop/refund. Local hook fixture không chứng
minh actual child reaping. Default worker/API/CLI không bật resume.
Final focused **166 PASS**, 10 PostgreSQL skips, 35,53 s; full sạch exact source
qua disposable PostgreSQL helper **2.481 +88 subtests PASS**, 2 optional-provider
skips, 192 warnings, 303,69 s, terminal exit 0. Gồm 2 actual PostgreSQL linked
parent accounting/checkpoint và two-writer cases; fault variants chủ yếu SQLite.
Ruff/pip-check/diff/templates PASS. Clean noneditable install/import, packaged
PostgreSQL DDL `0010:head`, owned SQLite head 0014 PASS; offline DDL từ base FAIL
ở data-reading migration 0007, không sửa/che giấu thành toàn-chain DDL PASS.
Initial fixture exception/lint failures và exact commands có receipt 20261003.
Container task đã dọn; managed fresh-install evidence giữ lại trên SSD ngoài.
Next: terminal original-context reader + linked stage/report/decision publication,
actual native child equivalence và stop/cancel/ACK reconciliation, rồi API/UI
activation. Multi-continuation, broader ingestion/UX/live finance/VI chưa đạt.
SEC contact chưa có giá trị; không tự điền. NQ=F giữ BLOCKED, không thêm provider.
Không private DB migration/restart/history rewrite, paid AI/vendor call, risk/
provider change, CI, merge/deploy. Full goal và Draft PR #7 vẫn mở.

**Separate linked execution lease prerequisite 2026-10-03:** source
`dbde6ff46ddb5ad99b2e43b229c5460b444ac000`. Internal allocation consume consent
UUID vào riêng `0013_research_executions`, không tạo lại RunRow/JobRow hoặc bỏ
unique original run. Auth owner/session/CSRF và original observation được reload
transactionally trước allocation/claim. Hai requests chỉ có một allocation và
một worker claim; private nonce chỉ lưu hash, ACK sau commit. Renew không reset
claim-time deadline đã trừ prior elapsed; corrupted DB/handle cùng sửa deadline
vẫn bị từ chối. Cancel reserved → cancelled; cancel leased → cancel_requested,
không giả child đã dừng. Expired/lost-ACK leased → review_required, không requeue
hay refund. Original run/job/event/checkpoint không đổi; không emitted actual
execution_started/usage, model call, checkpoint/report/decision mới.
111 focused PASS, 9 PostgreSQL skips, 25,21 s; initial/intermediate gates và Ruff
import repairs có receipt. Full sạch qua disposable PostgreSQL helper **2.450
+88 subtests PASS**, 2 optional-provider skips, 192 warnings, 291,69 s, terminal
exit 0; gồm 3 PostgreSQL linked-lease/reopen/allocation-race/claim-race cases.
Ruff/pip-check/diff/templates PASS. Fresh noneditable platform install/import,
packaged PostgreSQL DDL và owned SQLite head 0013 PASS tại exact source trên SSD
ngoài; fresh resolved dependency full suite chưa chạy. Container task đã dọn;
managed install run giữ lại, không xóa evidence. Xem receipt 20261003.
Default worker/API/CLI không consume lease; nonce không phải model/publication
grant. Next: linked parent-only publication/checkpoint provenance + actual
execution_started/usage/stop accounting và terminal original-context loading,
rồi real native-spawn equivalence trước API/UI activation. Multi-continuation,
full crash/transport, ingestion, UX và live finance/VI vẫn UNVERIFIED. Không
private DB migration/restart, paid AI/vendor call, provider/risk change, CI,
history rewrite, merge/deploy. NQ=F vẫn BLOCKED; goal/PR #7 mở.

**Authenticated consent / PostgreSQL checkpoint fix 2026-10-03:** final source
`fdd0b717059f5067788c8af0dce4ea7064eb0fb4`, sau prerequisite
`f2f42354134bf5d53775e0019187a6421628de5e`. Internal consent store xác thực
owner/session/CSRF, reload original failed/cancelled job/run, latest checkpoint
và toàn bộ accounting high-water dưới writer locks, rồi append riêng một link.
Canonical JSON giữ khác biệt bool/int; ACK chỉ sau commit. Không tạo job/model
call, không sửa history, không reset budget; default API/worker/CLI chưa bật.
Lặp cùng key trả cùng identity; khác key không reserve cùng observation hai lần.
Full PostgreSQL đầu tại f2f4235 **FAIL: 12 failed, 6 errors, 2.386 +88 subtests
passed**, 2 skips, 192 warnings, 313,14 s: migration 0011 đặt hai unique constraint
trùng tên do naming convention theo first column. Sửa explicit names ở migration
draft/model, thêm offline DDL regression và 4 disposable PostgreSQL consent/
two-writer cases; không nới integrity/auth gates hay migrate private DB.
Final full tại source sạch fdd0b71 qua `TA_ALLOW_TEST_DB_RESET=1 bash
scripts/verify-postgres-local.sh`: **2.409 +88 subtests PASS**, 2 skips (optional
Bedrock/live DeepSeek), 192 warnings, 343,62 s, terminal exit 0, Python 3.14.7/
Darwin 25.5.0; Ruff/pip-check/diff PASS. Task-only PostgreSQL container đã dọn.
Clean noneditable `.[platform]` install/import, packaged PostgreSQL DDL và fresh
SQLite migration PASS tại fdd0b71 trong managed external run; chưa full-test fresh
dependency set (SQLAlchemy mới resolve 2.1.3). Xem receipt 20261003 cho exact
path/version/initial failures. Không paid AI/market-data call, CI,
runtime restart, provider/risk change, private env/history upload, merge/deploy.
Goal/PR #7 vẫn mở. Next: consume link transactionally, separately leased execution
và linked accounting/publication; reload immutable terminal context mà không xóa
error/completed_at hoặc đổi original thread/fingerprint. API auth phải cùng consent
transaction, không nest dưới outer session-write lock; vẫn giữ Origin/cookie/CSRF.
Broader crash/transport, ingestion, operational UX và live finance/MT còn chưa đạt.
NQ=F vẫn BLOCKED theo owner; không tự mở paid BTC retry.

**Restore observer binding 2026-10-03:** source
`6cd566f7e27a45ce247357bd2ee2b405c3d7c980` chặn opt-in restore dùng observer
mới/copied, debit bị reset, caps/clock/callbacks thay đổi, attempt đã dùng/dừng,
hoặc owner/run/config/limits khác original context, trước khi tạo process.
Binding riêng frozen/repr-private từ builder đã reload accounting; không vào
child/event và không phải consent token hay transaction fence. Deadline dùng
clock gốc; cancellation vẫn ưu tiên cả khi hết giờ. Non-restore/default
worker/API/CLI không đổi. Initial focused FAIL: fixture tạo alias AAPL trùng
(1 failed, 1,51 s), sửa dùng disposable SQLite trống, không nới validator.
73 context/retained tests PASS (4,98 s); 89 native-spawn/context/retained tests
PASS (68 warnings, 59,44 s), trước hai cancellation cases cuối; final binding
23 PASS (2,82 s). Full tại source sạch: **2.343 + 88 subtests PASS**, 20 skips,
192 warnings, 350,14 s, terminal exit 0, Python 3.14.7/Darwin 25.5.0;
Ruff/diff/templates PASS. Không paid/vendor call/CI/private DB migration/
restart/history rewrite/provider/risk change/merge/deploy. Goal/PR #7 vẫn mở.
Tiếp theo phải thiết kế consent/linked execution transactionally: JobRow có
unique(run_id), original terminal run bị context từ chối, fingerprint/native
thread bind original run ID. Không xóa error/completed_at hoặc đổi thread ID
để lách flow. Dispatch/high-water fence, ingestion/UX/live vẫn UNVERIFIED;
NQ=F giữ BLOCKED theo owner.

**Stopped native attempt / lost-ACK recovery fixture 2026-10-03:** source
`d87ee6261a41d26df6d1639ef937eee08e433a53` actual supervisor dừng/reap child
sau durable nonempty market-report pending writes nhưng ACK bị mất. Child mới
restore latest validated tuple, debit prior calls/time; prefix + suffix trace
và published fields khớp uninterrupted EN/VI/song ngữ/invalid VI. Completed model
call không lặp; old rows/original fixture run không đổi, usage cộng đúng một lần.
Killed SDK cleanup giữ unknown; không giả closed. Test-only synthetic prefix
sink không thêm production prompt logging. Initial gate FAIL vì fixture bắt
market_report rỗng ở initial writes (1 failed, 9,38 s); sửa threshold nonempty,
không nới gate. 4 stopped cases PASS (23,28 s); final 45 focused PASS (68 warnings,
80,42 s); full **2.320 + 88 subtests PASS**, 20 skips, 192 warnings, 267,81 s,
terminal exit 0 tại source sạch, Python 3.14.7/Darwin 25.5.0; Ruff/diff/templates
PASS. Chỉ một pending-write/ACK boundary; abrupt parent crash/all-boundary/
concurrent writers/consent-linked execution/transport còn UNVERIFIED. Fixture
vẫn dùng original lease context, không tạo production consent hay job identity.
Default resume chưa bật; ingestion/UX/live còn mở, NQ=F BLOCKED theo owner.
Không AI/vendor/CI/private DB migration/restart/history rewrite/provider/risk
change/merge/deploy; goal và Draft PR #7 mở.

**Restricted new-child restore transfer 2026-10-03:** source
`60e9200a1d47ac596c79c4135ef0bebb6628fcf8` supervisor opt-in bytes cùng exact
original context/engine; parent validate/revalidate thread/fingerprint trước
spawn, child recorder kiểm actual initialized graph và parent allowance.
DB/lease/commit callback không chuyển sang child. EN/VI/song ngữ/invalid VI
fixture chạy child mới với intermediate tuple của completed synthetic run;
remaining trace/output khớp baseline, cả hai child reaped, old rows nguyên vẹn.
Retained observer debit TOÀN BỘ attempt trước kể cả work sau tuple; accounting
cộng hai attempts, không reset. Không phải consent hay stopped/crash recovery.
12 native-spawn PASS (43,71 s) + 61 context/allowance PASS (15,49 s); full mới
**2.316 + 88 subtests PASS**, 20 skips, 172 warnings, 261,25 s, terminal exit 0
tại source sạch, Python 3.14.7/Darwin 25.5.0; Ruff/diff/templates PASS. Full
lượt trước bị ngắt, handle mất và không còn process: UNVERIFIED, không lấy
progress percentage làm PASS; chỉ chạy lại local suite, không paid analysis.
Default worker/API/CLI resume chưa bật. Consent/linked execution, stopped/crash
acceptance, transport attestation, ingestion/UX/live còn UNVERIFIED; NQ=F
BLOCKED theo owner. Không AI/vendor/CI/private DB migration/restart/history
rewrite/provider/risk change/merge/deploy; goal và Draft PR #7 mở.

**Original recorder/graph restore hook 2026-10-03:** source
`7c36a2609c33ec3352295fbcb694a6d42539b4fe` recorder optional restricted bytes
sau initialized fingerprint/original observer allowance checks; native graph
dùng invoke(None), config_scope/callbacks/sync gốc, không dựng next-stage flow.
Default worker/API/CLI không bật restore. Fixture SQLite intermediate checkpoint
cho EN/VI/song ngữ/invalid translation: remaining trace và full non-message
result khớp baseline, observer start và prior rows không đổi; không paid proof.
52 focused PASS, 122 warnings, 33,90 s; full **2.310 + 88 subtests PASS**,
20 skips, 172 warnings, 380,16 s, terminal exit 0 tại source sạch; Ruff/diff/
templates PASS, không behavioral FAIL. New-child trusted transport/retained
accounting/consent transaction còn UNVERIFIED; ingestion/UX/live còn mở,
NQ=F BLOCKED theo owner. Không AI/vendor/CI/private DB migration/restart/history
rewrite/provider/risk change/merge/deploy; goal và Draft PR #7 mở.

**Native saver restore mechanism 2026-10-03:** source
`4e5b9aaf3015dd44970efe81b6a7c561931bfabb` nạp restricted tuple vào saver
trống, kiểm thread/fingerprint và decoded tuple equality; giữ native versions/
routing/pending writes, không republish history. Sai/malformed/repeated/partial
import poison saver. Original graph fixtures dùng method này cho committed
restore, không chọn next node thủ công. Initial focused FAIL do so byte JSON
khác key order; sửa semantic equality, không bỏ field/control validation.
365 graph/saver focused PASS (trước thêm partial-failure case); final saver
18 PASS; full **2.301 + 88 subtests PASS**, 20 skips, 156 warnings, 214,37 s
tại source sạch, Python 3.14.7/Darwin 25.5.0. Ruff/diff/templates PASS.
Chưa new-child transport/restore, consent transaction hoặc default worker/API
activation. Ingestion/UX/live còn UNVERIFIED; NQ=F BLOCKED theo owner. Không
AI/vendor/CI/private DB migration/restart/history rewrite/provider/risk change/
merge/deploy; goal và Draft PR #7 mở. Xem receipt ngày 2026-10-03.

**Retained observer enforcement 2026-10-03:** source
`ff0e3be987e6aa28707adbff5c362df2577a1f74` builder reload original accounting và
so toàn bộ expected observation; chặn wrong owner/run/type/altered/stale/unknown/
exhausted trước construction. Observer giữ max wall/calls gốc, debit prior elapsed/
starts tại boundary/admission nhưng events/counters/clock chỉ current attempt,
không fresh budget hay double-count. 44 focused PASS, 48,65 s; full **2.294 + 88
subtests PASS**, 20 skips, 156 warnings, 254,40 s tại source sạch; Ruff/diff/
templates PASS. Initial Ruff import/nested-with đã sửa, không behavioral FAIL;
29-pass gate trước final cases không thay final proof. Fixture spawn đơn giản
kiểm chứng retained parent cap/cleanup; chưa original graph recovery/consent.
Builder chưa nối default worker/CLI/API. Transaction consent/linked execution/
trusted restore/transport, ingestion/UX/live còn UNVERIFIED, NQ=F BLOCKED.
Không AI/vendor/CI/private DB migration/restart/history rewrite/provider/risk
change/merge/deploy; goal và Draft PR #7 vẫn mở.

**Original allowance arithmetic 2026-10-03:** source
`eb799a08adf79863c1e3f6f846a3698fb32c776f` reader load authoritative accounting,
trừ mọi logical starts và local elapsed upper bound khỏi cap gốc. Không nhận
caller-provided cap/time/consent; thiếu accounting/time vẫn unknown, known
exhaustion BLOCKED dù thiếu stop; nhiều attempts không reset cap. Frozen private
observation giữ identity/high-water/unknown provider usage, PASS chỉ arithmetic.
62 focused PASS, 31,87 s; full **2.283 + 88 subtests PASS**, 20 skips,
156 warnings, 218,78 s tại source sạch; Ruff/diff/templates PASS. Initial fixture
FAIL do allowance thiếu snapshot binding; sửa fixture đúng contract, không nới
validator. Native spawn completion/exhaustion receipts kiểm chứng debit 128-calls
và zero remaining cap; không live/cost/financial proof. Consent transaction,
supervisor retained-budget enforcement/restore/transport, ingestion/UX/live còn
UNVERIFIED; NQ=F BLOCKED. Không recorder/resume activation, AI/vendor/CI/private
DB migration/restart/history rewrite/provider/risk change/merge/deploy; goal/PR mở.

**Supervised stop elapsed boundary 2026-10-03:** source
`af087670821882c161b56b275736438013148baa` parent đóng observer và append
model.usage execution_stopped=True chỉ sau child reap và reader shutdown.
Reader chỉ cho local elapsed upper bound khi mọi observed attempt có stop;
thiếu marker/crash/fence refusal giữ unknown, cost/unreported usage vẫn unknown.
Chặn duplicate/false stop và usage sau stop; không callback/admission tiếp bằng
observer đã đóng. Refusal không che lỗi/result gốc, không giả ACK. 66 focused
PASS, 60,92 s; full **2.272 + 88 subtests PASS**, 20 skips, 156 warnings,
211,36 s tại source sạch; Ruff/diff/templates PASS. Initial import-only Ruff
đã sửa, không behavioral FAIL; gates 57/64 PASS trước final tests không thay
proof final. Đây là local supervised duration, không remote provider/billing
duration, exact elapsed hay consent/remaining-budget grant. Không bật recorder/
resume; transaction consent/restore/transport, ingestion/UX/live còn mở.
NQ=F BLOCKED theo owner; không AI/vendor/CI/private DB migration/restart/history
rewrite/provider/risk change/merge/deploy. Goal và Draft PR #7 vẫn mở.

**Accounting identity/recheck 2026-10-03:** tested source
`6ad3bba87f7a0a66cd3facbbfe6170d1eaa0117e` (implementation `e7ec914`) bind
observation với owner/run/config hash và scalar allowance gốc. Internal recheck
reload full evidence, chặn sai owner/run, counter/limits substitution và event
mới; frozen observation không lộ fields qua repr. Không lock writer hay cấp
consent/token/admission; còn race sau read nên không dùng check-then-dispatch.
44 focused PASS, 31,30 s; full **2.263 + 88 subtests PASS**, 20 skips,
156 warnings, 207,69 s tại source sạch; Ruff/diff/templates PASS. Full trước ở
e7ec914 FAIL (1 failed/2.262 passed): test cấm chuỗi "15" trong object repr,
nhưng địa chỉ hex có "15"; sửa assert field suppression/owner/run/config privacy,
không nới production gate. Consent transaction/unknown duration/restore/transport,
ingestion/UX/live còn UNVERIFIED, NQ=F BLOCKED. Không AI/vendor/CI/private DB
migration/restart/history rewrite/provider/risk change/merge/deploy; goal/PR mở.

**Accounting aggregate invariants 2026-10-03:** source
`b831d6ba7ad921918dd10533eeaef5198e05c35d` chặn tokens không có usage-bearing
completion, token growth khi calls_with_usage không tăng và elapsed aggregate
nonfinite dù từng attempt finite. Ba fixtures malformed kiểm tra fixed error và
rows không đổi; native callback fixtures vẫn PASS. 37 focused PASS, 54,87 s;
full **2.256 + 88 subtests PASS**, 20 skips, 156 warnings, 254,09 s tại source
sạch; Ruff/diff/templates PASS. Không behavioral FAIL. Không bật resume hay
consent/admission, không giả định exact elapsed/cost. Consent/restore/transport,
ingestion/UX/live finance/MT/PostgreSQL vẫn UNVERIFIED; NQ=F BLOCKED theo owner.
Không AI/vendor/CI/restart/migrate DB riêng tư/history rewrite/provider/risk
change/merge/deploy. Goal và Draft PR #7 vẫn mở.

**Read-only accounting evidence 2026-10-03:** source
`6034b88b6b158f1666828146a27b2f3db31bc861` thêm reader nội bộ owner/run-scoped,
prefix giới hạn 10.000 events, paging 500; chỉ cộng receipt cumulative cuối mỗi
attempt, không cộng trùng. Validate sequence/attempt/limits/counters/status;
legacy hoặc thiếu usage giữ UNVERIFIED/None, không giả định zero. High-water là
observation cần recheck transactionally; elapsed chỉ lower bound, exact duration
và cost vẫn unknown. Không cấp consent/admission hay bật resume/worker/API.
34 focused PASS, 29,77 s; full **2.253 + 88 subtests PASS**, 20 skips,
156 warnings, 258,01 s tại source sạch; Ruff/diff/templates PASS. Disposable
SQLite reopen và actual native spawn synthetic callbacks kiểm chứng aggregation;
không live billing/financial/MT/PostgreSQL proof. Consent/restore/transport,
ingestion/operational UX/live còn mở; NQ=F BLOCKED theo owner. Không AI/vendor/CI,
restart/migrate DB riêng tư, history rewrite, provider/risk change, merge/deploy.
Goal và Draft PR #7 vẫn mở.

**Durable pre-admission reservation 2026-10-03:** source
`7833efd35664164e48459a4d8733cba310449cb8` observer emit model.usage trước
call và sau completion/error; worker dùng event transaction lease-fenced sẵn có,
không migration/event type mới. Ghi counters/limits/elapsed trước admission rồi
recheck clock/cancellation; emit lỗi/deadline không cấp phép gọi provider. Status
incomplete khi còn reservation chưa có usage, không dùng reported của call cũ.
SQLite reopen và native spawn giữ owner/run/attempt, start/end usage và checkpoint;
không prompt/secret. 40 focused PASS, 69,32 s; full **2.235 + 88 subtests PASS**,
20 skips, 156 warnings, 275,68 s tại source sạch; Ruff/diff/templates PASS.
Initial assertion FAIL vì kỳ vọng chỉ một usage event; cập nhật để kiểm tra cả
reservation, fixture reported dùng đủ start/end lifecycle, không nới gate.
Elapsed chỉ là lower bound lúc event, không exact crash duration/cost; general
event DB transactions chưa có end-to-end deadline. Durable aggregation/unknown
duration, consent/restore/transport và ingestion/UX/live vẫn còn mở. Không chạy
AI/vendor/CI/deploy, restart/migrate DB riêng tư; NQ=F BLOCKED, goal/PR mở.

**Native callback accounting/admission 2026-10-03:** source
`c5e6314f6593a86fd5727747928b1deb217e94f3` bổ sung fixture chạy invoke và
callback lifecycle LangChain thật, chỉ fake generation/schema binding. Không
manually inject callbacks; parent logical starts/completions và synthetic
10/5/15 token counters khớp SDK baseline cho EN/VI/bilingual/invalid VI. Budget
fixture một call chặn call tiếp theo, giữ usage/event/checkpoints đầu tiên;
không thay product risk/allowance. 26 focused PASS, 45,88 s; full **2.231 + 88
subtests PASS**, 20 skips, 156 warnings, 230,77 s trên source sạch; Ruff/diff/
templates PASS. Ruff import-only đã sửa trước commit, không behavioral FAIL.
Synthetic reported usage không là vendor/billing proof; durable cross-attempt
ledger, elapsed/unknown usage, consent/restore/transport vẫn UNVERIFIED. Default
worker recorder/resume chưa bật; ingestion/UX/live finance/MT còn mở. Không AI/
vendor/CI/deploy/restart/migrate DB riêng tư; NQ=F BLOCKED theo owner, goal/PR mở.

**Actual recorder native spawn 2026-10-03:** source
`5195f554fc512cabff1752d9dffea07578c7a527` kiểm chứng exact production child,
AnalysisEngine, SnapshotRecorder và native graph trong process spawn thật.
Test bootstrap chỉ cài phản hồi SDK giả/network refusal; không thay engine/
graph/propagate/graph.invoke hay fingerprint/allowance guard. Bốn analyst,
hai rounds, EN/VI/bilingual/invalid VI khớp baseline prompt/model/stage trace
và published result fields. Parent-only commit vào SQLite reopen, không raw
reasoning/messages; hai SDK child đóng, PID child được reap, allowance/start
giữ nguyên. 18 focused PASS, 29,60 s; full **2.223 + 88 subtests PASS**, 20
skips, 120 warnings, 223,00 s tại source sạch; Ruff/diff/templates PASS.
Initial comparison FAIL do baseline còn internal state không được supervisor
publish; sửa so sánh theo RESULT_FIELDS hiện có, không nới production contract.
Synthetic SDK methods bypass accounting, usage vẫn incomplete, không là live
finance/MT proof. Default worker recorder/resume chưa bật; next accounting/
trusted client/consent và new-child restore, ingestion/UX/live vẫn thuộc goal.
Không AI/vendor/CI/deploy/restart/migrate DB riêng tư; NQ=F BLOCKED theo owner.
Goal và Draft PR #7 vẫn mở.

**Original context → supervised recorder 2026-10-03:** source
`7172e3c79b309772b994cd71125eb3673dbd04eb` thêm internal JSON context gốc,
revalidate ở parent/child và nối exact AnalysisEngine → SnapshotRecorder với
bridge commit. DB/lease/callback vẫn parent-only; context không chứa callable/
SDK/credential fields, không browser consent hay restore. Chặn sai owner/source/
book/policy, duplicate/nonfinite/oversized JSON và unknown fields; request sai
chặn trước spawn. 73 focused PASS, 31,96 s; full Python **2.219 + 88 subtests
PASS**, 20 skips, 108 warnings, 180,37 s tại source sạch; Ruff/diff/templates
PASS. Initial collection FAIL do fixture thiếu codec nodes, đã sửa trước gate;
không nới production contract. Child wiring là unit probe, chưa actual-engine
native-spawn proof. Default worker chưa bật recorder/resume; tiếp theo native
spawn, trusted client/accounting/consent và new-child restore. Không AI/vendor/
CI/deploy, restart/migrate DB riêng tư. Ingestion/UX/live finance/MT vẫn chưa
đạt; NQ=F BLOCKED theo owner. Goal và Draft PR #7 vẫn mở.

**Parent recorder allowance RPC 2026-10-03:** source
`98446bef42ce010b2a1733d9e91f198215e3ff78` nối kiểm tra allowance của recorder
qua exact private checkpoint-enabled bridge. Parent kiểm tra limits/fingerprint/
thread và clock/cancellation/lease gốc; ACK chỉ True, child không tạo clock hay
budget mới. Sai setup, boolean limits, identity/extra fields hoặc expired budget
chặn model/commit; child lỗi được xác nhận dừng. 38 focused PASS, 30,51 s; full
Python **2.184 + 88 subtests PASS**, 20 skips, 108 warnings, 179,33 s tại source
sạch; Ruff/diff/templates PASS. Chỉ RPC allowance: chưa chuyển trusted run/book/
source context, chưa actual recorder-native spawn/new-child restore hay owner
consent/accounting/API/UI; default worker không bật recorder/resume. Không AI/
vendor/CI/deploy, restart/migrate DB riêng tư. Goal/PR vẫn mở; ingestion/UX/live
finance/MT chưa đạt, NQ=F giữ BLOCKED theo owner.

**Actual recorder native acceptance 2026-10-03:** source
`c78908326a85bdeb642d4c0ad63afffdd92dc940` kiểm chứng AnalysisEngine/recorder/
native graph thật, SDK khởi tạo thật nhưng response giả và network bị chặn.
Bốn analyst, hai vòng debate/risk, EN/VI/bilingual/invalid VI khớp baseline về
prompt/call/stage trace và mọi result field ngoài messages. SQLite reopened
bytes bind owner/run/fingerprint, sequence liên tục, không raw reasoning hay
message values; bản run fixture cũ giữ nguyên. Đóng đúng hai SDK sync/async
instance và assert closed. 14 focused PASS, 21,36 s; full Python **2.171 + 88
subtests PASS**, 20 skips, 100 warnings, 264,81 s tại source sạch; Ruff/diff/
templates PASS. Gate trước tại 21a5ad1 cũng PASS nhưng không dùng thay proof
cleanup tại source mới. Test failures về fixture immutable run/messages metadata/
owner argument đã sửa đúng contract, không nới codec. Đây là same-process
synthetic native proof; SDK callback usage incomplete, không live financial/MT
hay supervised recovery acceptance. Default worker chưa bật recorder/resume;
tiếp theo trusted context/observer qua spawn, accounting/consent, new-child
restore; ingestion/UX/live vẫn mở, NQ=F giữ BLOCKED. Không AI/vendor/CI/deploy,
restart hay migrate DB riêng tư; goal và Draft PR #7 vẫn mở.

**Original-engine recorder wiring 2026-10-03:** source
`cb4e7061813c395d50e01fa61f6badb8418b016e` nối SnapshotRecorder nội bộ vào
AnalysisEngine thật: original context/expected fingerprint, observer và allowance
cũ bắt buộc; graph/client/source identity khớp mới truyền committed saver vào
snapshot sync hook. Không chấp nhận arbitrary factory/type hay non-snapshot;
ACK kiểm tra UUID/sequence int ở saver như bridge. 57 focused PASS, 21,55 s;
full Python **2.167 + 88 subtests PASS**, 20 skips, 80 warnings, 209,23 s tại
source sạch; Ruff/diff/templates PASS. Có collection FAIL do import limits từ
package chưa export, đã sửa đúng contracts.runs; không bỏ allowance gate.
Engine wiring test dùng SDK thật nhưng invocation spy, chưa full native/live
recording acceptance. Default worker/supervisor chưa chọn recorder; tiếp theo
trusted context/observer qua spawn, retained accounting/consent và new-child
restore. Không migrate DB riêng tư/restart/AI/vendor/CI/deploy; goal/PR vẫn mở,
live finance/MT, ingestion/UX còn chưa đạt và NQ=F giữ BLOCKED.

**Initialized graph identity guard 2026-10-03:** source
`c0d3cc7dbf832671b4aa1f58121e76634870e060` dựng fingerprint từ graph snapshot
thật và sync SDK đã khởi tạo, chặn sai effective config/roles/model/owner/source/
endpoint trước invoke. Graph giữ hash readers lúc construction, không giữ thêm
raw sources; nguồn đổi với hash mới hợp lệ vẫn không khớp graph cũ. 76 focused
PASS, 5,73 s; full Python **2.149 + 88 subtests PASS**, 20 skips, 50 warnings,
233,64 s tại source sạch; Ruff/diff/templates PASS. Tests dùng graph/SDK thật,
key giả và chặn model/network invoke. Đây chưa là complete transport/closure
attestation; engine/worker chưa chọn guard hay bật resume. Tiếp theo trusted
construction và original run/book context qua supervised boundary, retained
accounting/consent, restore trong child mới. Không migrate DB riêng tư/restart/
AI/vendor/CI/deploy; live finance/MT và UX/ingestion còn mở, NQ=F giữ BLOCKED.

**Native snapshot recording hook 2026-10-03:** source
`8b08628500df74e8641b151669bf8ee82cf9857d` thêm paired saver/canonical run-thread
hook vào propagate_snapshots thật; compile local và invoke sync, không thay
instance/CLI graph kể cả failure. Native spawn fixture đủ 14 stage giờ dùng
hook thật thay vì patch graph.invoke. 18 focused PASS, 23,48 s; full Python
**2.135 + 88 subtests PASS**, 20 skips, 22 warnings, 199,46 s tại source sạch;
Ruff/diff/templates PASS. Default AnalysisEngine/worker chưa chọn hook; không
restore/resume, migrate DB riêng tư, restart hay gọi AI/vendor/CI/deploy.
Tiếp theo trusted fingerprint/client construction và accounting/consent rồi
new-child restore; không bỏ execution_started hoặc reset allowance. Live finance/
MT, ingestion còn thiếu và operational UX vẫn thuộc goal; NQ=F giữ BLOCKED.

**Checkpoint DB-lock follow-up 2026-10-03:** source
`63d63d2b3aec6bf984080a15978cfea9464aa6bc` giới hạn từng thao tác chờ khóa
checkpoint (mặc định 5 giây), không phải deadline toàn transaction/network/disk.
SQLite rollback cả DBAPI transaction sau COMMIT lỗi trước khi restore timeout;
PostgreSQL dùng transaction-local timeouts nhưng live còn UNVERIFIED. Lỗi DB
không ACK, không vào thêm lease query không giới hạn. 37 focused tests PASS,
22,57 s; full Python **2.125 + 88 subtests PASS**, 20 skips, 22 warnings,
175,20 s tại source sạch; Ruff/diff/templates PASS. Test COMMIT-lock ban đầu
FAIL khoảng 5,24 s; sửa cleanup, không nới ngưỡng. Không migrate DB riêng tư,
restart, gọi AI/vendor, CI hay deploy. Production recorder/resume, trusted
identity, retained accounting/consent/API/UI và live finance/MT vẫn chưa đạt;
NQ=F giữ BLOCKED. Đọc receipt 2026-10-03 trước khi nối production graph.

**Opt-in checkpoint bridge 2026-10-03:** source
`90f009b28745e58dc17d7ad2e1a3eabbfefdc9ce` nối RPC checkpoint con → cha,
chỉ truyền fingerprint/thread identity; cha giữ codec/callback/DB/lease, kiểm tra
JSON/thread/ACK UUID-sequence-hash và cancellation/deadline trước ACK. Setup
thiếu hoặc factory không có recorder capability bị từ chối trước spawn; result
không có checkpoint bị từ chối khi opt-in. Default AnalysisEngine/worker chưa
bật recorder/resume. 11 bridge/crash tests PASS, 20,28 s; native fixture 4 ngôn
ngữ/invalid VI chạy đủ 14 stage qua RPC và SQLite parent commit. Kill cha trước
commit hoặc sau commit/trước ACK: con không còn executing orphan, DB giữ 0/1
row tương ứng; không gọi đó là reaped nếu zombie. Full Python **2.112 + 88
subtests PASS**, 20 skips, 22 warnings, 252,17 s; Ruff/diff/templates PASS.
Không migrate DB riêng tư/restart/AI/vendor/CI/deploy. Còn cần production graph
hook với trusted client/source identity, bounded parent DB-lock timeout, restore
ở child mới và consent/retained accounting/API/UI; không bỏ execution_started
hay reset allowance. Goal/PR mở, live finance/MT chưa đạt, NQ=F giữ BLOCKED.

**Native committed saver 2026-10-03:** source
`18c7d6975004863d08787d884bb359249c76a167` thêm internal native saver gửi
restricted JSON sau put/put_writes và kiểm tra ACK đúng bytes; lỗi/ACK mơ hồ
poison saver, không implicit retry. Phải dùng native durability="sync"; default
async không là fence. Invocation-only configurable helpers không persist, codec
state/metadata allowlist giữ nguyên. 350 focused tests PASS, 74,23 s: gồm 136
case đọc bytes đã commit thật trong SQLite tại 17 boundary × 4 language/invalid
VI × latest/pending, đủ 4 analyst và 2 rounds, prompt/call/stage trace và kết quả
ngoài messages khớp uninterrupted. Full Python **2.097 + 88 subtests PASS**,
20 skips, 22 warnings, 155,31 s; Ruff/diff/templates PASS. Chưa production
worker/supervisor hook hay separate-process crash recovery, không migrate DB
riêng tư/restart/vendor/AI call. Tiếp theo nối saver qua child bridge → parent
private commit/ACK, test crash/lease/cancel tại write/ACK, trusted construction
và explicit consent/accounting; không bỏ execution_started hoặc reset allowance.
Goal R01–R14/PR #7 mở, NQ=F giữ BLOCKED, live finance/MT còn chưa đạt.

**Private checkpoint persistence 2026-10-03:** source
`77b32d81a84f6abb4e5705fdd6a8e3e63e6c8852` thêm bảng riêng qua migration
`0011_research_checkpoints` và internal store append-only. JSON codec kiểm tra
owner/run/thread; ghi dưới publication_session hiện có, bind job/attempt/hash/
fingerprint và chỉ ACK sau commit. Bản pending-write mới không ghi đè bản cũ;
latest sai hash/identity không fallback về bản cũ. Không nằm trong ArtifactKind
hay reader báo cáo. 72 focused tests PASS, 2 skips; full Python **1.955 + 88
subtests PASS**, 20 skips, 22 warnings, 121,18 s; Ruff/diff/templates PASS.
Chỉ upgrade/downgrade DB fixture, không migrate DB riêng tư/restart/AI/vendor
call. PostgreSQL/concurrent writer và native saver/child bridge/crash/consent/
accounting còn UNVERIFIED; worker/API/CLI chưa dùng store và chưa bật resume.
Tiếp theo nối native saver qua supervised bridge, test commit/ack crash và
giữ execution_started/allowance/explicit consent. R01–R14 và Draft PR #7 mở;
NQ=F giữ BLOCKED, live finance/MT còn chưa đạt.

**Initialized-client prerequisite 2026-10-03:** source
`a120d5f33d6ed3653da187b470bf3f6c276ce638` đọc endpoint, timeout/retry và model
options từ SDK sync thật của các class OpenAI-compatible đã review, gồm MiniMax,
không invoke/network hay đọc auth headers. Builder chỉ chấp nhận trailing slash
do SDK thêm, không normalize bỏ host/path/query/credential khác. 62 focused tests
PASS; full Python **1.942 + 88 subtests PASS**, 20 skips, 22 warnings, 102,05 s;
Ruff/diff/templates PASS. Không bật recovery/restart, không AI/vendor call.
Đây chưa là complete transport attestation: cần trusted construction và bảo vệ
SDK/header/HTTP mutations, async/SDK khác còn UNVERIFIED. Tiếp theo xử lý các gate
này và private durable parent lease-fenced commit/ack; không bỏ execution_started
fence hoặc reset allowance. Receipt 2026-10-03 ghi source và limitation; R01–R14
vẫn mở, live finance/MT chưa đạt và NQ=F giữ BLOCKED.

**Recovery identity prerequisite 2026-10-03:** source
`c705cad32c3e6579c94942d8131ea32f0ac34def` thêm fingerprint riêng, không sửa
API config_hash/lịch sử và chưa bật worker recovery. Bind owner/run/asset/as-of/
roles, verified snapshots, full book/policy/risk-source content, actual config/
graph options/plan, supplied resolved-client descriptors và actual package source/
Python/dependency versions. 44 focused tests PASS; full Python **1.924 + 88
subtests PASS**, 20 skips, 131,46 s; Ruff/diff/templates PASS. Không gọi AI/vendor,
restart hay đổi provider/policy/frontend. Đọc
[receipt 2026-10-03](docs/platform/research-acceptance-20261003.md): descriptors
còn cần trusted attestation từ SDK client thật, chưa là auth/consent/lease proof.
Tiếp theo client-binding attestation + private durable parent commit/ack; không
bỏ execution_started fence hay tăng allowance. Goal R01–R14/PR #7 vẫn mở.

**Restricted checkpoint JSON 2026-10-02:** source
`25cb1d42f0b9372e475601c1cc39a7d9e373208b` thêm codec JSON native-v4, chưa nối
vào worker/CLI/API. Loại messages ở state/start/pending writes; giữ versions,
routing, task identity và schema-valid narrative/draft, chặn trường lạ, object
deserialization, payload quá lớn, authority/memory khác snapshot, writes trùng
và seen-version không có channel. 244 focused tests PASS; native 17 boundaries
× EN/VI/bilingual/invalid VI × current/JSON/pending-JSON khớp prompt/call/stage
trace và kết quả ngoài messages. Full Python **1.880 + 88 subtests PASS**,
20 skips, 128,73 s; Ruff/diff/templates PASS. Không chạy vendor/AI hay restart.
Production graph/supervisor vẫn giữ behavior cũ; đây không phải web resume.
Tiếp theo build fingerprint từ nguồn/config/runtime thật (không dùng riêng
API config_hash), rồi parent-fenced durable saver/commit-ack và explicit owner
continuation. Receipt và recovery contract giữ các gate chưa đạt; goal/PR mở.

**Recovery characterization 2026-10-02:** source
`60ef7e2c4b2ec04d51d9b564dcfeda5f9432d44a` thêm fixture native interruption tại
17 ranh giới, bốn analyst và hai vòng debate/risk, giữ bilingual presentation.
Bỏ current messages rồi tiếp tục cho prompt/call/stage trace và kết quả ngoài
messages giống chạy liên tục. Phải khôi phục `config_scope`; fixture ban đầu
FAIL khi bỏ scope, đã sửa đúng nguyên nhân. Đây chỉ là in-memory test, chưa là
durable checkpoint/resume cho web; không có paid/vendor call hay restart.
Đọc [recovery contract](docs/platform/research-recovery-contract.md) trước khi
implement serializer/fingerprint/parent commit-ack và explicit continuation.
Không bỏ execution_started fence hoặc tăng allowance cũ. Goal/PR vẫn mở.

**Bilingual supervised gate 2026-10-02:** source
`97b110d02596e8d57be6b0dd0b21f581c1e1b83b` chạy native graph đủ 14 stage qua
spawn ở English, Vietnamese và English + Vietnamese bằng fixture model. Giữ
canonical và horizon 3–6; presentation EN/VI trả về cha đúng nội dung. Fixture
tự thêm 25% bị từ chối sau một repair, không có decision payload hợp lệ và có
`report_translation_unavailable`. Full Python **1.640 + 88 subtests PASS**,
20 skips, 108,29 s; Ruff/diff/templates PASS. Chỉ test/docs, không đổi runtime,
prompt, provider hay frontend; không dùng quota AI. Đây không phải live MT/
financial acceptance. Tiếp theo ưu tiên fingerprinted graph recovery; các lỗi
live và NQ=F BLOCKED vẫn giữ nguyên, không tự chạy paid replay.

**Native/crash acceptance 2026-10-02:** source
`c4414a67a1c2d3b28169a0b201211457d635f626`. Native LangGraph thật qua spawn với
model giả lập chạy đủ 14 stage đúng thứ tự, giữ structured gate/600s SDK timeout/
retry 1 và không chạm CLI tool/memory/checkpoint/writes. Tiếng Anh-only: không
coi là bilingual/live finance proof. Process cha bị kill trong fixture: guard
dừng process con, không còn executing orphan trên macOS; zombie terminal không
được mô tả là process đã reaped. Full Python **1.637 + 88 subtests PASS**, 20 skips,
107,29 s; Ruff/diff/templates PASS. Không thay runtime production hay frontend,
không gọi vendor/model thật. Còn mở: bilingual supervised path, OS khác,
fingerprinted resume và live financial/translation acceptance. Xem receipt mới.

**Bridge concurrency follow-up:** runtime source hiện tại
`e1af4c35957918ae72debef3417ef24d2a1a767f` khóa cặp send/ack để callback threads
không xen frame hay lấy nhầm reply. Regression Python 1.634 + 88 subtests PASS,
20 skips, 109,11 s; một test concurrency bổ sung riêng PASS (thêm sau collection,
không gọi tổng thành một full run 1.635). Ruff/diff PASS; không đổi frontend.
Các gate native supervised graph/crash/resume/live của checkpoint dưới vẫn mở.

**Checkpoint process supervision 2026-10-02:** source
`be2149864ec0ffb91b7f8c3d79d88bd06087992c`. Default worker snapshot jobs chạy
graph trong process spawn, cha giữ observer/DB/lease/publication. Deadline,
cancellation và lease failure dừng/join process con, gồm SDK bị block, slow-read
hay retry/backoff; pipe reader riêng không chặn luồng kiểm tra allowance.
Usage/reader text được chuyển qua bridge, không gửi raw messages/reasoning;
nháp vẫn unvalidated, failure không tạo decision hay blind paid replay.
Full Python **1.634 + 88 subtests PASS**, 20 skips, 114,07 s; Ruff PASS; Web 137,
type/lint/build PASS. SDK tests dùng localhost/synthetic key, không vendor thật.
CLI/legacy live-tool và explicit injected engines giữ contract cũ. API chỉ công
bố default worker mode, không xác nhận worker đang chạy đã được nâng cấp.
Receipt 2026-10-02 ghi scope: native full graph qua spawn, crash/orphan và các OS
khác chưa nghiệm thu; graph resume/live quality còn mở. Chưa restart worker hay
chạy thêm AI trả phí. Tiếp theo nghiệm thu các gate này trước paid live mới.

**Checkpoint budget accounting 2026-10-02:** source
`fc6a8812cc4cde979c8aa72432b98966abf2ae50` reserve model starts atomically,
thêm remaining allowance dùng cùng monotonic clock và cancellation precedence.
Usage phân biệt logical LangChain calls với số request SDK không quan sát được
(`provider_request_attempts=null`); giữ usage trả muộn, không cho bắt đầu call mới.
Full Python **1.623 + 88 subtests PASS**, 20 skips, 46,66 s; Ruff PASS; Web 137,
type/lint/build PASS. Chưa hard-interrupt request, chưa resume hay paid live mới.
Tiếp theo phải supervise blocking request gồm retries/backoff/slow reads,
không dùng thread timeout rồi để request chạy ngầm, không cắt graph.

**Checkpoint UI allowance 2026-10-02:** source
`a2a0b6f6db38bc08102af853da889f874515a2a6` thêm chọn 30/60 phút trước consent,
đổi lựa chọn phải xác nhận lại và dùng request identity mới. Processing hiển thị
allowance đã lưu, không gán mặc định cho lịch sử thiếu trường. Web **137 tests**,
typecheck/lint/build PASS; built-app synthetic 1280×900/390×900 PASS, mỗi viewport
một POST giả lập, không gọi worker/provider, không lỗi console/page hay overflow.
Đây không phải hard deadline, cost cap hay graph resume; chưa paid live mới.
Skill React giữ state trong form và không thêm fetch/provider từ component.
Receipt 2026-10-02 ghi exact source và scope; goal/PR vẫn mở.

**Checkpoint allowance mới 2026-10-02:** source
`648fa183ee90eed1e353b3e06cbcc2c249aebb82` đã bind allowance rõ ràng cho API
snapshot run → manifest/config hash/job → worker observer. Mặc định 1800s/128
calls giữ nguyên; omission legacy không đổi hash/payload cũ. Full Python
**1.619 + 88 subtests PASS**, 20 skips, 59,09 s; Web 134, type/lint/build PASS.
Mode vẫn `cooperative_boundaries`, không phải ngắt cứng request. UI lựa chọn,
deadline transport và graph resume chưa có; chưa chạy paid BTC/AAPL mới.

**Checkpoint replay fencing trước, 2026-10-02:** runtime source
`93e797576b9179e088f6ff809761bddd34cc3df6` ghi dấu mốc trước engine và chặn
replay toàn-run sau lỗi execution/lease không rõ chi phí. Giữ retry hoàn tất
report/decision đã commit mà không gọi model; nếu outputs không còn đọc được,
không quay lại engine. Full Python **1.608 + 88 subtests PASS**, 20 skips,
50,14 s; Ruff/diff/templates PASS. Không tăng allowance hay đổi SDK retry/timeout.
Graph checkpoint resume vẫn chưa có; không lấy bản sửa này làm live acceptance.
Receipt 2026-10-02 ghi cả regression FAIL tại checkpoint trước và bản sửa.

Tiếp nối **2026-10-02**, source `1a01f21455fa351017319ad6283bb8307defe0ee`:
web đã tách bản nháp khỏi báo cáo hoàn chỉnh, chỉ tải khi mở đọc, cảnh báo
chưa kiểm chứng/không thể phê duyệt; đổi EN/VI không dịch nội dung gốc hay gọi AI.
134 Web tests, typecheck/lint/build PASS; built-browser synthetic 1280×900 và
390×900 PASS, zero console/page error/overflow/mutation, một note GET. Xem
[receipt 2026-10-02](docs/platform/research-acceptance-20261002.md). Đây không
phải live model/financial acceptance. Allowance/timeout và graph resume vẫn dở;
goal/PR vẫn mở, không tự chạy paid retry.

**Checkpoint retention trước:** code `ecbb7d3f25ac0d64defdc9231afabe8dea59edb0` lưu bản nháp
nghiên cứu bất biến sau khi từng vai trò trả kết quả, chỉ giữ reader text đã
allowlist và ràng buộc owner/run/source/config. Cancellation và lease chặn worker
cũ xuất thêm nội dung. Bản nháp luôn unvalidated, không đủ điều kiện phê duyệt;
không phải checkpoint để resume graph. Full Python **1.600 + 88 subtests PASS**
(20 skips), Ruff PASS; Web 122 tests, lint/typecheck/build PASS. Chưa live-test
code mới ở checkpoint đó; UI đọc bản nháp đã có tại 1a01f21 nhưng graph resume
vẫn chưa hoàn thành. Các sửa
SEC/translation tại `af5349d` vẫn được giữ.

Lượt BTC market+news tại `f73d1a9` **FAIL**: 37m38s / 539.339 token / 13 calls,
`RESEARCH_BUDGET_EXHAUSTED`, attempt 1/1, không xuất report/decision. Đã xong
chín stage trước Portfolio Manager; chưa chạy Financial validation/Report
presentation. Trần 30 phút hiện là kiểm tra giữa các bước, không ngắt request
model đang chạy. Không dùng sự kiện tiến trình để coi nội dung đã nghiệm thu.

Tiếp theo ưu tiên R08: allowance hiện rõ, tương thích request timeout và graph
recovery có fingerprint đầy đủ,
giữ source/config/model/prompt/owner/lease và toàn bộ vai trò. Không tự tăng trần
hay replay paid BTC; cần chủ repo duyệt lượt mới
sau khi sửa flow. AAPL full graph chưa chạy ở candidate mới; SEC source đã PASS.
NQ=F giữ BLOCKED theo quyết định chủ repo, không thêm provider. Xem phần cuối
receipt 2026-10-01 để có exact SHA và trạng thái. Goal và Draft PR #7 vẫn mở.

### Nhật ký các checkpoint trước

Goal R01–R14 vẫn **chưa hoàn thành**; Draft PR #7 chưa được merge. Nhánh
`fix/TA-R01-research-quality` nay có bước news hiện tại ngoài price: thu Yahoo
trong subprocess 45 giây, lưu snapshot bất biến và owner-scoped, xác minh
publication/retrieval/cutoff/hash/identity, endpoint `prepare-news` có auth/CSRF,
UI Anh–Việt cho phép chọn news tùy chọn trước consent AI. Feed bảy ngày là
`recent_feed_not_exhaustive`, không phải lịch sử đầy đủ hay nguồn social/
fundamentals/macro. Synthetic QA chặn mọi vendor/model.

PASS local tại worktree trước commit: Ruff toàn repo; Python **1.495 tests +
88 subtests**, 20 skips; Web **117 tests/21 files**, lint/typecheck/build; UI
synthetic desktop 1280px và mobile 390px có thao tác news lỗi, không gọi AI,
không tràn ngang, không pageerror. Direct Yahoo AAPL news smoke trả
`OK`, 100 bài trong khoảng 2,68 giây; chứng minh đúng **một lượt đọc nguồn**
trên máy này, không chứng minh toàn bộ flow live. Xem receipt mới nhất
[2026-10-01](docs/platform/research-acceptance-20261001.md) sau khi commit.

Còn mở: acquisition và hợp đồng evidence cho fundamentals/social/macro theo
asset, semantic finance và chất lượng dịch đã FAIL live, UI research/review
chưa nghiệm thu vận hành, live full-graph BTC/AAPL/NQ chưa chạy trên candidate
mới. NQ cần chọn rõ reference `NQ=F` hay `^NDX` trước khi coi là acceptance.
Không lấy kết quả local/synthetic/news smoke để nâng thành release approval.

Tiếp nối: chủ repo đã chọn `NQ=F` reference-only. Không thay bằng `^NDX` hay
QQQ. Yahoo continuous không có metadata active/next contract và rollover mà
pipeline futures yêu cầu, nên live NQ vẫn BLOCKED đến khi có nguồn hợp lệ.
Commit `cd033dd` thêm cảnh báo song ngữ bắt buộc cho news feed không đầy đủ;
1.496 Python tests + 88 subtests PASS, 20 skips. Chưa chạy thêm AI; xem
receipt 2026-10-01 để phân biệt gate đã/chưa nghiệm thu.

Tiếp nối tại `f69e329`: chủ repo đã duyệt dùng SEC EDGAR hiện có riêng cho
AAPL web, không đổi CLI default. Có collector filed-date-aware, snapshot bất
biến, endpoint/UI tùy chọn, fact-ID cho kiểm chứng số và bố cục báo cáo song
ngữ dễ đọc hơn. Local PASS 1.505 Python tests + 88 subtests (20 skips), 121
Web tests, build/lint/typecheck; browser synthetic desktop/mobile PASS cho SEC
unavailable, chưa phải live SEC. `SEC_EDGAR_USER_AGENT` chưa có trong worktree
ở lúc kiểm tra; không dùng contact mẫu. Social/macro vẫn chưa acquisition;
semantic finance/translation và live BTC/AAPL chưa được nghiệm thu. NQ=F chủ
repo chọn giữ BLOCKED, chưa thêm provider; không thay bằng ^NDX/QQQ.

Tiếp nối tại `2547669`: đã sửa layout để báo cáo hiện trước sau khi hoàn tất,
tiến trình được giữ trong mục mở rộng; active/error vẫn hiển thị trực tiếp.
Fixture song ngữ đi qua compiler/validation/worker/API thật với đầu ra synthetic
được ghi nhãn rõ. Browser desktop 1280×900/mobile 390×844 PASS các tab và chuyển
EN/VI, giữ nguyên số, không tạo run mới khi đọc, không tràn ngang/pageerror;
trang quyết định liên kết giữ phê duyệt disabled khi không có portfolio/risk.
Full Python 1.506 + 88 subtests PASS (20 skips), Web 122 tests PASS,
typecheck/lint/build PASS. Đây là UI/integration proof, không phải live model
hay translation acceptance. Kiểm tra tiếp đã tìm thấy contact SEC hợp lệ trong
`.env` ignored ở checkout gốc: AAPL API live SEC PASS 1.159 facts, zero invalid,
latest filing 2026-07-31. BTC API giá/news PASS và bind hai snapshot; chưa phải
full graph. Worktree chưa tự nạp root env, nên QA phải nạp rõ file gốc và assert
MiniMax-M3; initial QA default-OpenAI run đã cancel trước model call. Các gate
live finance/translation vẫn mở.

Yêu cầu mới nhất của chủ repo: lưu toàn bộ code, phần dở và ngữ cảnh lên GitHub
để có thể tiếp tục từ máy khác hoặc Claude. Đây là checkpoint công việc, chưa
nghiệm thu sản phẩm và chưa merge PR.

## Checkout đúng nhánh

```sh
git clone --branch fix/TA-R01-research-quality https://github.com/phankietit/TradingAgents.git
cd TradingAgents
git status --short
git rev-parse HEAD
```

- Nhánh tiếp tục: `fix/TA-R01-research-quality`.
- Draft PR: https://github.com/phankietit/TradingAgents/pull/7 (base `main`).
- `origin/main` được kiểm tra tại `7dfec4d20709a702b130f3ba5813f097a930ffe6`.
- Baseline trước checkpoint: `0696141fddb8b5b7bde7cbde21aa408015716e58`.
- Candidate đã full-test gần nhất: `97b110d02596e8d57be6b0dd0b21f581c1e1b83b`.
  Runtime production của supervisor giữ nguyên từ `e1af4c3`; candidate này bổ
  sung test và cập nhật chỉ dẫn, không phải một lượt phân tích live mới.
- PR #7 đã chứa code prerequisite của PR #5 (bilingual) và #6 (data flow).
  Không cherry-pick lại hoặc merge các PR này chỉ để phục hồi checkpoint.
- Nhánh `chore/governance-bootstrap` lưu nguyên bộ governance từ checkout gốc.
  Nhánh sản phẩm này cũng chứa các rules cần để tiếp tục độc lập.
- Nhánh `fix/TA-M4-model-env` lưu commit riêng `d5eecfe`; đây là nhánh lưu trữ,
  không phải bước bắt buộc để khởi động. Đối chiếu diff trước khi tích hợp vì
  nhánh sản phẩm đã có xử lý model env.
- Các milestone cũ: `feature/TA-018-observability-baseline` và
  `feature/TA-027-data-health-engine` đã ở origin; cả hai worktree local sạch.

Đọc tiếp: [AGENTS](AGENTS.md), [routing](docs/ops/agent-map.md),
[backlog R01–R14](docs/platform/research-remediation.md),
[bằng chứng mới nhất](docs/platform/research-acceptance-20261002.md).
Receipt milestone cũ chỉ chứng minh SHA ghi trong receipt, không chứng minh HEAD.

## Mục tiêu và yêu cầu đã chốt

Nền tảng hỗ trợ quyết định đầu tư cá nhân, giao diện web Anh–Việt hiện đại,
phong cách tài chính sạch, dễ đọc cho người không chuyên kỹ thuật. Nhóm tài sản:
US large caps, ETF/chỉ số tham khảo, BTC/ETH. NQ/ES chỉ tham khảo, không thực thi
futures. Không broker, không thay risk limits hay provider, không sửa lịch sử.
LLM viết nghiên cứu; tính toán danh mục/policy phải xác định và có human approval.

Giữ toàn bộ LangGraph: analyst theo phạm vi nguồn, Bull/Bear, Research Manager,
Trader, Aggressive/Conservative/Neutral, Portfolio Manager, Financial validation,
Report presentation. Không bỏ vai trò hay lấy dữ liệu hiện tại bù lịch sử để
ép kết quả đạt. MiniMax hiện dùng cho cả model nhanh/chậm. Thiết kế bằng code,
không ImageGen. Test local/manual; GitHub CI đã được disable trong checkpoint.

## Đang có và đang dở

- Python/CLI + FastAPI, durable worker, immutable artifact store, auth owner,
  React/Vite UI, progress/retry/cancel/usage, tách research/portfolio approval.
- Snapshot giá có session/cutoff và full-history indicator/return xác định;
  analyst truy vấn snapshot đã khóa. Dữ liệu thiếu không được biến thành trung tính.
- Strict MiniMax JSON parser, một lần format repair, kiểm tra số liệu/provenance,
  percentage statements EN/VI xác định, dịch theo block với protected quantities.
- UI đã có browser synthetic desktop/mobile receipts; các lỗi browser tool ở
  checkpoint cũ không còn là mô tả trạng thái mới nhất. Chất lượng tài chính và
  vận hành live vẫn chưa được nghiệm thu; không lấy screenshot làm finance proof.
- `tradingagents/dataflows/platform_news.py` đã commit/test: collector Yahoo news
  có publication/retrieval time, nhận diện asset và trạng thái lỗi/phạm vi nguồn.
- Tại checkpoint 2026-09-27, `NewsSnapshotService` mới là WIP chưa test hoặc
  nối API/UI. Bản tiếp nối 2026-10-01 đã xử lý phần này; xem cập nhật trên.
- Web `prepare-data` vẫn chỉ persist giá; `prepare-news` là bước riêng. Có
  reader social/fundamentals không đồng nghĩa có ingestion. R04 chưa hoàn tất.

## Kết quả kiểm chứng và lỗi phải xử lý

Full regression ở `50dd0df`: **1.482 tests + 88 subtests PASS**, 20 skip, 39.94s;
Ruff PASS. 20 skip gồm 18 PostgreSQL, optional Bedrock và live DeepSeek. Không
chuyển kết quả này sang file WIP hoặc HEAD mới một cách mặc định.

Live BTC ở `5bbbdee` chạy đủ 11 stage, 14 model calls, **480.325 token**.
Automatic validation không báo lỗi và tạo Hold research, nhưng **manual FAIL**:
nhận định xác suất mean reversion/tax-driven exits chưa có bằng chứng tương ứng;
dịch “preserve optionality” thành “duy trì quyền chọn” sai nghĩa. Đây là snapshot
market-only, không phải full-source/fresh-data/queue/browser acceptance.

Live AAPL full-graph ở `f70907f`: 15 calls, **430.934 token**, manual FAIL do diễn
giải phần trăm và tiếng Việt. Sau đó có sửa công thức và kiểm tra thành phần.
Translation replay ở `2cd2609`: 1 call, **21.417 token**, số liệu giữ nguyên,
nhưng manual FAIL vì mất qualifier “aggressive” và văn phong lặp. Prompt đã sửa
ở `5bbbdee`; sửa prompt không chứng minh khả năng dịch đúng một cách tổng quát.

Không có USD cost chính xác từ provider. Token usage không phải hóa đơn.
NQ chưa live-test: chủ repo đã chọn `NQ=F`, giữ BLOCKED do thiếu contract/roll
metadata. Không thay bằng `^NDX` hoặc ETF; đây không phải acceptance đã đạt.

## Công việc tiếp theo có thứ tự

1. R08 đã lưu reader text riêng tư bằng publication fence; chưa phải resume.
   UI đọc bản nháp/chọn allowance đã có synthetic proof, allowance bind API và
   default worker process supervision đã triển khai; supervised bilingual path
   đã có fixture proof. Hoàn thiện durable graph recovery trước
   paid acceptance mới; giữ tất cả analyst/debate/risk/validation/presentation,
   không tự nâng budget hoặc biến partial report thành decision. Kiểm tra bằng
   local fixtures trước. BTC mới cần duyệt; AAPL đã được duyệt nhưng chưa chạy.
2. News service và prepare-news đã có local test, browser synthetic, một lượt
   Yahoo AAPL trực tiếp; còn cần live API/snapshot/run acceptance và kiểm soát
   coverage theo từng nguồn. Không coi một feed gần đây là lịch sử tin tức.
3. Hoàn thiện nguồn fundamentals, social, macro phù hợp từng asset và hợp đồng
   evidence/number tương ứng; giữ nguyên provider hiện có.
4. Xử lý semantic evidence và tiếng Việt từ các lỗi live đã lưu. Tránh tiếp tục
   chỉ thêm blacklist từng câu hoặc dùng numeric parity để chứng nhận ý nghĩa.
5. Hoàn thiện flow chuẩn bị → nghiên cứu → kiểm tra → đọc quyết định; tổng kết,
   luận điểm đối lập, rủi ro, invalidation và coverage cần dễ đọc trên desktop/mobile.
6. Chạy scope-appropriate local gates; sau khi có sửa đáng kể mới làm live BTC,
   AAPL, NQ nghiệm thu. Ghi SHA/input/coverage/usage/kết quả manual. Không replay
   tốn phí tự động chỉ vì clone repo hoặc đọc tài liệu bàn giao.
7. Chỉ complete khi acceptance toàn bộ đạt. Giữ PR draft đến khi đủ bằng chứng.

## Chạy trên máy mới

Python baseline đã dùng: 3.14.7; Node 26.8.1/npm 11.19.0. Khả năng hỗ trợ version
khác theo `pyproject.toml`, cần kiểm tra môi trường mới.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev,platform]'
cd web
npm ci
npm run build
cd ..
bash scripts/verify-local.sh
```

Tạo `.env` từ tên biến trong `.env.example`, bổ sung secrets qua kênh riêng.
Cấu hình model không bí mật được kiểm tra lúc bàn giao:

```dotenv
TRADINGAGENTS_LLM_PROVIDER=minimax
TRADINGAGENTS_QUICK_THINK_LLM=MiniMax-M3
TRADINGAGENTS_DEEP_THINK_LLM=MiniMax-M3
TRADINGAGENTS_LLM_BACKEND_URL=https://api.minimax.io/v1
TRADINGAGENTS_OUTPUT_LANGUAGE=Vietnamese
TRADINGAGENTS_MAX_DEBATE_ROUNDS=1
TRADINGAGENTS_MAX_RISK_ROUNDS=1
```

Các QA replay đã override output language thành `English and Vietnamese`.
Không suy ra thinking/max_tokens khác từ env trống. API và worker cần cùng model
env/database/artifact root. FRED cần key; SEC cần user agent liên hệ; Yahoo giá/
news không cần API key. Xem `.env.example` và config cho đường nguồn thực tế.

Theo [local-web-startup](docs/platform/local-web-startup.md) để cấu hình đường
dẫn DB/artifact/web/dist theo máy mới, bootstrap **DB mới** và owner, rồi chạy
`tradingagents-api` và `tradingagents-worker` ở hai terminal. Worker có thể phát
sinh phí AI khi có job. Dùng loopback `http://127.0.0.1:8000`.
Không dùng bootstrap/reset/migration test lên DB chứa lịch sử người dùng.

Frontend checks: `cd web && npm run typecheck && npm run lint && npm test && npm run build`.
PostgreSQL chỉ dùng DB test bỏ được và hướng dẫn `scripts/verify-postgres-local.sh`.
Trên máy cũ Colima bị lỗi và restart chưa được owner xác nhận; máy mới có thể
dùng môi trường local riêng. Không thay đổi VM đang dùng bởi tác vụ khác.

## Dữ liệu riêng không có trong clone public

GitHub repo này là **public**. Code, rules, kế hoạch và receipt đã ở Git. Các mục
sau không được đưa lên GitHub public: `.env`, API keys, owner DB/password/session,
raw reports/snapshots, portfolio/history, checkpoint/cache, logs và ảnh QA chứa
thông tin cá nhân. Clone mới đủ để tiếp tục phát triển, nhưng không tự phục hồi
dữ liệu phân tích/đăng nhập hiện có.

Để giữ đúng lịch sử: chuyển `.env` qua secret manager/kênh bảo mật; tạo backup
nhất quán của DB bằng công cụ DB phù hợp và chuyển **cả artifact store** qua kho
private mã hóa. DB và artifact store là một cặp; chỉ copy một bên không đủ.
Xác minh hash, ownership và đường dẫn sau restore. Không copy DB SQLite đang
ghi bằng thao tác file đơn giản; dùng SQLite backup hoặc dừng writer có kiểm soát.
Chưa tạo hoặc tải backup riêng trong checkpoint này vì chưa có đích private.

Vị trí cũ để tìm dữ liệu khi cần: env tại checkout gốc
`/Volumes/Data/Project/TradingAgents/.env`; runtime dưới
`/Volumes/Data/TradingAgents-runtime/trial/`. Giá trị đường dẫn DB/artifact chính
xác lấy từ env trên máy cũ, không đoán. Worktree code cũ:
`/Volumes/Data/codex/worktrees/ta-030-analysis-risk/TradingAgents`.

Các helper QA dùng trong phiên được lưu nguyên source text ở
`docs/handoff/qa-source/`. Chúng phụ thuộc DB/artifact private, đường dẫn máy cũ
và parent report IDs; chưa portable hoặc live-test trên máy mới. Sửa cấu hình
cho bản sao DB private và review script trước khi chạy. Không lưu output raw vào Git.
Các script này có thể gọi MiniMax và tiêu token; không có job tự chạy khi clone.

Ảnh giao diện cũ không thay thế kiểm tra UI HEAD. Style contract nằm ở
`docs/platform/research-remediation.md`; không cần truy cập máy cũ để hiểu layout.

## Prompt để bàn giao cho Claude/agent khác

> Đọc HANDOFF.md, CLAUDE.md, AGENTS.md và docs/ops/agent-map.md. Tiếp tục trên
> fix/TA-R01-research-quality, Draft PR #7. Giữ mục tiêu R01–R14 và các boundary đã
> chốt. Bắt đầu từ receipt mới nhất để kiểm tra supervision/recovery còn thiếu,
> rồi hoàn thiện ingestion ngoài giá, semantic quality và UI/process theo backlog.
> NewsSnapshotService đã có API/UI, không bắt đầu lại như một WIP chưa tích hợp.
> Kiểm tra trạng thái Git
> và bằng chứng mới trước khi hành động. Dùng local tests; không CI, không tự merge,
> không sửa lịch sử, không đổi model/provider hay mở paid runs từ riêng prompt
> bàn giao này. Báo cáo rõ mọi acceptance chưa đạt, đừng gọi toàn bộ goal complete.
