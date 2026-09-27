# Renewed research-flow acceptance — 2026-09-27

Class: local private research candidate, not release approval. Branch
`fix/TA-R01-research-quality`, Draft PR #7. Same configured MiniMax provider and
models; no broker, public deployment, risk changes or historical rewrites.

## Reproduced failures

On `1b38109a9dae1735f64e16f9ba1f8969860cf420`:

- BTC run `3a8beedd-04e9-4068-98cc-19ab391f2772`, report
  `ea962da8-15a4-500e-a58e-9336387b7046`: FAIL valid-report acceptance.
  Unsupported derived financial quantities prevented canonical publication.
  Provider reported 263,010 input + 90,840 output = 353,850 tokens, 11 calls.
- AAPL run `c203877a-6f1a-4499-8ab7-d7f0f9bbdeab`, report
  `c3a8616d-2ca3-5ce4-b526-6edcad4add08`: FAIL valid-report acceptance.
  Unsupported financial quantities persisted through formatting repair.
  Provider reported 300,805 input + 97,108 output = 397,913 tokens, 11 calls.
- A separate financial-repair component check also failed quantitative and
  material-claim checks: 75,201 reported tokens, two calls. This was not a full
  graph acceptance run and did not mutate either historical report.

Processing completion was not promoted to valid research. All failed artifacts
remain immutable. These failures motivated quantity-bound draft compilation and
a separate financial-validation stage, rather than more whole-graph retries or
weaker publication gates.

## Candidate and local evidence

Backend candidate: `ac14bdbf9ef138d070bdeed94e0300eca7f56dbb`.
The subsequent `b2a1f85` changes only mobile UI/tests, changelog and documentation.

- PASS: `TA_ALLOW_TEST_DB_RESET=1 bash scripts/verify-postgres-local.sh`,
  Python 3.14.7, Ruff/dependency checks, 1,381 tests + 88 subtests, 48.52 seconds.
  Two skips remain UNVERIFIED: optional Bedrock package and DeepSeek live key.
  Script removed only its ownership-labelled disposable PostgreSQL container.
- PASS: `npm run build && npm run lint && npm test -- --run`, Node 26.8.1,
  115 tests across 21 files after the mobile/deep-link additions.
- PASS: browser submitted BTC and AAPL through the real authenticated form,
  including data preparation and explicit per-run AI confirmation.
- PASS: mobile 390×844 progress has no horizontal document overflow; compact
  run selection keeps the active process above the old history list. Desktop
  retains list/detail navigation. Final valid-report presentation remains
  UNVERIFIED until live output passes.

## Live candidate runs

Both workers started from clean backend candidate `ac14bdb`, with full original
market-only debate/manager flow and five-year stored daily price history. Their
scope does not include news, sentiment, fundamentals or macro evidence. API
process was started earlier; unchanged preparation/run routes served the tests.

- BTC `f6879da4-309d-4e2c-9653-1eac6219b702`, job
  `e5b6e1cd-4fbd-4ee8-85fc-d68523167f99`: FAIL acceptance. Report
  `3215c517-c475-5627-9f27-50a7820fa00f` withheld bilingual readiness.
  Canonical numerical references replayed, but manual review found a reciprocal
  percentage-description error and a false claim of unavailable volume history.
  Translation failed. 245,892 input + 130,748 output = 376,640 tokens, 15 calls.
- AAPL `cef5e869-189c-42c9-81a3-3620e3b529e2`, job
  `0699bd52-d3d6-438e-88a9-6a391899d26e`: FAIL acceptance. Report
  `12673674-0609-531e-b41f-e87f81c4832a` failed exact material-claim mapping and
  strict JSON repair. 275,456 input + 129,062 output = 404,518 tokens, 13 calls.

## Subsequent remediation and environmental limits

- Source-linked draft paragraphs remove duplicate whole-thesis citation text.
  The compiler preserves supplied source IDs; unknown sources still fail.
- Financial review now checks meaning before deterministic publication gates;
  failed upstream structured repairs also prevent readiness. Financial literals
  are rejected at their schema field, including approximate/conditional amounts.
- Official MiniMax endpoints retain the same configured provider and credentials
  while enabling documented reasoning separation and tool-turn metadata handling.
- Publication-only replay of saved AAPL research used 82,941 tokens (three calls)
  and still failed on unbound approximate percentages. It is component evidence,
  not a successful full analysis; no historical report was modified.
- A later PostgreSQL gate was interrupted by Python `Bus error` (exit 138).
  Colima became inaccessible/Broken; task-owned container cleanup was withheld
  because its label could no longer be verified. No broad VM restart or deletion
  was attempted. SSD identity/free space was rechecked and valid. The app uses
  SQLite, and its task-owned API was restarted successfully (HTTP 200).
- A local non-PostgreSQL regression passed 1,370 tests + 88 subtests with 20 skips
  in 252.86 seconds before the final field-validator/upstream-gate additions;
  targeted follow-up passed 36 tests. Exact final-candidate regression is pending.

## NQ preflight

BLOCKED for a live NQ report: the real form rejects automatic `NQ=F` preparation
before AI because reference-futures input requires contract and roll metadata.
Read-only Yahoo history returned bars and FUTURE type but did not establish
active/next-contract or historical roll metadata. The existing futures-reference
pipeline requires those inputs and CME session evidence; they were not invented.
No Nasdaq index/ETF was silently substituted. Owner clarification between `NQ=F`
and cash index `^NDX` is pending. No model quota was consumed by this preflight.

Goal remains active. Valid final reports, financial/language review and remaining
browser acceptance must pass before completion can be claimed.
