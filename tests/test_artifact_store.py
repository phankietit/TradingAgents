"""Immutable artifact store and manifest persistence evidence."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest

from tradingagents.contracts import ArtifactKind
from tradingagents.platform.artifacts import (
    ArtifactIntegrityError,
    ArtifactService,
    LocalArtifactStore,
    StoredBlob,
)
from tradingagents.platform.persistence import (
    Database,
    ImmutableRecordConflict,
    PlatformRepository,
    upgrade_database,
)


@pytest.mark.unit
def test_identical_content_is_idempotent_and_content_addressed(tmp_path):
    store = LocalArtifactStore(tmp_path / "artifacts")
    first = store.put_bytes(b"immutable evidence")
    second = store.put_bytes(b"immutable evidence")

    assert first == second
    assert first.content_hash.startswith("sha256:")
    assert first.storage_key.endswith(first.content_hash.removeprefix("sha256:"))
    assert store.get_bytes(first) == b"immutable evidence"
    assert len([path for path in store.root.rglob("*") if path.is_file()]) == 1


@pytest.mark.unit
def test_new_content_creates_new_version_without_overwriting_old_blob(tmp_path):
    store = LocalArtifactStore(tmp_path / "artifacts")
    original = store.put_bytes(b"version one")
    revised = store.put_bytes(b"version two")

    assert original != revised
    assert store.get_bytes(original) == b"version one"
    assert store.get_bytes(revised) == b"version two"


@pytest.mark.unit
def test_concurrent_writers_publish_one_complete_blob(tmp_path):
    store = LocalArtifactStore(tmp_path / "artifacts")
    content = b"same bytes from concurrent workers"

    with ThreadPoolExecutor(max_workers=8) as executor:
        blobs = list(executor.map(lambda _: store.put_bytes(content), range(32)))

    assert len(set(blobs)) == 1
    assert store.get_bytes(blobs[0]) == content
    assert len([path for path in store.root.rglob("*") if path.is_file()]) == 1


@pytest.mark.unit
def test_expected_hash_mismatch_is_rejected_before_persistence(tmp_path):
    store = LocalArtifactStore(tmp_path / "artifacts")
    with pytest.raises(ArtifactIntegrityError, match="expected_hash"):
        store.put_bytes(b"unexpected", expected_hash="sha256:" + "0" * 64)

    assert not [path for path in store.root.rglob("*") if path.is_file()]


@pytest.mark.unit
def test_tampered_blob_and_forged_storage_key_are_rejected(tmp_path):
    store = LocalArtifactStore(tmp_path / "artifacts")
    blob = store.put_bytes(b"trusted")
    target = store.root.joinpath(*blob.storage_key.split("/"))
    target.write_bytes(b"tampered")

    with pytest.raises(ArtifactIntegrityError, match="does not match"):
        store.get_bytes(blob)

    forged = StoredBlob(blob.content_hash, blob.byte_size, "sha256/00/00/forged")
    with pytest.raises(ArtifactIntegrityError, match="storage key"):
        store.get_bytes(forged)


@pytest.mark.unit
def test_symlink_escape_is_rejected(tmp_path):
    root = tmp_path / "artifacts"
    store = LocalArtifactStore(root)
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "sha256").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ArtifactIntegrityError, match="symlink"):
        store.put_bytes(b"must stay inside root")
    assert not list(outside.iterdir())


@pytest.mark.unit
def test_json_encoding_is_canonical(tmp_path):
    store = LocalArtifactStore(tmp_path / "artifacts")
    first = store.put_json({"b": 2, "a": 1})
    second = store.put_json({"a": 1, "b": 2})

    assert first == second
    assert store.get_json(first) == {"a": 1, "b": 2}


@pytest.mark.unit
def test_artifact_service_persists_immutable_owner_scoped_manifest(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'platform.db'}"
    upgrade_database(database_url)
    database = Database(database_url)
    store = LocalArtifactStore(tmp_path / "artifacts")
    owner_id = uuid4()

    with database.session() as session:
        service = ArtifactService(store, PlatformRepository(session))
        manifest = service.create(
            owner_id=owner_id,
            kind=ArtifactKind.ANALYSIS_REPORT,
            media_type="text/markdown",
            content=b"# Point-in-time report",
        )

    with database.session() as session:
        service = ArtifactService(store, PlatformRepository(session))
        assert service.read(manifest.artifact_id, uuid4()) is None
        stored_manifest, content = service.read(manifest.artifact_id, owner_id)
        assert stored_manifest == manifest
        assert content == b"# Point-in-time report"

    changed = manifest.model_copy(update={"media_type": "text/plain"})
    with pytest.raises(ImmutableRecordConflict), database.session() as session:
        PlatformRepository(session).add_artifact(changed)
    database.dispose()
