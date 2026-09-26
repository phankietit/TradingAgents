# Private Platform API

The platform now exposes a versioned FastAPI contract under `/api/v1`. It is an
API foundation for the planned Web UI; it is not itself a Web UI and does not
add broker or order endpoints.

## Runtime

Install `pip install ".[platform]"`, apply the packaged Alembic migrations, and
bootstrap the owner through an operator-controlled Python session. The API
requires these explicit environment names:

- `TRADINGAGENTS_DATABASE_URL`
- `TRADINGAGENTS_ARTIFACT_ROOT`
- `TRADINGAGENTS_ALLOWED_ORIGIN`
- `TRADINGAGENTS_SECURE_COOKIES` (`true` by default)
- `TRADINGAGENTS_API_PORT` (`8000` by default)

Run `tradingagents-api`. The bundled entrypoint binds only to `127.0.0.1`.
Reverse proxy, TLS, public network exposure, rate limits, and deployment are
separate release decisions. Database migrations and owner bootstrap never run
implicitly during API startup.

## HTTP Contract

- `GET /health/live`, `GET /health/ready`
- `POST /api/v1/auth/login`, `POST /api/v1/auth/logout`, `GET /api/v1/auth/me`
- `GET /api/v1/instruments` (asset-class, tradability, and venue filters)
- `GET /api/v1/instruments/resolve` (namespaced alias resolution)
- `GET /api/v1/instruments/{instrument_id}` (identity and aliases)
- `GET /api/v1/instruments/{instrument_id}/timeseries` (immutable normalized
  OHLCV, deterministic metrics, and optional benchmark comparison)
- `POST /api/v1/runs`, `GET /api/v1/runs`, `GET /api/v1/runs/{run_id}`
- `POST /api/v1/runs/{run_id}/cancel`
- `GET /api/v1/runs/{run_id}/events` (resumable SSE)
- `GET /api/v1/jobs/{job_id}`
- `GET /api/v1/decisions`, `GET /api/v1/decisions/{decision_id}`
- `GET /api/v1/artifacts/{artifact_id}`
- `GET /api/v1/observability/metrics` (authenticated Prometheus text)

Creating a run requires `Idempotency-Key`, a same-origin request, and a session
bound `X-CSRF-Token`. The API derives owner identity only from the authenticated
session. It rejects future analysis dates and unsupported/duplicate analyst
sets before enqueueing a durable job.

## Workspace discovery (M4)

Authenticated read-only routes:

- `GET /api/v1/portfolios` and `/portfolios/{portfolio_id}` return persisted
  owner snapshots, not frontend-recomputed balances.
- `GET /api/v1/policies` (optional `asset_class`) and
  `/policies/{policy_id}/{policy_version}` expose existing owner policy versions;
  these endpoints cannot edit policy or waive risk checks.
- `GET /api/v1/runs/{run_id}/artifacts` returns download metadata with artifact
  identity, kind, content hash, byte size and timestamps. It omits storage keys
  and checks run ownership before listing. Bytes still use the existing
  integrity-checked attachment endpoint.
- `GET /api/v1/instruments/{instrument_id}/snapshots` requires timezone-aware
  `analysis_as_of` (not future) and explicit `max_age_seconds` (0–315360000).
  Only manifests with an owner-readable matching payload artifact are listed.
  Each response includes `metadata_eligible`, `ineligibility_reasons` and
  `content_validation=required_on_run_creation`. This is not a claim that bytes
  have been loaded or hashes verified. Run creation still performs full content,
  freshness, analyst-role and policy validation. Ineligible snapshots stay visibly
  labelled instead of becoming an apparently valid fallback.

List endpoints above use `limit` 1–200 (default 50), `offset` 0–100000 (default 0)
and deterministic descending time/ID order. Portfolio/policy history is not
silently filtered to a current version; run validation determines temporal
eligibility. Cross-owner and missing detail IDs both return 404. All data remains
non-cacheable. These routes do not fetch vendors, trigger LLMs or mutate history.

## Browser Security

The session cookie is HTTP-only, Secure by default, and SameSite Strict. A
separate readable CSRF cookie must match the header and its server-side digest.
Both cookies remain scoped to `/api/v1`. A web client mounted at `/` fetches
`GET /api/v1/auth/csrf` with same-origin credentials after login or session
restoration, then keeps the returned `csrf_token` only in memory for mutation
headers. This authenticated, non-cacheable endpoint validates the existing
cookie against the session digest; it does not mint or rotate credentials.
Missing or forged CSRF cookies return 403; missing or expired sessions return
401. No cross-origin read access is enabled.
Unsafe methods also require the exact configured Origin. Responses use
`no-store`, `nosniff`, frame denial, and no-referrer headers. Validation errors
omit rejected input values so passwords are not echoed.

Artifacts are owner-scoped, integrity-checked, and returned as forced binary
attachments. OpenAPI describes cookie authentication and request schemas; no
request body or route accepts caller-selected `owner_id`.
