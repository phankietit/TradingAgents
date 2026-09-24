# Immutable Artifact Store

Platform evidence is stored as immutable, content-addressed blobs. Database
rows contain owner-scoped manifests; blob bytes are never accepted or resolved
from a caller-provided filesystem path.

## Current Backend

`LocalArtifactStore` is the development and test backend. It requires an
explicit root, derives every key from a lowercase SHA-256 digest, writes through
an atomic create operation, and validates hash plus byte size on every read.
Identical bytes reuse one blob. Revised bytes produce a new key and never
overwrite prior evidence.

The local backend is not a production storage choice. Selecting S3 or another
object-storage vendor requires a separate approved provider decision, threat
model, retention policy, encryption policy, backup/restore evidence, and live
integration gate.

## Manifests And Privacy

`ArtifactManifest` records owner, kind, media type, content hash, size, storage
key, creation time, and optional run/instrument/snapshot context. Manifests are
immutable and fetched with `owner_id`; a UI filter is not authorization.

Supported initial kinds are snapshot payloads, analysis reports, run event
logs, and decision evidence. Snapshot payload manifests require a
`snapshot_id`, keeping provenance linked to the versioned snapshot contract.

## Failure Semantics

- Expected-hash mismatch fails before a blob is published.
- A missing, symlinked, truncated, or modified blob fails closed with an
  integrity error.
- A database transaction failure can leave an unreferenced immutable blob; it
  must not trigger automatic deletion. A future audited garbage-collection
  ticket may remove only proven-unreferenced blobs under a retention policy.
- No API, public serving endpoint, retention deletion, or production object
  store is introduced by this ticket.
