# Private operator backup and restore

Release class: private decision-support platform, not broker execution.
This is the required procedure and acceptance checklist, **not an implemented
backup CLI or permission to copy/restore owner data**. Synthetic paired SQLite/
PostgreSQL restore tests exist; encrypted operator backup, session fencing,
active-job recovery and restored browser acceptance remain UNVERIFIED. See
[persistence](persistence.md) and [HANDOFF](../../HANDOFF.md) for executed receipts.
A documented step is not a passed gate.

## Preconditions

Obtain explicit owner approval for source, new target, private encrypted
destination, encryption recipient/key custody, retention and maintenance window.
A public Git handoff does not approve copying private data. Do not add a storage
provider, transfer data, stop a user process or overwrite a DB implicitly.

Keep a private receipt with source SHA, schema revision, Python/dependency
fingerprint, DB engine/version, artifact format, backup ID and capture time.
Never publish DB URLs, credentials, private report hashes, owner emails, raw rows,
reports, private paths or checkpoints in Git/PR logs. Use fresh private staging
outside Git/static assets with owner-only access, sufficient space and the
machine storage policy. Backups contain sensitive password/session hashes and
investment history even without `.env`.

Verify the owner's reviewed encryption/decryption tools and recipient/key access
before capture. Missing keys/destination is a stop, not permission for plaintext
upload. Do not select an encryption backend or cloud destination automatically.
Secrets travel through an independently approved channel, never in the manifest.

## Capture one consistent DB/artifact pair

1. During the approved window prevent new acquisition, research, approval and
   continuation requests. Inventory exact API, ordinary/continuation workers and
   children; confirm shutdown/reaping of owned writers. API shutdown alone does
   not stop workers. Do not kill other sessions, reset jobs, mark uncertain work
   stopped or infer remote provider termination/refund. If writers cannot safely
   be quiesced, stop; concurrent backup needs a separately verified protocol.
2. Capture the complete DB, schema and sequence state. PostgreSQL uses compatible
   custom-format `pg_dump`, with authentication in owner-only libpq service/
   password configuration, not password-bearing argv/logs. SQLAlchemy URLs are
   not libpq configuration. No downgrade/reset. SQLite development copies use
   its backup API and integrity check, never copy an actively written DB/WAL.
   SQLite proof is not PostgreSQL rollout proof.
3. While writers remain quiesced, copy the complete immutable artifact store.
   Inventory every DB-referenced blob's identity, size and hash privately,
   including source/report/checkpoint artifacts. Keep unreferenced blobs; no
   garbage collection during backup. Missing/corrupt referenced bytes fail
   capture; never reconstruct them from current vendor/model output.
4. Bind both captures and versions to one backup ID, verify locally, then encrypt
   the entire pair and manifest using the owner's reviewed authenticated setup.
   Integrity needs a trusted local manifest or authenticated signature: a hash
   beside an untrusted archive is not authentication. Verify decryption/integrity
   in a new isolated directory before approved transfer. Partial pairs are not
   valid backups. Plaintext cleanup/retention requires explicit ownership checks
   and the approved plan, never recursive deletion of a storage parent.

Capture completion does not authorize paid jobs. Original-installation worker
restart needs its own recorded approval, not an automatic post-backup action.

## Restore into a new inactive target

1. Authenticate/decrypt into new private staging. Before extraction refuse
   absolute/traversal paths, symlinks/hardlinks, special files, duplicate entries
   and expansion beyond reviewed resource bounds. Never execute archive scripts
   or deserialize arbitrary Python/pickle. Research checkpoint reads retain
   their existing restricted codec/integrity validation.
2. Prove DB is freshly created/empty and artifact root new, neither resolving to
   source/existing owner storage. Use compatible `pg_restore` with exit-on-error
   into that new DB. No `--clean`, DROP, downgrade, reset, bootstrap-owner,
   vendor backfill or history rewrite. Failed targets stay isolated; no
   destructive retry or source mutation.
3. Before startup compare schema revision, all table data/sequence state and
   every referenced blob's hash/owner/kind. Revalidate original manifests and
   linked accounting/consent/completion/stop receipts using existing integrity
   readers. Invalid/missing evidence stays unavailable/uncertain: no manufactured
   success, older fallback or financial/risk/translation gate bypass.
4. Fence all copied sessions before exposure. Backup taken before logout/password
   change can revive an old still-valid token. Preserve financial/run/evidence
   history; revoke authentication on the **new copy only**, in a reviewed
   transaction, then require fresh login. Existing `OwnerAuth.change_password`
   revokes all unrevoked owner sessions, but no audited operator restore command
   exists yet. A synthetic PG16 test in `tests/test_postgres_paired_restore.py`
   exercises post-backup logout revival, target-only password rotation, durable
   old-cookie/CSRF refusal, fresh login and source/history preservation. Test
   presence is not execution evidence; consult exact receipts. It does not prove
   operator target selection, browser rollout or encrypted restore. Do not call
   private helpers or mutate an existing owner DB to simulate acceptance.
5. Start only restored API on reviewed loopback settings: no worker, acquisition,
   public exposure, automatic migration or model job. Verify old cookies fail,
   fresh owner login succeeds, foreign-owner data is denied and saved EN/VI
   reports/source details match. Language/report switching must create no job.
6. Audit queued/running ordinary jobs, leased/uncertain research executions,
   checkpoints and reservations before any worker restart. Copied lease/local
   stop receipt is not provider-stop proof. Restored budget is not new allowance;
   pending consent is not blanket approval to replay on another machine. Never
   reset/requeue jobs or relabel terminal history. Record original state and
   uncertainty; obtain owner direction for unvalidated recovery. Keep ordinary
   and opt-in continuation workers off until audit/restart approval.

The current fixture covers synthetic successful run/report readback, not active
work or operator recovery. Never restore an investment workspace into a synthetic
fixture or use synthetic success to waive original financial/human approval.

## Acceptance and rollback

Separate receipts must prove paired capture, authenticated encrypted transfer/key
recovery, untouched source, fresh-target schema/data/blobs, old-session refusal/
new login, saved EN/VI browser readback, active/queued job/checkpoint uncertainty
and explicit restart authorization. Test wrong key/corrupt bundle, unsafe archive
path, missing/tampered blob, source/nonempty target, interruption, failed restore
and unavailable source/key. Failures must neither modify original history,
dispatch AI nor leave an apparently valid partial restore.

Record exact environment/SHA, credential-free commands, results and limitations
privately; publish only redacted statuses. Local synthetic tests do not prove
these operator receipts. Private-platform acceptance stays UNVERIFIED until
tooling and complete rehearsal pass.

Rollback withholds the new target and retains the intact original, not automatic
endpoint switching/deletion. If new work exists on a restored target, preserve
both and ask for reviewed reconciliation; never merge DBs or overwrite history.
No automatic plaintext cleanup, transfer, migration or worker restart.
