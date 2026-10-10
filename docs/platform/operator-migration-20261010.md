# Owner-approved local migration — 2026-10-10

Scope: original private SQLite workspace; paired encrypted local backup and
additive schema upgrade only. No broker/execution, CI, public exposure, provider
change or production-ready verdict. This receipt supersedes only the pending
backup/migration choice in the older [HANDOFF](../../HANDOFF.md) checkpoint.

## Exact execution boundary

- Source: clean `fix/TA-R01-research-quality`,
  `eae0a6caca4765ddaf7e70e080dbb8cf58885018`, Python 3.14.7, existing environment.
- Owner approved local encrypted vault, password custody/retention, maintenance
  and backup/migration of existing storage. Password stayed owner-local.
- Operator-local `capture-and-check.py capture` used SQLite backup API, not a
  DB/WAL file copy; preserved complete artifact inventory including unreferenced
  files and empty directories. Original tables/rows/schema/sequence fingerprints
  and every referenced blob were checked. Data never entered Git or static web.
- A separate database copy inside the encrypted vault rehearsed the original
  Alembic upgrades to explicit `0018_preparation_refusals`; original backup stayed
  at `0010_owner_watchlist`. No downgrade, reset, backfill or bootstrap.
- Owner's first `reopen-and-verify.command` detached successfully, then failed
  authentication. No data recreation or migration followed that failure.
- Owner's `retry-open-vault.command` used `hdiutil attach -readonly -noautoopen
  -stdinpass` with direct `/dev/tty` password entry; then paired readback PASS.
  Current independent verifier sessions 21858 and 10698 both terminal0 PASS.
- `migrate-approved-source.py`, session82787 terminal0, verified frozen SHA,
  read-only encrypted mount, trusted manifest and unchanged quiescent source,
  then called original `upgrade_database` with explicit revision0018.
  Full post-upgrade comparison and backup revalidation PASS.

Scripts, exact private target selection, trusted anchor, manifests and private
receipt remain in the owner's approved local operator directory, not in Git.
Public receipt intentionally omits private paths, database URLs, blob hashes,
account identifiers and raw values. A clone does not carry this backup or its
password. The encryption uses macOS AES-256 disk-image protection plus a trusted
owner-only manifest anchor; no claim of a separately signed/authenticated cloud
archive or independently verified cryptographic construction is made.

## Results and limits

| Gate | Status | Evidence boundary |
| --- | --- | --- |
| Encrypted image and owner-password reopen | PASS | Exact local image identity, native encrypted flag, owner reopen and current readback |
| Complete paired capture and integrity | PASS | Original DB integrity/FKs, all files/directories and 15 referenced blobs |
| Rehearsal and in-place schema upgrade0010→0018 | PASS | Original migration chain, explicit pinned revision, no source reset |
| Original history and artifact preservation | PASS | All 15 original non-version tables, exact rows/schema/sequence and full artifact bytes; resulting DB matches rehearsal |
| Quiescent source/pending-work audit | PASS | Nine saved runs, eight succeeded and one cancelled job; no active jobs/leases; new recovery tables empty |
| Fresh login/browser saved EN/VI readback | UNVERIFIED | API/worker not started by this operation; zero unrevoked nonexpired sessions, no session mutation |
| Fresh-target restore/copied-session fencing | UNVERIFIED | In-place additive migration is not a restored installation |
| Encrypted cloud transfer/PostgreSQL rollout | UNVERIFIED | Not performed; local SQLite proof does not establish these gates |
| Full financial/semantic/VI/live UX acceptance | UNVERIFIED | Retain existing FAIL/UNVERIFIED receipts; no new paid job submitted |
| Live NQ=F | BLOCKED | Owner chose to wait for eligible active-contract/roll metadata, no new provider |

Vault remains read-only and retained; no automatic cleanup or restore over the
source. Worker/API startup needs separate reviewed authorization. The pending
proposal is loopback8001 for the real workspace while leaving synthetic8000
untouched, with worker use limited to the previously approved one BTC plus one
AAPL run; neither run has been submitted. Never treat a prior successful job,
saved consent or backup as permission to replay a paid analysis.

This is an operational receipt, not a product-code change. Earlier full Python
and web regression receipts retain their original exact SHAs; no new full suite
or supported-version matrix is implied. Entire R01–R14 scope remains ACTIVE.
