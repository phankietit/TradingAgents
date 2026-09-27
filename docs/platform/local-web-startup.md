# Start the private local Web UI

This is a local research workspace, not a brokerage account or live price feed.
M4 acceptance evidence is tracked separately in [the verification ledger](milestone-4-verification.md).
No hosted CI or public deployment is required or enabled by these steps.

## 1. Install and build

Use the intended checkout and a Python virtual environment. Install
`pip install '.[platform]'`. In `web/`, run `npm ci` then `npm run build`.
Verified runtimes: Python 3.14.7, Node 26.8.1 and npm 11.19.0; this is not proof
of every supported runtime. The Python wheel does not include `web/dist`.
Follow this machine's external-storage policy before dependency/build work.

## 2. Configure private storage and initialize explicitly

Provide these environment variables to the API and worker through your local
secret setup; do not paste populated credentials into source, screenshots or logs:

- `TRADINGAGENTS_DATABASE_URL`: your approved local database, with the
  `postgresql+psycopg://` scheme for PostgreSQL. SQLite is supported for isolated
  development checks; it is not proof of PostgreSQL concurrency.
- `TRADINGAGENTS_ARTIFACT_ROOT`: an absolute, private writable directory for
  immutable source/report artifacts. Keep it outside static web assets.

For a **new empty database only**, initialize from a local Python session after
setting the variables above. Do not use this as a migration/backup procedure for
an existing owner database. Existing installations need a backup and reviewed
migration plan; never downgrade an owner database to reproduce QA.

```python
import os
from getpass import getpass
from tradingagents.platform.auth import OwnerAuth
from tradingagents.platform.instruments import InstrumentMaster
from tradingagents.platform.persistence import Database, PlatformRepository, upgrade_database

url = os.environ['TRADINGAGENTS_DATABASE_URL']
upgrade_database(url)
database = Database(url)
try:
    with database.session() as session:
        OwnerAuth(session).bootstrap_owner(input('Owner email: '), getpass('Owner password: '))
        InstrumentMaster(PlatformRepository(session)).bootstrap()
finally:
    database.dispose()
```

There is no default owner password. Bootstrap is one-time and rejects another
owner. Passwords must have 12–1024 characters. This creates instrument identities,
not market snapshots, portfolio holdings or risk policies.

## 3. Start the API and web together

In the API process environment, additionally set:

```sh
export TRADINGAGENTS_WEB_ROOT="/absolute/path/to/TradingAgents/web/dist"
export TRADINGAGENTS_ALLOWED_ORIGIN="http://127.0.0.1:8000"
export TRADINGAGENTS_API_PORT=8000
export TRADINGAGENTS_SECURE_COOKIES=false
tradingagents-api
```

Open `http://127.0.0.1:8000`. This insecure-cookie setting is only for loopback
HTTP. Use the exact origin; a `localhost` alias is not interchangeable. Do not
expose the port publicly or place a tunnel in front of it. No Vite dev server is
needed for the built UI. API startup does not create an owner, migrate, seed,
ingest sources or start the worker. The package may load ignored `.env` and
`.env.enterprise` from the current directory/parents; use the intended working
directory and never assume unrelated inherited settings are safe.

Set `TRADINGAGENTS_LLM_PROVIDER`, `TRADINGAGENTS_QUICK_THINK_LLM` and
`TRADINGAGENTS_DEEP_THINK_LLM` explicitly in the same environment for API and
worker. The API records these on new runs; the worker uses those recorded
models. Missing/blank values retain the API defaults (`openai`, `gpt-4o-mini`,
`gpt-4o`), not the standalone CLI defaults. Existing runs are not rewritten.
Provider reasoning settings such as `TRADINGAGENTS_OPENAI_REASONING_EFFORT`
are read by the worker and depend on model support; they are not dedicated
immutable run fields. Restart the relevant processes after changing env.

When the ignored env file belongs to another checkout, load its explicit path
before importing the package instead of copying secrets into the worktree:

```sh
.venv/bin/python -c 'from dotenv import load_dotenv; load_dotenv("/absolute/path/to/private/.env", override=False); from tradingagents.platform.api.runtime import main; main()'
```

Existing process environment takes precedence. Loading a key is not proof of
provider access, quota or a successful paid request. Never use `VITE_`-prefixed
variables for provider credentials.

## 4. Supply evidence, then opt into processing

The UI reads existing owner-scoped records. Empty lists are expected for a fresh
database; never copy synthetic QA evidence into an investment workspace.
Follow [snapshot contracts](normalized-time-series.md),
[portfolio ledger](portfolio-ledger.md), [risk policy](risk-engine.md) and
[analysis engine](analysis-engine.md) for operator-controlled inputs.

There is no automatic ingestion scheduler in this UI. A weekly/medium-term
workflow should ingest approved sources before each review, inspect source
timestamps and coverage, then run research against the chosen cutoff. Refresh
only rereads saved records. Equities/ETFs use their exchange sessions; BTC/ETH
use a 24/7 calendar. NQ/ES are context references, never investable positions.
Missing historical coverage or stale evidence must not be filled from current
data merely to obtain a result.

Only after configuring and authorizing model use, launch `tradingagents-worker`
in a separate terminal with the same database and artifact root. It consumes
eligible queued jobs and may incur model charges. Stopping the API does not
stop an independently running worker. Stop each task-owned process with Ctrl-C;
do not delete the database or artifact store. Retry/cancellation semantics are
documented in [durable jobs](durable-jobs.md).

## 5. Review, do not execute

Read thesis, risks, invalidation conditions and source quality. Portfolio values
and policy checks come from the backend, not browser calculations. Approval
requires an explicit reason and backend revalidation; it records research
review, not an order. A successful job with invalid output remains review-only.
For a safe no-cost QA demonstration, use the isolated fixture instructions in
[web/README](../../web/README.md), not the owner database.
