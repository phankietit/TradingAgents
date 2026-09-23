"""Content-addressed immutable blob storage."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

HASH_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


class ArtifactIntegrityError(RuntimeError):
    """Stored content or its reference failed an integrity check."""


@dataclass(frozen=True, slots=True)
class StoredBlob:
    content_hash: str
    byte_size: int
    storage_key: str


class ArtifactStore(Protocol):
    def put_bytes(self, content: bytes, *, expected_hash: str | None = None) -> StoredBlob: ...

    def get_bytes(self, blob: StoredBlob) -> bytes: ...


def _content_hash(content: bytes) -> str:
    return f"sha256:{hashlib.sha256(content).hexdigest()}"


class LocalArtifactStore:
    """Local dev/test store with atomic, content-addressed writes.

    Production object storage is intentionally not selected by this implementation.
    """

    def __init__(self, root: str | Path):
        configured_root = Path(root).expanduser()
        if configured_root.exists() and configured_root.is_symlink():
            raise ValueError("artifact store root must not be a symlink")
        configured_root.mkdir(parents=True, exist_ok=True)
        self.root = configured_root.resolve(strict=True)

    @staticmethod
    def _storage_key(content_hash: str) -> str:
        if not HASH_PATTERN.fullmatch(content_hash):
            raise ValueError("artifact hash must be a lowercase sha256 digest")
        digest = content_hash.removeprefix("sha256:")
        return f"sha256/{digest[:2]}/{digest[2:4]}/{digest}"

    def _path_for(self, content_hash: str, *, create_parents: bool) -> tuple[str, Path]:
        key = self._storage_key(content_hash)
        directory = self.root
        segments = key.split("/")
        for segment in segments[:-1]:
            candidate = directory / segment
            if candidate.is_symlink():
                raise ArtifactIntegrityError("artifact path contains a symlink")
            if candidate.exists() and not candidate.is_dir():
                raise ArtifactIntegrityError("artifact directory is missing or invalid")
            if create_parents and not candidate.exists():
                candidate.mkdir(exist_ok=True)
            if not candidate.is_dir():
                raise ArtifactIntegrityError("artifact directory is missing or invalid")
            if not candidate.resolve(strict=True).is_relative_to(self.root):
                raise ArtifactIntegrityError("artifact path escaped the configured root")
            directory = candidate
        return key, directory / segments[-1]

    def _verify_file(self, target: Path, expected: StoredBlob) -> bytes:
        if target.is_symlink() or not target.is_file():
            raise ArtifactIntegrityError("artifact target is not a regular file")
        content = target.read_bytes()
        if len(content) != expected.byte_size or _content_hash(content) != expected.content_hash:
            raise ArtifactIntegrityError("artifact content does not match its immutable reference")
        return content

    def put_bytes(self, content: bytes, *, expected_hash: str | None = None) -> StoredBlob:
        if not isinstance(content, bytes):
            raise TypeError("artifact content must be bytes")
        actual_hash = _content_hash(content)
        if expected_hash is not None and actual_hash != expected_hash:
            raise ArtifactIntegrityError("artifact content does not match expected_hash")

        key, target = self._path_for(actual_hash, create_parents=True)
        reference = StoredBlob(actual_hash, len(content), key)
        if target.exists() or target.is_symlink():
            self._verify_file(target, reference)
            return reference

        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as temporary:
                temporary_path = Path(temporary.name)
                os.chmod(temporary_path, 0o600)
                temporary.write(content)
                temporary.flush()
                os.fsync(temporary.fileno())
            try:
                os.link(temporary_path, target)
            except FileExistsError:
                self._verify_file(target, reference)
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
        return reference

    def get_bytes(self, blob: StoredBlob) -> bytes:
        expected_key, target = self._path_for(blob.content_hash, create_parents=False)
        if blob.storage_key != expected_key:
            raise ArtifactIntegrityError("artifact storage key does not match its content hash")
        return self._verify_file(target, blob)

    def put_json(self, value: Any, *, expected_hash: str | None = None) -> StoredBlob:
        content = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return self.put_bytes(content, expected_hash=expected_hash)

    def get_json(self, blob: StoredBlob) -> Any:
        return json.loads(self.get_bytes(blob))
