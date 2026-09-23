"""Coordinate immutable blob writes with owner-scoped database manifests."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from tradingagents.contracts import ArtifactKind, ArtifactManifest
from tradingagents.platform.persistence import PlatformRepository

from .store import ArtifactStore, StoredBlob


class ArtifactService:
    def __init__(self, store: ArtifactStore, repository: PlatformRepository):
        self.store = store
        self.repository = repository

    def create(
        self,
        *,
        owner_id: UUID,
        kind: ArtifactKind,
        media_type: str,
        content: bytes,
        run_id: UUID | None = None,
        instrument_id: UUID | None = None,
        snapshot_id: UUID | None = None,
        artifact_id: UUID | None = None,
        created_at: datetime | None = None,
        expected_hash: str | None = None,
    ) -> ArtifactManifest:
        blob = self.store.put_bytes(content, expected_hash=expected_hash)
        manifest = ArtifactManifest(
            artifact_id=artifact_id or uuid4(),
            owner_id=owner_id,
            kind=kind,
            media_type=media_type,
            content_hash=blob.content_hash,
            byte_size=blob.byte_size,
            storage_key=blob.storage_key,
            created_at=created_at or datetime.now(UTC),
            run_id=run_id,
            instrument_id=instrument_id,
            snapshot_id=snapshot_id,
        )
        return self.repository.add_artifact(manifest)

    def read(self, artifact_id: UUID, owner_id: UUID) -> tuple[ArtifactManifest, bytes] | None:
        manifest = self.repository.get_artifact(artifact_id, owner_id)
        if manifest is None:
            return None
        blob = StoredBlob(
            content_hash=manifest.content_hash,
            byte_size=manifest.byte_size,
            storage_key=manifest.storage_key,
        )
        return manifest, self.store.get_bytes(blob)
