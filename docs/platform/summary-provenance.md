# R07 summary provenance — implementation design

Status: FAIL red regression; not implemented, not release acceptance.
`tests/test_summary_source_coverage.py` proves the current canonical summary can
assert an uncited external cause when unrelated news is available, even after
the claim-local thesis guard. See exact receipts in [HANDOFF](../../HANDOFF.md).
Do not fix this by deleting the summary, selecting every available source,
keyword-matching a guessed citation or expanding a vocabulary blacklist.

## Required change

Generated web research must bind summary statements to their actual immutable
snapshot references, as thesis/risk/invalidation blocks already do. The original
CLI `PortfolioDecision` remains unchanged. Introduce an explicit versioned web
report contract: new generation/review output uses the new version, while stored
legacy reports retain a separately readable original representation. The exact
schema names/fields require implementation review; this document does not claim
that new fields already exist.

The model supplies summary prose and citations. The deterministic compiler
projects prose and references losslessly into canonical text plus versioned
summary evidence; it must never infer support from the union of thesis citations,
model memory, related words or a source's mere availability. Retain full source
records and original opposing cases/uncertainty. Monetary/percentage placeholders
still resolve through the same verified quantities/application-owned statements.

Canonical validation must require exact summary/evidence parity and eligible
known snapshot IDs for the new contract. Missing, duplicate, foreign, unknown or
misbound support refuses publication, rather than fall back to the old format.
The existing financial review receives the complete actual cited records;
mechanical parity is not causal entailment. Known price-only attribution checks
must use summary citations just as material thesis citations. Mixed citations
still need financial/semantic review; source presence is not proof of causality.

Keep the original roles, debates, financial review, translation, deterministic
risk and human approval. Preserve one structured attempt/one repair; no model
loop, provider/model switch, new allowance or reduction of data. Invalid output
stays unvalidated/review-only. Model-generated confidence remains uncalibrated.
New fields can affect provider schema/repair frequency; measure locally, then
obtain explicit fresh live-run approval, not silently consume paid retries.

## Historical and reader boundary

Do not rewrite, backfill, automatically assign citations to or relabel stored
reports/checkpoints. Legacy reading must preserve exact bytes, original schema,
status and evidence; it does not certify summary entailment. New review output
may use the new contract only as a separately validated result retaining its
original rejected input, never an in-place repair of history. No fallback may
publish new incomplete output as a legacy success. Existing approval integrity,
policy and explicit owner gates remain authoritative.

Rendered EN/VI reports must preserve complete financial meaning and quantity
bindings. Summary source details should be readable financial provenance, not
raw UUIDs in prose; technical identifiers can remain in authenticated expanded
details. Saved-language switching creates no model job. Native fingerprint
changes must refuse incompatible old checkpoint restoration, never rewrite its
fingerprint or grant fresh allowance.

## Acceptance before integration

- Red uncited-summary cause withheld with price-only and mixed available sources.
- New sourced factual summary and explicitly unverified scenario remain eligible;
  unrelated source availability does not change cited-source support.
- Compiler preserves every summary statement/reference through quantity
  substitution; missing/unknown/misbound IDs and legacy-format output escape
  refuse, without invented citations or truncation.
- Legacy stored report reading preserves bytes/schema/history; new output cannot
  bypass validation by claiming the legacy version.
- Full original-role graph and bounded repair preserve trace, budgets and
  immutable rejected candidate. EN/VI representation keeps meaning/numbers.
- Authenticated API/artifact/browser source readback respects owner isolation and
  approval. No report reading, language switch or source expansion dispatches AI.
- Exact-source focused, native/integrated/full regression and separately approved
  live BTC/AAPL finance/editorial acceptance. NQ remains owner-BLOCKED.

All are requirements, not passed receipts. General semantic/translation quality,
operational restore and whole R01–R14 acceptance remain open.
