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

The existing qualitative evidence and translation-intensity diagnostics remain
unresolved. Full source input, numeric correctness and citation identity do not
prove semantic entailment or faithful translation. Default worker does not yet
activate owner-authorized durable continuation; internal native tests are not
default-owner/browser/live-operational proof. NQ=F remains owner BLOCKED without
contract/roll metadata. No paid AI, new provider, risk-limit change, CI, private
history rewrite, broker, public deployment or production-readiness claim.
