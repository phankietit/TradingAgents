"""Validated immutable evidence inputs for a tool-free graph run."""

import hashlib
import json
from typing import Annotated
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from tradingagents.contracts import DataQualityStatus, SnapshotManifest


def snapshot_ineligibility(manifest: SnapshotManifest, instrument_id: UUID,
                          as_of, max_age_seconds: int) -> tuple[str, ...]:
    """Shared metadata gate; content integrity is independently checked on load."""
    reasons = []
    if manifest.instrument_id != instrument_id:
        reasons.append("instrument_mismatch")
    if manifest.quality_status is not DataQualityStatus.OK:
        reasons.append("quality_not_ok")
    if manifest.source_end is None:
        reasons.append("source_time_missing")
    elif manifest.source_end > manifest.retrieved_at:
        reasons.append("source_after_retrieval")
    if manifest.retrieved_at > as_of or manifest.as_of > as_of:
        reasons.append("not_available_at_analysis_time")
    if manifest.source_end is not None and (as_of - manifest.source_end).total_seconds() > max_age_seconds:
        reasons.append("stale")
    return tuple(reasons)


class AnalysisSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    manifest: SnapshotManifest
    payload: str = Field(min_length=1, max_length=2_000_000)

    @model_validator(mode="after")
    def verify_content(self):
        if "sha256:" + hashlib.sha256(self.payload.encode()).hexdigest() != self.manifest.content_hash:
            raise ValueError("analysis source hash mismatch")
        json.loads(self.payload)
        return self


class SnapshotAnalysisContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    as_of: AwareDatetime
    by_analyst: dict[str, tuple[AnalysisSnapshot, ...]]
    source_max_age_seconds: dict[str, Annotated[int, Field(ge=0, le=315360000)]]

    def reports(self, instrument_id: UUID, analysts: tuple[str, ...]) -> dict[str, str]:
        # Frozen Pydantic models can still contain mutable dictionaries.
        validated = SnapshotAnalysisContext.model_validate(self.model_dump())
        if set(validated.by_analyst) != set(analysts):
            raise ValueError("snapshot roles must exactly cover selected analysts")
        if set(validated.source_max_age_seconds) != set(analysts):
            raise ValueError("snapshot roles require explicit freshness limits")
        if sum(len(s.payload) for sources in validated.by_analyst.values() for s in sources) > 2_000_000:
            raise ValueError("snapshot prompt payload exceeds bounded input size")
        reports = {}
        for role, sources in validated.by_analyst.items():
            if not 1 <= len(sources) <= 16 or len({s.manifest.snapshot_id for s in sources}) != len(sources):
                raise ValueError("snapshot role requires nonempty unique sources")
            for source in sources:
                manifest = source.manifest
                reasons = snapshot_ineligibility(manifest, instrument_id, validated.as_of,
                                                validated.source_max_age_seconds[role])
                if reasons:
                    raise ValueError("analysis source is not point-in-time eligible: " + ", ".join(reasons))
            reports[role] = json.dumps([
                {"snapshot_id": str(s.manifest.snapshot_id),
                 "provenance": s.manifest.model_dump(mode="json"),
                 "data": json.loads(s.payload)} for s in sources
            ], sort_keys=True, ensure_ascii=False)
        return reports


def load_snapshot_context(artifacts, run, by_analyst):
    """Only owner-readable artifacts already bound to the run may enter prompts."""
    repository = artifacts.repository
    result = {}
    for role, ids in by_analyst.items():
        sources = []
        for snapshot_id in ids:
            if snapshot_id not in run.snapshot_ids:
                raise ValueError("analysis snapshot is not bound to run")
            manifest = repository.get_snapshot(snapshot_id)
            artifact = repository.get_snapshot_artifact(snapshot_id, run.owner_id)
            if (manifest is None or artifact is None or artifact.content_hash != manifest.content_hash
                    or artifact.instrument_id != manifest.instrument_id):
                raise ValueError("owner analysis snapshot is unavailable")
            loaded = artifacts.read(artifact.artifact_id, run.owner_id)
            if loaded is None:
                raise ValueError("owner analysis snapshot bytes are unavailable")
            sources.append(AnalysisSnapshot(manifest=manifest, payload=loaded[1].decode("utf-8")))
        result[role] = tuple(sources)
    context = SnapshotAnalysisContext(as_of=run.analysis_as_of, by_analyst=result,
        source_max_age_seconds=run.decision_inputs.source_max_age_seconds)
    context.reports(run.instrument_id, run.selected_analysts)
    return context
