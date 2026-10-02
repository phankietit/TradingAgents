"""Native in-process saver with restricted synchronous commit acknowledgements.

Internal prerequisite, not wired to worker/API/CLI. Call graph with durability
"sync": LangGraph's default async durability does not fence node advancement.
Raw native messages exist only in ephemeral InMemorySaver; commit sees codec
bytes only. A failed/ambiguous commit poisons this saver, never authorizes retry.
"""

import hashlib
from threading import RLock

from langgraph.checkpoint.memory import InMemorySaver

from .checkpoint_store import CheckpointCommit


class CheckpointCommitError(ValueError):
    """Fixed error without checkpoint contents or callback exception text."""


class CommittedSnapshotSaver(InMemorySaver):
    def __init__(self, *, codec, commit):
        super().__init__()
        self.codec = codec
        self.commit = commit
        self._commit_lock = RLock()
        self._failed = False

    def _check(self):
        if self._failed:
            raise CheckpointCommitError("snapshot checkpoint commit requires review")

    def _persist(self, config):
        try:
            # Native put_writes receives invocation-only configurable fields
            # (task routing/callback helpers), not a persisted checkpoint config.
            # Address the tuple with only native checkpoint identifiers; codec
            # still strictly validates all state/control/metadata contents.
            fields = config["configurable"]
            address = {"configurable": {"thread_id": fields["thread_id"],
                       "checkpoint_ns": fields.get("checkpoint_ns", ""),
                       "checkpoint_id": fields["checkpoint_id"]}}
            value = super().get_tuple(address)
            raw = self.codec.encode(value)
            receipt = self.commit(raw)
            if (type(receipt) is not CheckpointCommit or receipt.sequence < 1
                    or receipt.content_hash != hashlib.sha256(raw).hexdigest()):
                raise ValueError("invalid acknowledgement")
        except Exception:
            self._failed = True
            raise CheckpointCommitError("snapshot checkpoint commit requires review") from None

    def put(self, config, checkpoint, metadata, new_versions):
        with self._commit_lock:
            self._check()
            try:
                saved = super().put(config, checkpoint, metadata, new_versions)
                self._persist(saved)
                return saved
            except Exception:
                self._failed = True
                raise CheckpointCommitError("snapshot checkpoint commit requires review") from None

    def put_writes(self, config, writes, task_id, task_path=""):
        with self._commit_lock:
            self._check()
            try:
                super().put_writes(config, writes, task_id, task_path)
                self._persist(config)
            except Exception:
                self._failed = True
                raise CheckpointCommitError("snapshot checkpoint commit requires review") from None

    def get_tuple(self, config):
        with self._commit_lock:
            self._check()
            return super().get_tuple(config)

    def list(self, config, *, filter=None, before=None, limit=None):
        with self._commit_lock:
            self._check()
            yield from super().list(config, filter=filter, before=before, limit=limit)
