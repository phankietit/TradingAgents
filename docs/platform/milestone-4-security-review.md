# M4 local/manual security review

Date: 2026-09-27. Review base: M3 `e45e079`; application candidate:
`cbb1bfe5ef1c742270ac0450d9ba64267f5e4713` on
`feature/TA-M4-local-web-ui`. This is the owner-approved manual evidence format,
not a sealed plugin report, penetration-test certification or public-release
approval. No earlier security report was changed.

## Scope and trust model

Scope is the M4 diff: authenticated browser UI, its API additions, watchlist
persistence/migration, snapshot-role validation, valuation receipts, local
static serving and synthetic QA tooling. Existing auth, artifact storage,
decision/risk and worker boundaries were followed where these changes call them.
Unrelated legacy CLI/provider code is not newly certified by this review.

Protected assets are owner sessions, private portfolios, research/approval
history, source artifacts and server provider credentials. Untrusted inputs
include another website targeting loopback, unauthenticated requests, forged
resource IDs, URL/hash navigation, source/model text and malformed artifact
responses. The operator, local OS, installed dependencies and generated static
build are trusted; a compromised local OS or malicious build is not contained
by browser CSRF. Public hosting remains outside scope.

## Source review and evidence

| Boundary | Reviewed implementation | Evidence and conclusion |
| --- | --- | --- |
| Session and CSRF | API dependencies/login/logout/CSRF bootstrap; `web/src/api.ts`, `auth.tsx`, `App.tsx` | Session is HttpOnly, SameSite Strict and API-scoped. CSRF bootstrap authenticates and validates the existing token; mutations use exact Origin plus session-bound CSRF. Browser requests reject redirects, use same-origin credentials and no-store; tokens/reports are not saved in browser storage. PASS for local boundary. |
| Resource ownership | New routes in `api/app.py`; repository list/get paths and schema allowlists | Owner derives from session, not caller payload. Portfolio/policy/run artifacts/screenings/jobs filter owner; snapshot discovery requires a matching owner-readable artifact. Missing and foreign resources fail closed. Storage keys/lease payloads are not exposed by the new discovery responses. PASS. |
| Static file serving | `api/web.py`, runtime/settings, Vite/index/config | Loopback bind and exact built-web Host/port; CSP self-only with no eval/inline scripts, framing/object denial; no SPA fallback for API errors. Only index and allowed asset suffixes; hidden files/source maps/path traversal and escaping symlinks rejected. No third-party UI scripts/fonts/analytics added. PASS. |
| Untrusted research | `ArtifactPreview`, `Decisions`, `StockScreener`, `ValuationSources`, `Markets` and display validators | React text rendering, no HTML injection sink; external evidence links allow HTTP(S) without credentials and use noopener/noreferrer. Artifact preview is on demand, bounded to 1 MB even without Content-Length, and checks run/graph/claim identity. Malformed data is withheld or contained by `ViewBoundary`; raw caught render exceptions are not logged. PASS for reviewed sinks. |
| Research actions | `RunForm`, `Analysis`, `JobProgress`, decision confirmation | Explicit cost authorization, stable idempotency keys for unchanged inputs, exact prior lifecycle state, mandatory review reason. Matching decision/run/instrument/time required before UI approval. Backend still revalidates all policy/evidence/run requirements; client controls confer no authority. PASS. |
| Financial integrity | Snapshot dataset-role mapping; portfolio receipt service; `Portfolio`, decimal/portfolio validators | Unsupported analyst datasets rejected; source clocks/quality/age validated. Receipt binds portfolio hash and quotes, verifies artifact integrity, and does not backfill old history. UI displays persisted values rather than computing portfolio allocation or risk limits. PASS. |
| Synthetic tooling | `scripts/web_fixture.py`, test modes | New isolated DB per invocation, explicit synthetic flag, labelled sources/policies; synthetic graphs have no live fallback. TTL obeys existing minimum. No owner DB parameter or public bind. PASS. |

All new/changed runtime Python modules in this scope and frontend application
modules were read; build/config/environment-ignore changes were inspected.
Relevant tests were inspected to confirm denial/integrity assertions, not merely
their names. Documentation/tests/lockfiles were used as supporting evidence,
not treated as production request handlers. CSS was checked for external-resource
references; visual accessibility acceptance remains a separate gate.

## Findings and remediation

- No newly confirmed exploitable security finding remained in the reviewed M4
  boundaries at this candidate. This is a bounded review result, not a claim
  that the repository has no vulnerabilities.
- Defense-in-depth issue found earlier during M4: decision detail accepted a
  response for a different selected identity, and approval UI did not verify
  the associated run identity. Fixed in `08a1fb3`; tests cover wrong decision,
  run, instrument and as-of. Backend owner/policy validation was not bypassed.
- Invalid-output and failed-job copy previously exposed technical details in
  the main reading flow. Moved diagnostics into collapsed details without
  hiding the warning or relaxing review gates (`8056c54`, `cbb1bfe`).

## Executed checks

- At clean candidate above, scoped API/static/source/receipt gate:
  `pytest tests/test_built_web.py tests/test_platform_api.py
  tests/test_analysis_configuration_api.py tests/test_run_job_api.py
  tests/test_screening_api.py tests/test_valuation_evidence_api.py
  tests/test_snapshot_analysis.py tests/test_portfolio_valuation_service.py -q`:
  **71 PASS**, 14.76 seconds. Tests include missing/foreign owner, missing/forged/
  cross-session/expired CSRF, Host/Origin refusal, metadata redaction, invalid
  artifact content, unsupported/future/wrong-asset risk inputs and source clocks.
- Latest frontend: **84 PASS**, lint/typecheck/build PASS. Tests cover escaped
  narrative, bounded previews, response identity, rejected transitions and
  malformed display recovery. Browser evidence for real expiry/revocation,
  conflicting review, invalid output, cancel/new run and retry exhaustion is in
  [the verification ledger](milestone-4-verification.md).
- `npm audit` (including dev dependencies) and runtime-only audit: zero reported
  advisories. `pip-audit 2.10.1 --path <developer-site-packages> --skip-editable`:
  109 packages, zero reported advisories; internal editable package skipped.
  Advisory scans do not establish absence of unknown vulnerabilities.
- Tracked-file inventory contained no populated runtime environment/database/
  certificate artifact. High-signal private-key/OpenAI-project/AWS/GitHub-token
  pattern scan found no matching tracked files; no values were printed.
  This limited manual-pattern scan is not an exhaustive entropy/history scan;
  `gitleaks` was not installed. No secret was found requiring rotation.

## Limits and delivery conditions

### Final display-diff addendum — 2026-09-27

Reviewed `cbb1bfe..967aa24` after the original source review. Changes are
finance-first labels, policy table formatting, compatible-source display and
supporting tests/docs. Existing exact-ID submission, freshness checks, risk
values, session/CSRF and approval enforcement remain unchanged. Unknown role
names are rendered as escaped text with own-property lookup; custom risk warning
text is preserved. No new HTML sink, external endpoint or provider. No new
confirmed exploitable finding in this follow-up scope.

At clean `967aa24ab148d8dc4b78979a0134ea3b254be1d6`: 87 frontend tests,
lint/typecheck/build and full PostgreSQL regression (1284 tests + 88 subtests)
PASS. Browser approval conflict, same-database API reconnect, final mobile
presentation and logout verified. Full details and the two optional/provider
skips remain in the verification ledger. Later documentation-only edits do not
change this reviewed application tree.

### Ongoing limits

PASS for this scoped local/manual source-review gate. Rerun relevant checks and
review subsequent security-sensitive changes before merge. Final whole-candidate
regression and PostgreSQL receipt remain separate delivery gates. Do not infer
public-deployment safety, live provider readiness, broker safety or investment
validity from this review. No hosted CI was enabled or required.

Idle pages clear private in-memory content when an authenticated request fails;
this release does not claim a browser-only idle-screen lock. Local HTTP cookies
are only appropriate for loopback. TLS, rate limiting, recovery/backup controls,
public exposure and hostile multi-user hosting require a separately approved
deployment review. Stored source integrity verifies recorded bytes, not whether
the upstream financial facts are true.
