# Local web (M4 implementation in progress)

This checkpoint implements the React shell, session boundary and Markets with
real API instrument discovery, persisted watchlists, saved price chart/table,
backend metrics and source provenance. Analysis now supports snapshot selection,
explicit cost authorization, durable queue submission, SSE progress, cancellation,
new-attempt configuration and artifact downloads. Portfolio renders persisted
snapshots/cash/holdings/policies without recomputing portfolio math. Decisions
renders original/current state, narrative/evidence/risk checks and explicit
approve/reject dialogs. Full worker-to-approval integration and acceptance remain
pending. Do not describe this checkpoint as the completed M4 product.

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

These commands run locally; no hosted CI. `npm run build` emits static assets,
but a supported built-asset server remains pending. Do not publicly expose the
development server or use it as a production deployment.

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
  This server never starts a worker or calls a vendor/model. The synthetic vendor
  label is visible beside the chart. This is integration evidence, not live data.
- Analysis IAB check: Markets Analyze → choose market snapshot → explicit queue
  authorization → real queued run → cancel → SSE `run.cancelled`. No worker or
  model ran. Browser logs had no app errors. Generated report/risk/decision paths
  remain UNVERIFIED. Unit tests cover disabled stale inputs, required consent and
  stable idempotency keys after failed unchanged submissions.
- Portfolio/Decisions IAB: backend replay of synthetic deposit and historical
  holding gives NAV 10180.20 USD, cash 8200 USD, 10 AAPL units at 198.02 USD.
  Seeded REVIEW candidate cannot be approved; explicit reason/reject persists an
  audit event after reload. This is seeded local QA, not generated model output.
  Successful approval and multi-asset risk integration remain UNVERIFIED.
- Analysis risk input check: choose a persisted portfolio and existing effective
  policy, enter an owner target, select market evidence, authorize and enqueue.
  API accepted the pinned timestamp/risk payload. Price sources are disabled for
  unrelated analysts. No worker/model ran in this browser check; policy fixture
  is explicitly synthetic and does not change owner limits.
