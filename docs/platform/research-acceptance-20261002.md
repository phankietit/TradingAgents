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
