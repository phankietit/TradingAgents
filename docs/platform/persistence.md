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

## Synthetic paired restore acceptance

`tests/test_paired_restore_api.py` is a local SQLite/artifact recovery gate, not
an operator backup command. It creates a new synthetic account, instrument,
run and separate EN/VI report blobs, closes writers, uses SQLite's backup API,
then copies artifacts into a new restore root. A fresh API process context logs
in with the copied synthetic account and checks unchanged run metadata and
exact report bytes/hashes. Anonymous reads refuse, foreign-owner artifacts
remain inaccessible, and missing/tampered restored blobs return integrity errors.
Full SQL dump, database hash and blob bytes of the original fixture remain
unchanged after restored authentication/readback. Temporary fixture credentials
and databases never enter Git.

Test presence is not execution evidence; see HANDOFF for exact receipts. This
does not prove PostgreSQL dump/restore, encrypted backup/transfer, writer
coordination, retained session safety, active jobs/checkpoints, restored browser
UX or an operational owner restore. Those remain required before private
platform release. Never copy a live owner DB with this test or overwrite its
history. An actual rollout needs the separately reviewed paired backup/restore
and session/worker restart runbook described above.

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

Additive `0015_linked_dispatch` creates one dispatch-consumption row per linked
execution, with the pinned original checkpoint ID/hash and consumption time.
Consumption reloads immutable root evidence, owner-readable source bytes and
the exact unused retained observer inside the linked publication transaction.
It commits before child construction; a lost committed ACK is uncertainty,
not permission to respawn, reset budget or mark success. It introduces no new
root job, mutable dispatch-success state or default worker claim path.
SQLite/PostgreSQL single-consumer/race fixtures and disposable schema reversal
are local evidence only. No private database migration or automatic history
deletion is authorized; default API/worker activation remains disabled.

Additive `0016_linked_results` stores only artifact actor links and one atomic
completion receipt per execution, linked to the final private checkpoint,
report/evidence/candidate identities and pinned hashes. It does not rebuild
analysis_runs/analysis_jobs or change terminal root status. Native result
return, clean child exit/reaping, exact bound parent publisher and durable
stopped accounting are required before the shared ordinary report/evidence/
risk pipeline can append output metadata and the receipt in one fenced commit.
Blob puts remain content-addressed; a rolled-back metadata transaction may
leave an unreferenced blob, never an apparently completed result or auto-deletion.
Read-only receipt verification works after lease expiry and lost ACK, checking
original root/job, consent/dispatch/checkpoint/event/artifact actor links, pinned
hashes and stopped cumulative accounting. It does not authorize execution or
approval. Default continuation API/worker dispatch stays disabled. The existing
decision transition route can now approve a linked candidate only after full
completion-receipt/source integrity, original deterministic risk and human-owner
policy/lifecycle validation; no failed/cancelled root is relabelled. Candidate
payload/hash is immutable, current indexed status must match append-only events.
All linked lifecycle events are checked against completion time before any write
or idempotent acknowledgement, including review/reject/expire. The boundary is
inclusive; later events must still strictly follow existing lifecycle history.
Non-approval actions grant no investment authority; full approval/source/risk
validation remains separate and mandatory for approval.
This uses existing tables and needs no additional migration. Follow the
same backup/owner rollout gates; schema reversal tests use disposable empty tables.

The ORM and packaged `0016` migration explicitly share
`uq_linked_completion_report` and `uq_linked_completion_decision`. Fresh disposable
SQLite/PostgreSQL schema checks assert these names as well as columns; the full
PostgreSQL autogenerate parity gate must remain empty. This corrects ORM metadata,
not the migration or an existing private database. No constraint rename or
private-history rebuild is required or authorized by this source fix.

Additive `0017_linked_stops` creates only one separate stop fact per execution,
with owner/root, a strict hash-bound payload and stop observation time. The
trusted original supervisor records it only after joining the actual parent-owned
Process, closing both pipes and stopping/joining its reader. Exact original
context/observer/request, private lease nonce/worker/deadline, source manifest,
entry/dispatch and cumulative accounting must match. Cancel/expiry may permit
only this control-plane fact, never ordinary publication/admission. No existing
row/event is relabelled, no allowance or cost is inferred/refunded. The standalone
owner-scoped reader resolves committed ACK loss and rejects missing/foreign/
corrupt provenance. Database failure/missing fact preserves uncertainty.
Default API/worker/CLI continuation remains disabled. No private database
migration/restart/backfill or deletion is authorized by this source change;
upgrade/downgrade and rollback evidence use acknowledged disposable QA only.
The stop reader verifies its recorded immutable event prefix, not a truncated
allowance assessment. Later appended attempts do not invalidate the old stop
fact; consent/recheck/remaining-allowance paths still load all latest accounting
and cannot use a prefix to drop later starts or restore an unknown time bound.
