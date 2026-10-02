"""Internal original-context recorder, not an owner continuation endpoint."""

import re
from dataclasses import dataclass
from uuid import UUID

from tradingagents.contracts import RunManifest
from tradingagents.contracts.runs import ResearchExecutionLimits

from .checkpoint_codec import MAX_CHECKPOINT_BYTES, SnapshotCheckpointCodec
from .checkpoint_saver import CommittedSnapshotSaver
from .client_binding import build_initialized_graph_fingerprint
from .observer import ResearchObserver
from .recovery_fingerprint import RecoveryFingerprintError


@dataclass(frozen=True, repr=False)
class SnapshotRecorder:
    """Trusted caller supplies original context and parent-fenced commit.

    No field is browser input or consent. Expected fingerprint must match actual
    graph/client/source construction before any invocation; no implicit fallback.
    Optional restricted bytes restore a trusted checkpoint; no field grants
    consent or resets the caller's existing observer/allowance.
    """

    owner_id: UUID
    run: RunManifest
    expected_fingerprint: str
    commit: object
    portfolio_snapshot: object = None
    policy: object = None
    risk_snapshots: tuple = ()
    restore_checkpoint: bytes | None = None

    def __post_init__(self):
        try:
            run = RunManifest.model_validate(self.run.model_dump(warnings=False))
            if (type(self.owner_id) is not UUID or run.owner_id != self.owner_id
                    or type(self.expected_fingerprint) is not str
                    or re.fullmatch(r"[0-9a-f]{64}", self.expected_fingerprint) is None
                    or not callable(self.commit)
                    or (self.restore_checkpoint is not None and (
                        type(self.restore_checkpoint) is not bytes
                        or not 0 < len(self.restore_checkpoint) <= MAX_CHECKPOINT_BYTES))):
                raise ValueError()
            object.__setattr__(self, "run", run)
        except (ValueError, TypeError, AttributeError):
            raise RecoveryFingerprintError("invalid snapshot recorder setup") from None

    def prepare(self, *, request, graph, base_config):
        limits = self.run.execution_limits or ResearchExecutionLimits()
        observer = request.execution_observer
        if type(observer) is ResearchObserver:
            if (observer.max_seconds != limits.wall_seconds or observer.max_calls != limits.model_calls):
                raise RecoveryFingerprintError("snapshot recorder allowance requires review")
            # Existing start/clock, never a fresh observer or budget reset.
            observer.remaining_seconds()
        else:
            from .supervision import _Bridge

            if type(observer) is not _Bridge:
                raise RecoveryFingerprintError("snapshot recorder allowance requires review")
            observer.validate_recording_allowance(wall_seconds=limits.wall_seconds,
                model_calls=limits.model_calls, fingerprint=self.expected_fingerprint,
                thread_id=str(self.run.run_id))
        actual = build_initialized_graph_fingerprint(graph=graph, owner_id=self.owner_id,
            run=self.run, request=request, base_config=base_config,
            portfolio_snapshot=self.portfolio_snapshot, policy=self.policy,
            risk_snapshots=self.risk_snapshots)
        if actual != self.expected_fingerprint:
            raise RecoveryFingerprintError("snapshot recorder identity requires review")
        codec = SnapshotCheckpointCodec(fingerprint=actual, nodes=graph.workflow.nodes)
        saver = CommittedSnapshotSaver(codec=codec, commit=self.commit)
        if self.restore_checkpoint is not None:
            saver.restore(self.restore_checkpoint, expected_thread_id=str(self.run.run_id))
        return {"checkpoint_saver": saver, "checkpoint_thread_id": str(self.run.run_id),
                **({"checkpoint_resume": True} if self.restore_checkpoint is not None else {})}
