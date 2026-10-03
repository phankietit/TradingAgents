# Platform Persistence

The platform persistence layer stores versioned domain contracts without
changing the existing CLI files, Markdown reports, or checkpoint behavior.

## Runtime Contract

- PostgreSQL is the platform target. SQLite is supported only for isolated unit
  and migration tests.
- A database URL is always explicit; the package has no embedded production
  endpoint or credential.
- Install platform dependencies with `pip install "tradingagents[platform]"`.
- Apply packaged migrations with
  `tradingagents.platform.persistence.upgrade_database(database_url)`.
- Downgrades are available for candidate verification; production rollback must
  still follow a backup/restore runbook.

## Safety Properties

- Market instruments and snapshot manifests are immutable and idempotent by ID.
- Snapshot provenance includes vendor, as-of time, content hash, and quality.
- Private runs, decisions, portfolio snapshots, and policies are queried with
  `owner_id`; UI filtering is not treated as authorization.
- Run status changes follow an explicit state-transition map and terminal runs
  cannot restart.
- `Database.session()` commits the whole unit of work or rolls it back on any
  exception.

This ticket does not start PostgreSQL, choose a production host, expose an API,
or migrate existing local reports. Durable jobs and API wiring are separate
Milestone 1 tickets.

## Draft research recovery additions

`0011_research_checkpoints` and additive `0012_research_continuations` are private
recovery/consent tables, separate from readable reports and historical jobs.
The latter records authenticated owner intent bound to an immutable latest
checkpoint/accounting observation; it does not enqueue or authorize a model.
Migration `0011` now uses distinct explicit names for its two checkpoint unique
constraints, matching the model. The first draft's first-column naming convention
gave both the same name: PostgreSQL rejected the DDL, whereas SQLite accepted it.
This corrects draft DDL for a fresh database; it does not rename constraints or
rewrite records in an already migrated private SQLite database. Do not drop or
recreate that database to obtain cosmetic naming parity. An existing deployment
needs a separately reviewed additive migration/backup plan before rollout.

Disposable SQLite and PostgreSQL migration/concurrency fixtures cover these
additions. See exact-SHA acceptance receipts for executed results; test presence
does not prove PostgreSQL recovery or private runtime readiness. Follow
backup/restore and explicit owner rollout
before changing a private database; never downgrade/delete its checkpoint or
consent history as an automatic recovery action. See
[the recovery contract](research-recovery-contract.md) for activation gates.

Additive `0013_research_executions` stores separately leased internal allocations
linked by primary/foreign key to the immutable consent execution identity. The
original analysis_jobs unique run ID remains unchanged. A unique source-run/
attempt pair and state/attempt checks prevent duplicate allocation/invalid
states; only the new row's lease/cancellation/review fields may change.
No historical research state is cleared, no successful-result state is defined,
and the existing worker does not claim these rows. These test-only lease
mechanics do not authorize migration of a private database, model dispatch,
publication or repeated continuations without linked accounting integration.

Additive `0014_linked_publication` creates only three side tables: one actual
parent entry event per execution, actor links for linked events, and actor links
for new checkpoints. It does not rebuild/backfill historical tables or remove
the original job's unique run ID. Entry/event/checkpoint actor links are committed
with their evidence, not afterward. New checkpoints retain original run/thread/
job identity and derive their attempt from the independently fenced execution.
Idempotently acknowledging identical old checkpoint bytes never relabels them.
Latest linked provenance is validated on read; missing/corrupt linkage refuses
the latest row without fallback. An explicit disposable empty-table downgrade
tests schema reversal, not permission to delete private checkpoint history.
Default API/worker remain unwired; no private migration/activation is approved
by these source changes. Follow the same owner backup/restore/rollout gate.
