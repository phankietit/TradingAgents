# Evidence graph

Material decision claims are represented by `EvidenceClaim` nodes linked to
immutable snapshot-backed `EvidenceReference` records. Each reference preserves
the vendor, observed/source timestamps, point-in-time cutoff, snapshot ID, and
content hash. Missing, stale, unavailable, or future-leaking snapshots cannot
support a material claim.

The graph hash covers all claim and evidence links so a recorded decision can
identify the exact evidence set it used. This is local contract and unit-test
evidence; it does not prove a live vendor is currently reachable.

Graph IDs, claim IDs, evidence IDs and hashes are deterministic for identical
run inputs, regardless of source/claim insertion order. Deserialization verifies
the hash and every link. Duplicate sources, missing publication/source time,
future snapshot cutoffs, and observations predating the source are rejected.
Retrieval after the analysis date remains possible for an archived historical
source; retrieval time is preserved separately from source eligibility.

`EvidenceGraphService` resolves sources from the database using an owner-scoped
run. Sources must be in that run's snapshot manifest and match its instrument.
It stores the graph as an immutable `DECISION_EVIDENCE` artifact and enforces
owner/run scope when reading. No caller-supplied snapshot is trusted on this
persistence path. Cross-instrument macro/benchmark claims require a separately
typed relationship before they can enter this graph.
