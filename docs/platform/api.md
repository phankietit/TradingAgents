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
- `GET /api/v1/instruments`
- `POST /api/v1/runs`, `GET /api/v1/runs`, `GET /api/v1/runs/{run_id}`
- `POST /api/v1/runs/{run_id}/cancel`
- `GET /api/v1/jobs/{job_id}`
- `GET /api/v1/decisions`, `GET /api/v1/decisions/{decision_id}`
- `GET /api/v1/artifacts/{artifact_id}`

Creating a run requires `Idempotency-Key`, a same-origin request, and a session
bound `X-CSRF-Token`. The API derives owner identity only from the authenticated
session. It rejects future analysis dates and unsupported/duplicate analyst
sets before enqueueing a durable job.

## Browser Security

The session cookie is HTTP-only, Secure by default, and SameSite Strict. A
separate readable CSRF cookie must match the header and its server-side digest.
Unsafe methods also require the exact configured Origin. Responses use
`no-store`, `nosniff`, frame denial, and no-referrer headers. Validation errors
omit rejected input values so passwords are not echoed.

Artifacts are owner-scoped, integrity-checked, and returned as forced binary
attachments. OpenAPI describes cookie authentication and request schemas; no
request body or route accepts caller-selected `owner_id`.
