# Private Platform API

The platform now exposes a versioned FastAPI contract under `/api/v1`. It is an
API foundation for the local Web UI. UI serving is explicitly opt-in and adds
no broker or order endpoints.

## Runtime

Install `pip install ".[platform]"`, apply the packaged Alembic migrations, and
bootstrap the owner through an operator-controlled Python session. The API
requires these explicit environment names:

- `TRADINGAGENTS_DATABASE_URL`
- `TRADINGAGENTS_ARTIFACT_ROOT`
- `TRADINGAGENTS_ALLOWED_ORIGIN`
- `TRADINGAGENTS_SECURE_COOKIES` (`true` by default)
- `TRADINGAGENTS_API_PORT` (`8000` by default)
- `TRADINGAGENTS_WEB_ROOT` (optional absolute path to the built `web/dist`)

Run `tradingagents-api`. The bundled entrypoint binds only to `127.0.0.1`.
Reverse proxy, TLS, public network exposure, rate limits, and deployment are
separate release decisions. Database migrations and owner bootstrap never run
implicitly during API startup.

### Built local UI (M4)

With `TRADINGAGENTS_WEB_ROOT` set, the same process serves `/`, `/index.html`
and allowlisted built files under `/assets/`. The browser uses hash navigation,
so there is no SPA catch-all; unknown API routes and missing assets stay 404.
Build first using `cd web && npm ci && npm run build`. Missing index/assets
causes startup to fail rather than quietly serve a blank app.

This mode requires `TRADINGAGENTS_ALLOWED_ORIGIN=http://127.0.0.1:<port>`,
`TRADINGAGENTS_SECURE_COOKIES=false` for loopback HTTP only, and the same port in
`TRADINGAGENTS_API_PORT`. The bundled entrypoint always binds `127.0.0.1`.
Requests with another Host are rejected to resist DNS rebinding. Existing
session, owner, Origin and CSRF enforcement is unchanged. The shell is public
static code; private data still comes exclusively from authenticated API routes.

Only index and built asset files are served, never the repository, artifact
root, source maps, dotfiles or source files. StaticFiles confines asset paths
and rejects symlinks escaping the asset directory. Built UI responses use CSP
with self-only scripts/styles/connections, no inline scripts/eval, no framing
or object embeds, and restrictive browser permissions. All responses remain
`no-store`. API-only mode is unchanged when WEB_ROOT is absent. This is not
approval for public hosting, TLS termination or a production deployment.

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

Time-series comparisons now include nullable `benchmark_snapshot` provenance
beside `snapshot` and `view`; absent when no benchmark was requested. The
benchmark uses the same owner-readable artifact checks, cutoff and requested
window as the asset. It is not fetched from a provider on demand. Missing
snapshots remain 404; invalid dates, incompatible interval/currency or insufficient
alignment remain 422. Both asset and benchmark metadata describe saved snapshots,
not a current live-feed freshness guarantee.

## Workspace discovery (M4)

Watchlist: `GET /api/v1/watchlist` returns owner-saved instrument contracts,
alphabetically ordered, with the same bounded `limit`/`offset` pagination below.
`PUT /api/v1/watchlist/{instrument_id}` saves an existing instrument and
`DELETE /api/v1/watchlist/{instrument_id}` removes only that owner's bookmark.
Both are idempotent, session/CSRF/Origin protected and serialized with the owner
lock. Watching an index reference does not make it investable. No portfolio,
decision, evidence or instrument history is deleted. Apply migration
`0010_owner_watchlist` before using these routes. Downgrade drops bookmarks;
test rollback only on a disposable database, never on owner data without approval.

Authenticated read-only routes:

- `GET /api/v1/instruments/{instrument_id}/analysis-profile` returns the existing
  deterministic asset profile, allowed analysts intersected with server settings,
  and investability. UI choices do not override this backend contract.

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

Snapshot discovery also returns `supported_analysts`. Dataset-to-role mapping is
explicit: `daily_prices`, `price`, supported `ohlcv.*` intervals and
`futures.reference` map to market; `news`, `fundamentals`, `social` and `sentiment`
map to their corresponding role. Unknown/bundle datasets are withheld from
analysis until a reviewed mapping exists. Both UI and snapshot-run validation
enforce this boundary; a price source cannot stand in for news or fundamentals.

Optional risk inputs bind an owner portfolio snapshot at the exact analysis
timestamp, an existing policy effective at that timestamp for the instrument's
asset class, and an explicit owner target weight. Reference-only instruments
cannot submit a portfolio risk proposal. Missing correlation coverage remains a
blocking REVIEW from the risk engine, never a default passing correlation.

List endpoints above use `limit` 1–200 (default 50), `offset` 0–100000 (default 0)
and deterministic descending time/ID order. Portfolio/policy history is not
silently filtered to a current version; run validation determines temporal
eligibility. Cross-owner and missing detail IDs both return 404. All data remains
non-cacheable. These routes do not fetch vendors, trigger LLMs or mutate history.

## Research configuration disclosure

`GET /api/v1/analysis-configuration` requires an owner session and returns only
the configured provider, quick/deep model names, maximum job attempts and explicit
`UNVERIFIED` worker/provider states. Responses are non-cacheable. It does not
inspect credentials, connect to providers, start work or report service health.
The API cannot attest a separate worker's credentials or liveness. These settings
describe new runs; existing run manifests retain their own recorded configuration.
No environment values, database URLs, artifact paths or provider endpoints are
included. This is configuration disclosure, not a readiness probe or cost quote.

## Saved stock screenings

- `GET /api/v1/screenings` lists owner-scoped screening artifact metadata with
  the same bounded `limit`/`offset` contract. Future-created artifacts are omitted;
  private storage paths and owner identifiers are not returned.
- `GET /api/v1/screenings/{screening_id}` loads the saved deterministic universe
  through the existing screener service. Artifact bytes, schema, identity and
  universe hash are verified. Missing/cross-owner IDs return 404; invalid or
  future-dated results return 409 without exposing raw payloads.

Neither endpoint reranks candidates, refreshes vendors, changes policy or starts
analysis. Input hashes and source snapshot IDs support audit; successful loading
does not independently revalidate original facts or prove current eligibility.
Operator generation/persistence remains the workflow in
`deterministic-stock-screener.md`. A new analysis validates its own bound sources.

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
