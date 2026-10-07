"""Owner-readable original recording inputs, not risk approval."""

from dataclasses import dataclass

from tradingagents.contracts import (
    ArtifactKind,
    DataQualityStatus,
    PolicyContract,
    PortfolioSnapshot,
    RunManifest,
)
from tradingagents.platform.analysis.snapshots import AnalysisSnapshot


@dataclass(frozen=True, repr=False)
class OriginalRecordingSources:
    portfolio_snapshot: PortfolioSnapshot | None
    policy: PolicyContract | None
    risk_snapshots: tuple[AnalysisSnapshot, ...]


def load_original_recording_sources(*, repository, artifacts, run):
    """Read original owner rows/bytes only; never current/latest or LLM floats.

    The caller must authenticate the run/job before calling this loader. Risk
    coverage, window, correlations and policy pass/fail remain the existing
    deterministic risk engine's responsibility, never a recording permission.
    """
    try:
        run = RunManifest.model_validate(run.model_dump(warnings=False))
        inputs = run.decision_inputs
        if inputs is None or artifacts.repository is not repository:
            raise ValueError()
        book, policy = None, None
        if inputs.portfolio_snapshot_id is not None:
            book = repository.get_portfolio_snapshot(inputs.portfolio_snapshot_id, run.owner_id)
            policy = repository.get_policy(inputs.policy_id, inputs.policy_version, run.owner_id)
            if book is None or policy is None:
                raise ValueError()
            book = PortfolioSnapshot.model_validate(book.model_dump(warnings=False))
            policy = PolicyContract.model_validate(policy.model_dump(warnings=False))
            if (book.portfolio_id != inputs.portfolio_snapshot_id or book.owner_id != run.owner_id
                    or book.as_of != run.analysis_as_of or policy.owner_id != run.owner_id
                    or policy.policy_id != inputs.policy_id or policy.policy_version != inputs.policy_version
                    or policy.effective_at > run.analysis_as_of):
                raise ValueError()
        risks = []
        for snapshot_id in inputs.risk_snapshot_ids:
            if snapshot_id not in run.snapshot_ids:
                raise ValueError()
            manifest = repository.get_snapshot(snapshot_id)
            artifact = repository.get_snapshot_artifact(snapshot_id, run.owner_id)
            if (manifest is None or artifact is None or manifest.snapshot_id != snapshot_id
                    or artifact.snapshot_id != snapshot_id or artifact.owner_id != run.owner_id
                    or artifact.kind is not ArtifactKind.SNAPSHOT_PAYLOAD
                    or artifact.media_type != "application/json"
                    or artifact.content_hash != manifest.content_hash
                    or artifact.instrument_id != manifest.instrument_id
                    or manifest.quality_status is not DataQualityStatus.OK
                    or manifest.as_of > run.analysis_as_of or manifest.retrieved_at > run.analysis_as_of
                    or manifest.source_end is None or manifest.source_end > manifest.retrieved_at):
                raise ValueError()
            loaded = artifacts.read(artifact.artifact_id, run.owner_id)
            if (loaded is None or loaded[0] != artifact or type(loaded[1]) is not bytes
                    or len(loaded[1]) != artifact.byte_size):
                raise ValueError()
            risks.append(AnalysisSnapshot(manifest=manifest, payload=loaded[1].decode("utf-8")))
        return OriginalRecordingSources(book, policy, tuple(risks))
    except Exception:
        # Do not expose raw DB/storage/source exceptions or private inputs.
        raise ValueError("original recording sources require review") from None
