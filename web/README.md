# Local web (M4 implementation in progress)

This checkpoint implements the React shell and session boundary only. Markets,
analysis, portfolio and decisions are not connected yet; the signed-in screen
explicitly labels that limitation. Do not use this checkpoint for investment
decisions or describe it as the completed M4 product.

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
- First IAB smoke: login renders at 1280×720, no framework overlay, retry returns
  to the visible unavailable-API state. No app warning/error captured by the
  browser log API. Authenticated and narrow-viewport browser checks remain
  UNVERIFIED at this checkpoint.
