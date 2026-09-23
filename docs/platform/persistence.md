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
