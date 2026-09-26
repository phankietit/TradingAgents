# Evidence graph

Material decision claims are represented by `EvidenceClaim` nodes linked to
immutable snapshot-backed `EvidenceReference` records. Each reference preserves
the vendor, observed/source timestamps, point-in-time cutoff, snapshot ID, and
content hash. Missing, stale, unavailable, or future-leaking snapshots cannot
support a material claim.

The graph hash covers all claim and evidence links so a recorded decision can
identify the exact evidence set it used. This is local contract and unit-test
evidence; it does not prove a live vendor is currently reachable.
