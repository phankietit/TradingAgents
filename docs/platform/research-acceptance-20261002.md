# R01–R14 continuation · 2026-10-02

## R08 working-note reader

Source candidate: `1a01f21455fa351017319ad6283bb8307defe0ee`, clean at browser
refresh, branch `fix/TA-R01-research-quality`. Private-platform candidate only;
overall acceptance remains **FAIL** and PR #7 remains Draft.

The web separates `research_stage` artifacts into a collapsed working-note
collection, apart from final reports/evidence. Contents load only on explicit
inspection. The reader validates schema/run/role/section/attempt/sequence and
nonapproval markers; malformed contents are withheld. Original Markdown remains
untrusted and is never executed as HTML. Mandatory EN/VI application copy states
that these are unvalidated drafts, not completed decisions. Changing interface
language neither translates original stage text nor calls a model. Large notes
remain bounded by the existing one-million-byte preview limit.

| Gate | Result | Evidence |
| --- | --- | --- |
| Web regression | PASS | 134 tests/22 files, `npm test`, 5.50 s; Node 26.8.1/npm 11.19.0 |
| Type/lint/build | PASS | `npm run typecheck`, `npm run lint`, `npm run build`; Vite 8.3.1 |
| Ruff/diff/templates | PASS | `.venv/bin/ruff check .`, `git diff --check`, Ruby YAML issue-template parse |
| Browser page identity/nonblank/overlay | PASS | Built app title `TradingAgents · Local research`; `http://127.0.0.1:5190/#/analysis?run=qa`; real reader contents visible, no framework overlay |
| Browser interaction/console/layout | PASS | 1280×900 and 390×900; open notes → inspect → switch VI; zero console/page errors, no horizontal overflow, exactly one note GET, zero mutation requests |
| Untrusted text and quantities | PASS | Synthetic `-22.94%` preserved; literal image markup displayed as text with no image execution; no linked decision in note reader |
| New backend full regression | UNVERIFIED | Backend unchanged; prior 1,600 + 88 subtests at ecbb7d3 retained, not relabeled as a new execution |
| Real source/API/model report | UNVERIFIED | Browser API fixtures are explicitly synthetic, not a live provider/worker acceptance |
| Runtime allowance/graph resume | UNVERIFIED | Not implemented in this reader slice; no role skips or budget increases |
| NQ=F live | BLOCKED | Owner retains valid contract/roll-source hold; no provider substitution |

Browser plugin/skill is not available in this session, so bundled Playwright was
used with the built Vite preview. The first isolated development component
harness failed because its React import was wrong and its dev HMR websocket was
blocked; it does not count as passing evidence. Verification instead exercised
the actual built app with mocked owner/run/job/artifact endpoints. An initial
mobile locator included hidden label text; the corrected accessible-name
locator and repeat on the committed candidate passed both viewports.

Private screenshots/scripts: `/Volumes/Data/TradingAgents-runtime/qa-stage-reader-aMBEwV/`.
They contain synthetic fixtures only and are not committed. No new dependency,
provider, CI, risk policy, broker, public deployment or historical mutation.
The task's local preview is stopped after verification.

Next: explicit execution allowance and request-timeout behavior, then full
owner/run/source/model/prompt/config-bound, lease-fenced graph recovery. The
original failed BTC has no notes to reconstruct. Further BTC paid permission
remains pending; AAPL remains previously approved but not rerun on this source;
semantic financial/translation and remaining ingestion acceptance are open.

## R08 execution uncertainty and model-free finalization

Candidate: `93e797576b9179e088f6ff809761bddd34cc3df6`, unchanged runtime source
through final regression. Only follow-up documentation was dirty. This follows `9fdbdb0`, whose full regression found
one existing recovery regression and is **FAIL**, not an accepted checkpoint.

The handler persists `research.execution_started` before graph construction;
new event storage is additive on the existing string event column, with no
historical rewrite or schema migration. Engine/publication exceptions are typed
without raw provider messages. Queue failure/expired-lease recovery recognizes
owner/run-bound execution evidence and stops blind full-run replay; legacy
stage-start/model-usage evidence is also honored. Unknown provider billing is
not described as zero cost. Cancellation and old-worker fences remain intact.

The earlier implementation blocked an existing legitimate storage-only recovery:
a report/decision pair had committed, but queue completion failed. This was
reproduced by the full regression, not waived by changing the expected result.
The corrected candidate preserves that idempotent retry. The handler reads and
checks the saved pair before engine entry; incomplete/corrupt outputs cannot
cause new model work. An additional test simulates outputs becoming unavailable
after retry was scheduled and proves the engine call count remains one.

Focused command: `.venv/bin/python -m pytest -q tests/test_analysis_job_handler.py
tests/test_research_stage_records.py tests/test_durable_jobs.py tests/test_run_events.py
--disable-warnings`: **PASS**, 55 tests, 2 PostgreSQL skips, 5.59 s. Ruff **PASS**.
This includes max-attempts=3 with an engine error, lease expiration/post-handler
failure for new/legacy execution events, ordinary pre-engine retry, saved working
notes, cancellation/lease isolation, and committed-output finalization with no
second model call. All are local/fake-model/SQLite evidence.

No execution allowance, SDK timeout/retry policy, provider/model, original graph
role, source input, risk policy or CLI behavior is changed. No new live request,
private-history deletion or public deployment. Actual request deadline/allowance,
fingerprinted graph resume, remaining ingestion, finance/VI semantics and live
BTC/AAPL acceptance remain unfinished. NQ=F remains owner-BLOCKED.

Full Python regression on this candidate: **PASS**, 1,608 tests + 88 subtests,
20 skips, 22 warnings, 50.14 s, Python 3.14.7. `.venv/bin/ruff check .`,
`git diff --check`, and Ruby issue-template YAML parsing **PASS**. Skipped gates
remain **UNVERIFIED**: 18 PostgreSQL cases (`TEST_POSTGRES_URL` absent), optional
Bedrock (`langchain_aws` absent) and live DeepSeek (key absent). No candidate
release or qualitative live acceptance is inferred from these checks.

Web refresh on the same runtime source: **PASS**, `npm run typecheck`,
`npm run lint`, `npm test` (134 tests/22 files, 6.60 s), `npm run build`;
Node 26.8.1/npm 11.19.0. No rendered UI source changed in this backend slice;
the earlier 1a01f21 browser proof is retained with its original synthetic scope,
not relabeled as new live/browser acceptance.

## R08 explicit snapshot-run allowance contract

Source: `648fa183ee90eed1e353b3e06cbcc2c249aebb82`, clean through regression.
API requests may opt into strict immutable `execution_limits` (`wall_seconds`
60–7200, `model_calls` 1–128). Defaults remain 1800/128. Explicit selection
requires snapshot inputs and binds to run manifest/config hash/job payload;
the worker verifies payload identity and uses the selected observer allowance.
Legacy omission stays `None` and preserves the original job payload/hash, with
no historical rewrite. Authenticated configuration disclosure now includes
defaults and `deadline_mode=cooperative_boundaries`; no vendor probe or key leak.

| Gate | Result | Exact source evidence |
| --- | --- | --- |
| Focused contract/API/worker | PASS | 44 tests, 5.12 s: strict ranges/types, idempotent reuse, changed allowance conflict/hash, immutable repository inputs, no legacy rewrite, real worker/handler observer and saved report limits |
| Full Python | PASS | `.venv/bin/python -m pytest -q --disable-warnings`: 1,619 tests + 88 subtests, 20 skips, 22 warnings, 59.09 s; Python 3.14.7 |
| Ruff/diff | PASS | `.venv/bin/ruff check .`, `git diff --check` |
| Web regression/type/lint/build | PASS | 134 tests/22 files, 6.57 s, `npm run typecheck`, `npm run lint`, `npm test`, `npm run build`; Node 26.8.1/npm 11.19.0 |
| PostgreSQL/optional providers | UNVERIFIED | Same 18 PostgreSQL, missing optional Bedrock dependency and live DeepSeek key skips |
| UI allowance / request deadline / graph resume | UNVERIFIED | Not implemented by this API binding slice; SDK timeout/retry unchanged and in-flight requests can still overrun |
| Live finance/translation | UNVERIFIED | No new paid/vendor call; earlier manual failures stay unresolved |
| NQ=F | BLOCKED | Owner retains contract/roll-source hold; no new provider |

Explicit 3600-second fixture selection is local proof, not approval to spend on
a live 60-minute BTC run. That separate permission remains pending. All graph
roles, source/risk/approval gates and CLI defaults are preserved. Goal remains
active and Draft PR #7 is not eligible for release/merge approval.

## R08 web allowance selection and consent

Source `a2a0b6f6db38bc08102af853da889f874515a2a6`, branch
`fix/TA-R01-research-quality`. The new form offers 1800/3600 seconds with the
unchanged 128-call cap. A changed selection invalidates paid-call consent and
changes request identity. Processing displays recorded limits; legacy records
without them are explicitly labeled, not silently assigned values. EN/VI copy
discloses cooperative checking, possible in-flight overrun and no cost cap.

| Gate | Result | Evidence |
| --- | --- | --- |
| Web regression/type/lint/build | PASS | 137 tests/23 files, 4.98 s; `npm run typecheck && npm run lint && npm test && npm run build`; Node 26.8.1/npm 11.19.0 |
| Consent/request identity | PASS | Mocked failure/retry proves 1800 default, 3600 selection, renewed consent and distinct keys; unchanged-payload retry tests retained |
| Recorded/legacy display | PASS | Analysis tests assert saved 60 minutes and explicit missing-limit copy for old runs |
| Built browser | PASS | Playwright at `http://127.0.0.1:5192/#/analysis?instrument=aapl`, 1280×900 and 390×900; exact title, meaningful first viewport, no framework overlay, zero console errors/warnings/page errors and horizontal overflow |
| Interaction | PASS | Select synthetic source → authorize → change to 60 minutes → consent cleared/submission disabled → switch VI/EN → reauthorize → one intercepted run POST per viewport → saved allowance shown. Source unchanged, wall_seconds=3600, model_calls=128 |
| Diff/templates | PASS | `git diff --check`; Ruby YAML load of issue templates |
| Full Python refresh | NOT_IN_SCOPE | Frontend/docs-only source; no Python behavior changed. Earlier 648fa183 receipt remains checkout-specific, not a fresh full-suite run |
| Live report/request deadline/resume | UNVERIFIED | No actual worker/provider/model called. SDK timeout/retry unchanged, no hard interrupt or graph resume implemented |

Browser plugin not available; bundled Playwright used without installing
dependencies. Private QA script/screenshots are outside Git at
`/Volumes/Data/TradingAgents-runtime/qa-allowance-2RpR1B/`. Both initial and
selected-allowance desktop/mobile screenshots were visually inspected. The
first harness attempt failed on an incorrect disclosure-text locator; corrected
to the actual UI label and rerun successfully on the clean source SHA. This was
not waived or labeled a product/provider pass.

No paid retry, new provider, derivative execution, risk-limit change, history
rewrite, CI or public deployment. NQ=F remains owner-BLOCKED. Existing live
financial/translation failures remain unresolved; goal and Draft PR #7 stay open.
