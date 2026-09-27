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

## Fixed-candidate follow-up

- PASS: clean `678fe00edb1c4b7ec0d23b735142b7df25037f47`,
  `bash scripts/verify-local.sh`: 1,372 tests + 88 subtests, 20 skips,
  400.01 seconds. Ruff/dependency checks passed. Eighteen PostgreSQL skips
  remain BLOCKED by the local VM issue; Bedrock and DeepSeek remain UNVERIFIED.
- FAIL: publication-only AAPL replay on that candidate used 137,442 reported
  tokens (70,794 input + 66,648 output), four calls. Canonical report and
  translation were not accepted. Unused quantity bindings were reported with
  an overly generic numeric error; the repair also violated uppercase key
  syntax. No source evidence or historical artifact was rewritten.
- Follow-up separates allowlisted binding failure codes and explicitly states
  placeholder syntax and one-to-one usage. All previous rejection conditions
  remain; the compiler never silently removes unsupported claims or bindings.
  Targeted compiler, financial-stage and structured-agent tests: 64 PASS.
- Further browser verification is BLOCKED: in-app browser could not verify its
  admin-enforced policy for localhost. No security bypass or indirect browser
  access was attempted. Earlier screenshots/interaction receipts remain scoped
  to their original candidate; no final valid-report screenshot is claimed.
- PASS: clean `c34258d3eb602431154e661205aa1f5522259aea`,
  `bash scripts/verify-local.sh`: 1,377 tests + 88 subtests, 20 skips,
  244.18 seconds. Skip classifications above remain unchanged.
- FAIL: a financial-validation-only replay reused the saved AAPL draft without
  rerunning research or PM. It used 68,508 tokens (14,424 input + 54,084 output),
  two calls. The repair had 19 used bindings, no unused/missing bindings, but
  added 12 instrument-metadata fields forbidden by the report schema. The
  rejected object was not stripped, published or promoted to a valid report.
- Follow-up explicitly separates input metadata from output and lists the exact
  permitted top-level schema fields on both the initial and bounded repair
  attempt. This does not relax additional-field rejection or evidence checks.
  Live acceptance of this final prompt change remains UNVERIFIED; no further
  whole-graph paid run was opened while NQ/environment gates remain unresolved.
  Targeted compiler, financial-stage, structured-agent, engine and localization
  checks passed 81 tests in 5.55 seconds; Ruff passed. The full regression above
  predates only this prompt-boundary change and its regression test.

## Continuation audit

- PASS: clean `1bf543323ae78b658df80a1012d20a07ba6a1e00`, full local gate:
  1,378 tests + 88 subtests, 20 classified skips, 142.40 seconds.
- PASS: fresh core-only Python 3.14 venv installed a non-editable wheel built
  from that SHA, resolving dependencies independently. Isolated CLI/graph
  imports ran outside the checkout, `pip check` passed, and neither SQLAlchemy
  nor exchange-calendars was installed. Wheel SHA-256:
  `b070e9bb0ee7ef4b31ee42ca45af526ae95b6c6d80846ad92214e0049ff57aea`.
  This proves core installation on this interpreter, not the platform extra,
  every supported Python version or unchanged dependency resolution forever.
- Publication replay on that SHA passed schema, source-bound numerical values
  and protected numeric translation, using 50,007 tokens (19,803 input + 30,204
  output), four calls. **Manual financial/language acceptance remained FAIL**:
  the prose reused an indicator-relative percentage for a move from the close,
  used a negative signed change as a magnitude below a high, and translated
  volatility/volume as liquidity and a crossover as divergence. No full run was
  registered, no old artifact was rewritten and this was not promoted to a
  successful investment conclusion.
- Follow-up adds placeholder-specific rejection of those reproduced percentage
  relations, explicit formula feedback, a financial translation glossary and
  conservative terminology-substitution checks. It does not silently rewrite
  prose, select another fact, relax schema validation or remove research roles.
  Other qualitative entailment and translation quality still require review.
  Initial targeted regression: 45 PASS; final candidate/live evidence pending.
- PASS: clean `1e72eb2cd4b3249083784c38b18b8070e862ead0`, full local gate:
  1,386 tests + 88 subtests, 20 classified skips, 47.05 seconds.
  The candidate wheel was installed into the isolated core environment;
  report/compiler, CLI and graph imports passed before platform dependencies
  were added. After installing the declared platform extra, API/worker imports
  and `pip check` passed. No owner runtime dependency was changed. Wheel hash:
  `3ee4dbad1a217308db58beb8dc4d6cc5168466d883e0e1be6d20108bd9f9e7c7`.
- FAIL: bounded financial replay on `1e72eb2` was correctly withheld by
  `percentage_relation_requires_review`, including after its one repair.
  Usage: 47,471 tokens (15,012 input + 32,459 output), two calls; translation
  was not called. This is fail-closed evidence, not usable-report acceptance.
- Follow-up reports all affected placeholder keys together, rather than a
  generic error or one mismatch at a time. Only syntax-validated placeholder
  identifiers enter diagnostics; provider prose and private values do not.
  It also catches the reciprocal upper-band and generic percentage-move forms
  observed in the rejected repair. No claim or fact is silently rewritten.
- PASS: clean `93e3411a0c32f7388b75b8fe0635ddce1ea40c07`, full local gate:
  1,389 tests + 88 subtests, 20 classified skips, 42.97 seconds.
- Publication component replay on that candidate passed canonical validation
  and EN/VI numeric/terminology checks after one bounded financial repair.
  Usage: 59,811 tokens (17,833 input + 41,978 output), three calls. Manual
  review confirmed correction of the observed reciprocal/drawdown errors and
  crossover/volatility substitutions. Vietnamese wording remained overly literal;
  final editorial and whole-run acceptance were not claimed. The saved QA blob
  remains separate from registered analysis/decision history.
- A separate unit audit found RSI had been divided by the quote-currency close
  in the catalog. Snapshot facts v4 withholds that dimensionally invalid ratio,
  retaining raw RSI and valid price-unit ratios. No source candle, snapshot or
  historical report is rewritten. Targeted unit/catalog/translation checks pass.
  Binding instructions now state each reciprocal fact ID's exact meaning.
- Translation-only follow-up targets financial Vietnamese wording, retaining
  the accepted canonical report, numerical anchors, opposing case and conditions.
  It is not another research or whole-graph run.
- PASS: clean `9d9f8f4f35a26a054c58a16afc470ccabd660bb2`, local regression:
  1,390 tests + 88 subtests, 20 classified skips, 181.46 seconds; Ruff passed.
- FAIL: translation-only replay used 53,377 tokens (10,546 input + 42,831
  output), two calls, and failed localized numeric parity. Canonical English
  remained intact. Rejected raw translation was not retained, so its exact
  offending phrase is UNVERIFIED.
- Independently reproduced a lexer inconsistency: `EMA10` versus `EMA 10`
  falsely failed parity, while range `3-6` was protected as separate `3` and
  `-6` anchors. Shared recognition now counts indicator digits consistently and
  protects dates/ranges intact. Tests still reject changed periods, endpoints
  and signs. This fixes a proven checker defect, not proof of the live failure's
  exact wording; subsequent live acceptance remains required.
- PASS: candidate `da2a675`, local regression 1,394 tests + 88 subtests,
  20 classified skips, 186.76 seconds; Ruff passed. Translation-only replay
  consumed 8,250 tokens (2,942 input + 5,308 output), one call. Canonical English
  was byte-for-value unchanged outside the localized field; numeric parity passed.
  **Manual translation acceptance remained FAIL**: one sentence attached the
  moving-average period to the price extension and its percentage to SMA.
  Numeric multiset equality is not semantic fidelity and is not sufficient for
  report acceptance. QA blob: `sha256/50/5c/505c77319104018ee665d524780f7c95eb6f0586de1bbaadd77cb0faeaa7363c`.
- Follow-up protects the complete moving-average name (`200-SMA`, `EMA 10`,
  `SMA50`) as one atom and supplies non-numeric anchor-role metadata. This
  reduces the reproduced period/percentage confusion without rewriting the
  canonical conclusion or removing any research stage. It is not a universal
  semantic guarantee; live editorial acceptance remains UNVERIFIED.
- PASS: `f70907f5dd47ed58311790e60136dc926be097c0`, local regression 1,396
  tests + 88 subtests, 20 classified skips, 254.86 seconds; Ruff passed.
  The 20 skips remain 18 unavailable PostgreSQL gates and two optional-provider
  checks, not implicit passes.
- Translation-only replay on that SHA preserved the canonical report and
  corrected the observed indicator/percentage attachment after one bounded JSON
  repair: 20,264 tokens (9,053 input + 11,211 output), two calls. Remaining
  Vietnamese phrasing is still awkward; editorial readiness remains UNVERIFIED.
  QA blob: `sha256/4d/9c/4d9cca7344a396a4c0c8961d33b14899f571653a556fb1d3fd5a5d7497a1c1ba`.
  This component replay does not prove whole-graph or browser acceptance.
- Full AAPL engine replay on immutable existing market snapshots, candidate
  `f70907f5dd47ed58311790e60136dc926be097c0`, completed the original available
  market-only research/debate graph, financial validation and EN/VI presentation.
  Schema/source/numeric gates returned no issues and a decision payload.
  Usage: 430,934 tokens (269,994 input + 160,940 output), 15 calls.
  **Manual financial acceptance: FAIL**. The thesis described the EMA as
  1.68% below the close using a fact measuring the close above EMA; the reciprocal
  denominator differs. The observed `EMA at $... sits only ...% below the close`
  wording is now included in the bounded relation guard. Translation remains
  overly literal and editorial acceptance is FAIL. Automated success was not
  promoted to readiness, no registered run was rewritten or added, and this
  replay does not test current-data ingestion, durable queue or browser UX.
  QA blob: `sha256/49/6b/496b75fa468735b1878e55d89e6d6b32124fcd7231d83c7b8f7838b3f63346a4`.
- PASS: `340d0cb` targeted compiler/localization/repair/engine tests: 58 in
  4.05 seconds; financial-validation-stage tests: 4 in 3.01 seconds; Ruff passed.
  An initial command named a nonexistent test file and ran no tests; the actual
  stage test file was subsequently run as recorded above. Full-suite evidence
  remains tied to `f70907f`, not this later bounded regex fix.
- Remaining design gap: numeric/source binding plus known prose-pattern guards
  cannot guarantee arbitrary quantitative prose semantics. A typed relationship
  representation (subject, reference, denominator and direction) should be
  evaluated before further expensive whole-graph retries; it must preserve
  original research arguments and cannot rewrite a model conclusion to pass.
  This is pending design/implementation, not an implemented capability.

## Deterministic percentage relationships

- Implemented on `f9102587bb3ffe00c38c62b59026146e6a37da74`: percentage
  placeholders now represent complete statements. The compiler selects subject,
  denominator, sign and unit from the verified fact ID, not free-form prose.
  It refuses embedded percentage anchors and a ratio/price fact relabeled `%`.
  Exact generated statements have code-owned Vietnamese equivalents and are
  protected as entire statements during presentation. Generic pattern-based
  percentage interpretation was removed from the new compilation path.
- Material interpretation, opposing arguments, risks and invalidations remain
  model-authored, source-linked and subject to review. The change does not
  shorten the original graph, rewrite historical reports, guarantee qualitative
  entailment or override any portfolio policy.
- PASS: full local regression at this candidate: 1,420 tests + 88 subtests,
  20 classified skips, 42.85 seconds; Ruff passed. Tests include all percentage
  IDs in the current catalog, reciprocal subject/baseline distinctions, custom
  history/window calculation labels, unit-bypass rejection and deterministic
  EN/VI presentation without model translation of the relationship.
- Live component acceptance remains UNVERIFIED pending the bounded financial
  review/presentation replay. This does not replace full BTC/AAPL/NQ, browser or
  PostgreSQL acceptance.
- Follow-up result: the replay started on `f910258` successfully converted the
  retained draft to standalone percentage statements and bilingual presentation
  after one bounded financial format repair. Usage: 56,564 tokens (20,327 input
  + 36,237 output), three calls. QA blob:
  `sha256/7d/58/7d588e7f4a1b76a1d889fbe223ca94528d816b8667ba369c76152bcb9578aab9`.
  Manual check: generated percentage sentences keep their intended denominator
  and their deterministic Vietnamese counterparts. The report remains complete
  with opposing case, coverage limitations, risks and invalidations. Snapshot
  replay also confirms the stated rising moving averages at both one- and
  five-observation comparisons and the mixed recent close sequence.
  **Editorial acceptance remains FAIL**: surrounding Vietnamese prose is still
  overly literal and some terms are awkward. Adjacent qualitative interpretation
  still requires human review; this is not full report or product acceptance.
- PASS: `c42372e` extends labels for verified derived-percentage operands without
  restricting the existing calculation grammar. Full local regression: 1,422
  tests + 88 subtests, 20 classified skips, 42.93 seconds; Ruff passed. This later
  change was not separately live-replayed; live evidence above belongs to the
  loaded `f910258` candidate. No new whole-graph run was opened this continuation.

## Block-addressed Vietnamese editing

- `865ccc28435d1829624edd38d296f542ab374810` makes translation paragraph/item
  addressed. Source-owned headings and order are restored by code; missing,
  duplicate, unknown, empty or heading-injected blocks fail closed. Anchors
  cannot move between blocks. Known literal calques use the existing single
  repair budget rather than an additional editing agent or graph shortcut.
- PASS: full local regression, 1,437 tests + 88 subtests, 20 classified skips,
  41.10 seconds; Ruff passed. Mocked frontend ArtifactPreview: 9 tests PASS,
  2.39 seconds. These are component tests, not browser-rendered acceptance.
- Live translation-only replay from the previously accepted canonical research
  retained that canonical object unchanged outside localization and passed block
  and numerical checks after one format repair. Usage: 62,463 tokens (10,089
  input + 52,374 output), two calls. QA blob:
  `sha256/8f/71/8f711fc14bde3944615a279ff863445c2d1ea174c09b1bbec754ac657f4a5e1c`.
  **Manual translation acceptance remains FAIL**: RSI's neutral midline was
  rendered as a moving average in a paragraph containing no moving average;
  literal expressions such as “việc khung nó” remained. A subsequent regression
  guard covers this specific RSI concept substitution and the reproduced
  editorial cases. No assertion of universal translation fidelity is made.
- Browser revalidation: the old QA tab was absent; existing owner tab 27 was
  found at `http://127.0.0.1:8000/#/markets`. Access was again denied because the
  admin-enforced browser policy could not be verified. No alternate browser,
  indirect UI access or security bypass was attempted. Page content, screenshot,
  console health and interactions remain UNVERIFIED for this candidate.
- No new whole-graph paid run, database restart, NQ substitution, provider/model
  change, historical rewrite, merge or deployment occurred in this continuation.
