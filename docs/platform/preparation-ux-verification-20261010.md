# R11 — supplementary preparation disclosure, 2026-10-10

## Candidate and scope

- Worktree: `/Volumes/Data/codex/worktrees/ta-030-analysis-risk/TradingAgents`.
- Branch: `fix/TA-R01-research-quality`.
- Verified clean source: `877143168057237da3552f42944111c77c4bf2b6`.
- Parent: `a4374808316bca36a4ce227a700d02e42919a763`.
- Local macOS arm64; Node26.8.1, npm11.19.0, Vitest5.0.2.
- Scope: existing RunForm presentation, CSS, EN/VI application copy and tests.
  Python, graph/CLI, provider/model, source eligibility, risk, consent payload,
  owner history and publication code are unchanged.

The current preparation screen expanded every supplemental source before the
coverage and next action. A native `details`/`summary` now groups these controls
under Broaden research coverage / Bổ sung phạm vi nghiên cứu. All original
StockTwits, Reddit, Yahoo headlines, FRED and eligible SEC controls and disclosures
remain mounted. There is no source acquisition, automatic selection or AI call
when opening/closing the disclosure. Missing-area coverage stays outside it.
Native disclosure avoids new React synchronization state/effects; no dependency
or custom keyboard implementation was added.

## Local verification

Commands ran from `web`, with cleared inherited environment, explicit system/
Homebrew PATH and external managed TMPDIR/npm cache. No env file was loaded.

| Gate at clean source | Result | Evidence |
| --- | --- | --- |
| `npm run build` | PASS | session54718 terminal0, TypeScript and Vite299 modules |
| `npm run lint` | PASS | session66786 terminal0 |
| `npm test` | PASS | session61204 terminal0,227 tests/29 files,19.57s |
| Backend/CLI source parity with parent | PASS | `git diff --exit-code a437480 HEAD -- tradingagents tests scripts pyproject.toml uv.lock` |

New EN/VI DOM tests check closed native structure, preserved coverage/next action,
all applicable controls after expansion and no acquisition/submission on toggle.
The consent test also exercises data/review navigation and source disclosure
without granting or losing unchanged consent; changed inputs still reset it.
Existing preparation tests explicitly open the real disclosure before interacting
with supplementary controls, rather than querying hidden panels to skip UX.

Dirty diagnostic7469 originally had26PASS/2FAIL: jsdom role queries returned
descendants inside closed native details. The assertion was corrected to verify
the native DOM contract, not pretend jsdom proves browser visibility. Dirty
35779 then227PASS; neither replaces the clean receipt above. The original
authorization/source/failure tests remain present and pass.

## Rendered QA

In-app browser, isolated localhost8000 synthetic fixture only. The original
`scripts.web_fixture --synthetic-local-only --fixture-worker --graph-result
bilingual --built-web --all-assets --screening` ran in an env-cleared Python3.13.16
environment. Its model/vendor replacements are explicitly synthetic; this is NOT
original LangGraph or live financial/provider/translation acceptance. The current
production frontend build was used; no response interception or runtime patch.

- PASS: actual scope/data/review navigation, EN/VI labels, missing coverage visible
  with supplementary controls collapsed, original controls visible after opening.
- PASS: Enter opens, Space closes. Tab from a closed summary advances to Advanced
  data settings; from an open summary it advances to Add StockTwits discussions.
- PASS: choosing a saved synthetic price retains it in review and on returning to
  data. Queue analysis remains disabled without literal consent.
- PASS: mobile390x844 EN/VI and desktop observations; mobile document scrollWidth390.
- PASS: no warn/error entries from the QA tab's browser console at closeout.
- No new analysis submission/acquisition/approval in this continuation. Synthetic
  SQLite still has exactly one succeeded job from the earlier QA journey.
- Full-screen-reader, zoom, WCAG, long native process, cancellation/race and actual
  provider acceptance are UNVERIFIED by this check.

Screenshots were saved outside Git below the existing owned managed run's
`ux-journey-GzXTTb` directory and each accepted image was visually inspected:
`data-disclosure-desktop-vi.jpg`, `data-disclosure-mobile-vi.jpg`,
`data-disclosure-mobile-en.jpg`, `data-disclosure-desktop-en-native.png`.
The VI desktop full-page capture was at the default1280x720 viewport; mobile
captures are390px wide. EN desktop DOM was also checked at1440x900. The generic
tab screenshot after resizing produced a malformed/blank desktop capture;
`data-disclosure-desktop-en.jpg` is not accepted as evidence. Native observation produced
the accepted EN desktop image after resetting to default1280x720. This limitation
is not hidden or treated as proof of a layout regression/pass at1440x900.

The temporary viewport override was reset and the task-created QA tab closed.
Owned fixturePID49930 was checked by exact command then terminated: session53707
terminal143 with normal Uvicorn application shutdown; PID/listener8000 absence
independently confirmed. No unrelated runtime was stopped and no artifact deleted.

## Remaining R11 and whole-goal gates

This improves one preparation interaction; it does NOT complete R11. The mobile
data page is still long, report masthead/financial summary and decision readiness
hierarchy still need work, and actual complete live operational UX remains
UNVERIFIED. Preserve the prior live financial/VI FAIL and broader semantic/native
recovery/operator gates. NQ stays owner-BLOCKED without eligible roll metadata.
Separate owner API8001/worker restart approval is pending; neither approved paid
BTC/AAPL acceptance run has been submitted. Full R01–R14 goal remains ACTIVE.
