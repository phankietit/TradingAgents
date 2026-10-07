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

### Exact full corrective regression

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
