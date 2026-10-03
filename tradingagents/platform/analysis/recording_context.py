"""Bounded private transfer of trusted original inputs, never browser consent."""

import json
from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from tradingagents.contracts import PolicyContract, PortfolioSnapshot, RunManifest
from tradingagents.contracts.runs import RunStatus

from .profiles import resolve_analysis_profile, select_analysts
from .recovery_fingerprint import RecoveryFingerprintError, _no_credentials
from .snapshots import AnalysisSnapshot, SnapshotAnalysisContext

MAX_RECORDING_CONTEXT_BYTES = 4_000_000


def _unique_fields(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError()
        result[key] = value
    return result


def _invalid_constant(value):
    raise ValueError()


class _Inputs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    owner_id: UUID = Field(repr=False)
    run: RunManifest = Field(repr=False)
    expected_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$", repr=False)
    portfolio_snapshot: PortfolioSnapshot | None = Field(default=None, repr=False)
    policy: PolicyContract | None = Field(default=None, repr=False)
    risk_snapshots: tuple[AnalysisSnapshot, ...] = Field(default=(), max_length=100, repr=False)


class _LinkedInputs(_Inputs):
    format: Literal["linked-snapshot-recording-v1"]
    execution_id: UUID = Field(repr=False)
    source_job_id: UUID = Field(repr=False)
    source_job_hash: str = Field(pattern=r"^[0-9a-f]{64}$", repr=False)
    source_run_hash: str = Field(pattern=r"^[0-9a-f]{64}$", repr=False)
    observation_hash: str = Field(pattern=r"^[0-9a-f]{64}$", repr=False)
    attempt: int = Field(strict=True, ge=2, le=1_000_000)
    checkpoint_record_id: UUID = Field(repr=False)
    checkpoint_hash: str = Field(pattern=r"^[0-9a-f]{64}$", repr=False)


@dataclass(frozen=True, repr=False)
class SnapshotRecordingInputs:
    """JSON-only internal envelope; no callable, SDK, DB, lease or credentials.

    Authenticated source loading and initialized-client attestation remain caller
    obligations. This has no restore path and grants no continuation allowance.
    Source prose is data, not a universal secret-detection guarantee.
    """

    raw: bytes

    @classmethod
    def create(cls, **values):
        try:
            policy = values.get("policy")
            if policy is not None:
                _no_credentials(policy.parameters)
                # Reject objects/nonfinite numbers rather than letting a model
                # serializer normalize them into a different research policy.
                json.dumps(policy.parameters, allow_nan=False)
            model = _LinkedInputs if cls is LinkedSnapshotRecordingInputs else _Inputs
            data = model.model_validate(values).model_dump_json(warnings=False).encode("utf-8")
            result = cls(data)
            result.read()
            return result
        except (ValueError, TypeError, AttributeError, RecursionError):
            raise RecoveryFingerprintError("invalid recording context") from None

    def read(self):
        return self._read(_Inputs, terminal=False)

    def _read(self, model, *, terminal):
        try:
            if type(self.raw) is not bytes or not 0 < len(self.raw) <= MAX_RECORDING_CONTEXT_BYTES:
                raise ValueError()
            json.loads(self.raw, object_pairs_hook=_unique_fields, parse_constant=_invalid_constant)
            value = model.model_validate_json(self.raw)
            run = value.run
            declared = run.decision_inputs
            if run.owner_id != value.owner_id or declared is None:
                raise ValueError()
            if terminal:
                from .continuation import _digest

                if (type(value) is not _LinkedInputs or run.status not in {RunStatus.FAILED, RunStatus.CANCELLED}
                        or run.completed_at is None or _digest(run.model_dump(mode="json")) != value.source_run_hash):
                    raise ValueError()
            elif (run.error_message is not None or run.error_code is not None or run.completed_at is not None):
                raise ValueError()
            book, policy = value.portfolio_snapshot, value.policy
            if declared.portfolio_snapshot_id is None:
                if book is not None or policy is not None:
                    raise ValueError()
            elif (book is None or policy is None or book.owner_id != value.owner_id
                    or policy.owner_id != value.owner_id or book.as_of != run.analysis_as_of
                    or book.portfolio_id != declared.portfolio_snapshot_id
                    or policy.policy_id != declared.policy_id
                    or policy.policy_version != declared.policy_version
                    or policy.effective_at > run.analysis_as_of):
                raise ValueError()
            if policy is not None:
                _no_credentials(policy.parameters)
            risk_ids = tuple(source.manifest.snapshot_id for source in value.risk_snapshots)
            if len(set(risk_ids)) != len(risk_ids) or set(risk_ids) != set(declared.risk_snapshot_ids):
                raise ValueError()
            for source in value.risk_snapshots:
                if (source.manifest.as_of > run.analysis_as_of
                        or source.manifest.retrieved_at > run.analysis_as_of
                        or source.manifest.quality_status.value != "OK"):
                    raise ValueError()
            return value
        except (ValueError, TypeError, AttributeError, RecursionError):
            raise RecoveryFingerprintError("invalid recording context") from None

    def validate_request(self, request):
        try:
            value = self.read()
            run = value.run
            analysts = select_analysts(resolve_analysis_profile(request.instrument), request.selected_analysts)
            if (request.snapshot_context is None or run.instrument_id != request.instrument.instrument_id
                    or run.analysis_as_of.date() != request.analysis_date or analysts != run.selected_analysts
                    or (request.portfolio is None) != (value.portfolio_snapshot is None)):
                raise ValueError()
            sources = SnapshotAnalysisContext.model_validate(request.snapshot_context.model_dump(warnings=False))
            sources.reports(run.instrument_id, analysts)
            declared = run.decision_inputs
            if (sources.as_of != run.analysis_as_of
                    or sources.source_max_age_seconds != declared.source_max_age_seconds
                    or {role: tuple(source.manifest.snapshot_id for source in items)
                        for role, items in sources.by_analyst.items()} != declared.snapshots_by_analyst):
                raise ValueError()
            return value
        except (ValueError, TypeError, AttributeError, KeyError, RecursionError):
            raise RecoveryFingerprintError("recording request requires review") from None


@dataclass(frozen=True, repr=False)
class LinkedSnapshotRecordingInputs(SnapshotRecordingInputs):
    """Private terminal original context, never portable consent/lease authority.

    The parent must reload/fence the source and consume dispatch before spawn.
    Error/completion fields remain unchanged; the ordinary context still rejects
    terminal manifests. No DB, lease nonce, session or callable enters these bytes.
    """

    def read(self):
        return self._read(_LinkedInputs, terminal=True)


def read_child_recording_inputs(raw, *, checkpoint_options, restore_checkpoint):
    """Reviewed private child transport, not a browser-selectable context mode."""
    if "linked_execution_id" in checkpoint_options:
        if restore_checkpoint is None:
            raise RecoveryFingerprintError("invalid recording context")
        value = LinkedSnapshotRecordingInputs(raw).read()
        if str(value.execution_id) != checkpoint_options["linked_execution_id"]:
            raise RecoveryFingerprintError("invalid recording context")
        return LinkedSnapshotRecordingInputs(raw)
    return SnapshotRecordingInputs(raw)
