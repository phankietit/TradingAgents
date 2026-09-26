# Local web (M4 implementation in progress)

This checkpoint implements the React shell, session boundary and Markets with
real API instrument discovery, persisted watchlists, saved price chart/table,
backend metrics and source provenance. Analysis now supports snapshot selection,
explicit cost authorization, durable queue submission, SSE progress, cancellation,
new-attempt configuration and artifact downloads/inline inspection. Portfolio renders persisted
snapshots/cash/holdings/policies without recomputing portfolio math. Decisions
renders original/current state, narrative/evidence/risk checks and explicit
approve/reject dialogs. Worker-to-approval integration is verified locally with a
labelled synthetic graph; live-provider and broader acceptance remain pending.
Do not describe this checkpoint as the completed M4 product.

## Development

Verified with Node 26.8.1 and npm 11.19.0. Dependencies are locked; TypeScript
6.0.3 is used because the selected lint integration does not support TypeScript 7.

```sh
cd web
npm ci
npm run dev
```

Open `http://127.0.0.1:5173`. The server binds loopback with a strict port and
proxies `/api` to `http://127.0.0.1:8000`, preserving Origin. Set the API's
`TRADINGAGENTS_ALLOWED_ORIGIN=http://127.0.0.1:5173` and explicitly set
`TRADINGAGENTS_SECURE_COOKIES=false` only for this local HTTP workflow. Follow
the existing API runbook for migrations, owner bootstrap and API startup; do
not put backend/provider credentials in Vite environment variables.

```sh
npm run typecheck
npm run lint
npm test
npm run build
```

These commands run locally; no hosted CI. Do not publicly expose the development
server or use it as a production deployment.

## Run the built local web

After `npm run build`, use the existing `tradingagents-api` process with:

```sh
export TRADINGAGENTS_WEB_ROOT="/absolute/path/to/TradingAgents/web/dist"
export TRADINGAGENTS_ALLOWED_ORIGIN="http://127.0.0.1:8000"
export TRADINGAGENTS_API_PORT=8000
export TRADINGAGENTS_SECURE_COOKIES=false
tradingagents-api
```

Set the existing `TRADINGAGENTS_DATABASE_URL` and `TRADINGAGENTS_ARTIFACT_ROOT`
in that process environment first, using your approved local database/store.
The package initializer may load `.env` and `.env.enterprise` from the current
directory/parents without overriding exported variables; keep those files local
and ignored, and launch from the intended checkout. API startup does not migrate,
bootstrap an owner, seed data or start a worker. Follow [API setup](../docs/platform/api.md),
[owner bootstrap](../docs/platform/owner-authentication.md) and
[worker operation](../docs/platform/durable-jobs.md). Run `tradingagents-worker`
separately with the same database/store only after authorizing its model use.
Missing data/worker/credentials is not repaired with synthetic production data.

Open `http://127.0.0.1:8000`; no Vite process is needed. UI, API and SSE share
one origin. Do not use localhost aliases or another port: the configured Host
and Origin must match exactly. `secure_cookies=false` is for this loopback HTTP
mode only. Omit WEB_ROOT to retain API-only operation. The build is a separate
operator-generated artifact, not bundled into the Python wheel.

For **isolated synthetic QA only**, from repo root after building:

```sh
.venv/bin/python -m scripts.web_fixture --synthetic-local-only --fixture-worker --built-web
```

This creates a new ignored database/store and uses labelled synthetic graph
output; it does not load owner records or call models/vendors. Never point the
fixture script at an owner database. Stop with Ctrl-C; fixture data is retained
for inspection. This is not a populated investment product or live-data demo.

Built-mode QA: 1280×720 IAB login → saved AAPL → CSRF watchlist save → reload
and session restoration → logout PASS, no console/CSP errors or framework
overlay. Static/API gate: 43 tests PASS, including no API-to-HTML fallback,
path traversal/symlink/dotfile/source-map refusal, Host/Origin rejection,
same-origin session/CSRF and local bind/port checks. Narrow built-mode and full
cross-asset acceptance remain pending; earlier narrow checks used Vite.

## Security and verification boundary

- Private data is mounted only after `/auth/me` or login validates the owner.
- Mutations bootstrap the existing session-bound CSRF token; no credentials,
  reports or financial records are stored in browser local/session storage.
- A 401 unmounts private components; failed logout remains visible and retryable.
- Request errors use local safe messages, not unrestricted backend payloads.
- Component tests use explicitly synthetic responses. They are not live-provider
  or browser-to-backend integration evidence.
- IAB verification at 1280×720 and 390×844: real API login → AAPL saved snapshot
  → add watchlist → reload/session restoration → watchlist filter → price table
  → index reference with missing series → logout/private data unmount. No
  framework overlay or app warning/error captured. Narrow viewport has no
  document-level horizontal overflow; OHLCV table scrolls within its region.
- Reproduce isolated synthetic QA from the repository root with
  `.venv/bin/python -m scripts.web_fixture --synthetic-local-only`, then start
  Vite. Fixture credentials are documented in that script, not owner credentials.
  Each run creates a new ignored `.cache/web-fixture-*` database and artifacts.
  By default no worker starts. Add `--fixture-worker` to run the real durable job,
  evidence and risk pipeline with explicitly labelled synthetic graph output.
  Neither mode calls a vendor/model; the fixture graph has no live-tool fallback.
  Provider/model metadata is synthetic, not OpenAI. The synthetic vendor label
  is visible beside the chart. This is integration evidence, not live data.
- Analysis IAB check: Markets Analyze → choose market snapshot → explicit queue
  authorization → real queued run → cancel → SSE `run.cancelled`. No worker or
  model ran. Browser logs had no app errors. Generated report/risk/decision paths
  were UNVERIFIED at that checkpoint. Unit tests cover disabled stale inputs, required consent and
  stable idempotency keys after failed unchanged submissions.
- Portfolio/Decisions IAB: backend replay of synthetic deposit and historical
  holding gives NAV 10180.20 USD, cash 8200 USD, 10 AAPL units at 198.02 USD.
  Seeded REVIEW candidate cannot be approved; explicit reason/reject persists an
  audit event after reload. This is seeded local QA, not generated model output.
  Multi-asset browser risk integration remains UNVERIFIED.
- Analysis risk input check: choose a persisted portfolio and existing effective
  policy, enter an owner target, select market evidence, authorize and enqueue.
  API accepted the pinned timestamp/risk payload. Price sources are disabled for
  unrelated analysts. No worker/model ran in this browser check; policy fixture
  is explicitly synthetic and does not change owner limits.
- Worker fixture check (2026-09-27 local, 1280×720, IAB): login → AAPL market
  snapshot → synthetic portfolio/policy → owner target 0.2 → queue → worker
  succeeded → two integrity-checked artifact manifests → eight risk checks PASS
  → confirm approval with reason → reload → approved audit persists. Source run
  `26dc48fa-…`, decision `156eadfd-fa5a-5cfd-ad7f-fd4e33aaad54`. Original research
  state remains ready_for_approval while current state is approved; actions are
  disabled afterward. No order or paid model call occurs. Browser console clean,
  meaningful page/title and no framework overlay; screenshot inspected.
  A discovered stale history-row status was fixed with stable status propagation
  from the fetched run detail; a second queued run reached succeeded in both
  list and detail without manual refresh. Regression test checks no SSE reconnect.
  Local gates: 24 frontend tests, 6 snapshot-worker tests, lint/typecheck/build PASS.
- Report inspection checkpoint: a user-triggered preview reads the existing
  owner-authorized, integrity-checked artifact endpoint. Only analysis-report and
  decision-evidence JSON up to 1 MB is previewed; both manifest and streamed-byte
  bounds apply. Run identity, report shape and claim/source links are checked
  before rendering. Malformed, mismatched or integrity-failed data yields an
  explicit unavailable state, not a narrative fallback. HTML remains plain text;
  there is no HTML/Markdown injection, iframe, external asset fetch or browser
  persistence. Other formats/sizes retain explicit download only.
  Reports link to the exact decision, including older candidates outside the
  latest history page; missing/forbidden IDs do not silently select another row.
  Selection survives reload. Immutable research and current lifecycle are labelled
  separately; a successful run without risk inputs still cannot be approved.
  Built-mode IAB at 1280×720 and 390×844: synthetic worker publication → inspect
  narrative/structured output → claim/source/time/hash drilldown → correct linked
  REVIEW decision → reload PASS; Enter opens preview/disclosure, visible focus,
  no document overflow, console/CSP errors or framework overlay. 34 frontend
  tests plus lint/typecheck/build PASS. This remains offline fixture evidence.
