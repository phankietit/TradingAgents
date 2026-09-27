# English / Vietnamese language contract

## Scope and acceptance

- VI/EN controls on login and authenticated screens: Markets, Analysis,
  Portfolio, Decisions, financial labels, warnings, forms and accessibility copy.
- Keep drafts, navigation, source selection and consent when changing UI locale;
  UI locale is not report language and cannot submit financial actions.
- Store only `en` or `vi` in the versioned local preference key; tolerate disabled
  storage. Prefer the saved locale, then Vietnamese browser locale, else English.
- Format numeric displays for en-US/vi-VN without changing stored values. Decimal
  holdings remain string-based (no binary floating-point conversion). Keep UTC
  timestamps explicit and ISO/numeric input/API conventions unchanged.
- Source narrative, portfolio names, original policy details, identifiers,
  citations and machine codes remain original. The UI is not a translation proxy.

## Report generation

New snapshot-mode Portfolio Manager output may retain a `localized_report`
with complete `en` and `vi` Markdown. Bilingual runs require both; the schema
checks numeric-token parity, and the UI switches saved content without model
calls. Canonical decision fields remain English. This is a translation-integrity
check, not certified semantic equivalence. Older mixed-language reports are
shown as saved and are not regenerated. Markdown never executes raw HTML or
loads remote images; source links remain in the separate provenance view.

`POST /api/v1/runs` accepts optional `report_language`: `en`, `vi`, `en-vi`, or
null/omitted for legacy worker-configured behavior. The web form explicitly
defaults to `en-vi`. Changing this selection clears paid-run consent. The API
allowlist rejects arbitrary prompt text.

An explicit selection participates in `config_hash`, immutable `RunManifest`
JSON, job payload and worker payload validation. It cannot change during a
lifecycle transition. Omitted language leaves the original config-hash/job
payload shape unchanged, preserving legacy queued work and idempotency.
This additive JSON field needs no SQL migration. Update API and workers together;
an old worker does not understand a new explicitly localized job.

The worker overrides only `output_language` using a fixed mapping. Models,
provider routing, retries, financial policy, evidence and approval checks are
unchanged. A report records the requested language; null means legacy/unrecorded,
not proof that a report is English. The report viewer retains original text and
escaping. Downloaded artifacts are not rewritten or post-processed.

For `en-vi`, the existing language prompt asks for paired English and Vietnamese
in each narrative section/string, while retaining exact financial values,
units, signs, dates, tickers, citations, uncertainty and invalidation conditions.
JSON keys, enums and tool arguments must remain unchanged. This is a generation
instruction, not a certified translation or a new evidence source. No separate
translation provider, automatic translation call or regeneration of old reports
is added. Bilingual output may increase tokens/latency and truncation risk under
existing limits. Invalid structured output still becomes REVIEW.

## Local verification (2026-09-27)

Implementation branch: `feature/TA-M4-bilingual`, based on `origin/main`
`7dfec4d20709a702b130f3ba5813f097a930ffe6`, retaining the model-env fix.
Runtime: macOS, Python 3.14.7, Node 26.8.1, npm 11.19.0.

- PASS: Python local regression, lint, dependency consistency and diff checks.
  Includes language allowlist, language-sensitive idempotency/hash, immutable
  language, mismatched worker payload rejection before model use and prompt
  preservation fixtures. Legacy worker tests remain intact.
- PASS: frontend tests, TypeScript, ESLint and Vite build. Includes UI language
  changes without credential submission/draft reset, stable asset-filter values,
  consent reset, exact decimal/UTC preservation, six distinct quality states,
  original report text/HTML escaping and translation-catalog coverage.
- PASS: bundled Playwright Chromium against a separate synthetic-only local
  fixture at 127.0.0.1:8001, 1440×1000 and 390×844. Login → VI/EN → reload → asset
  filters → new bilingual analysis → fake worker → original bilingual report →
  portfolio → disabled approval. No live model/vendor call, no owner records.
  Initial unauthenticated `/auth/me` returns expected 401; final run has no
  unexpected console/page errors or horizontal page overflow.
- UNVERIFIED: live model bilingual fluency, translation equivalence and actual
  token costs. Owner authorization is required for paid verification.
- UNVERIFIED: PostgreSQL-specific, optional Bedrock and live DeepSeek gates not
  run for this local SQLite candidate. No hosted CI/public deployment.

Browser plugin was unavailable; the existing bundled Playwright runtime was
used without adding repository dependencies. Synthetic screenshots/runtime
evidence are outside committed source and never mixed into the owner database.
