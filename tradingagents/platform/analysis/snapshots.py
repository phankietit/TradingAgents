"""Validated immutable evidence inputs for a tool-free graph run."""

import hashlib
import json
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from tradingagents.contracts import DataQualityStatus, SnapshotManifest


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

    def reports(self, instrument_id: UUID, analysts: tuple[str, ...]) -> dict[str, str]:
        # Frozen Pydantic models can still contain mutable dictionaries.
        validated = SnapshotAnalysisContext.model_validate(self.model_dump())
        if set(validated.by_analyst) != set(analysts):
            raise ValueError("snapshot roles must exactly cover selected analysts")
        if sum(len(s.payload) for sources in validated.by_analyst.values() for s in sources) > 2_000_000:
            raise ValueError("snapshot prompt payload exceeds bounded input size")
        reports = {}
        for role, sources in validated.by_analyst.items():
            if not 1 <= len(sources) <= 16 or len({s.manifest.snapshot_id for s in sources}) != len(sources):
                raise ValueError("snapshot role requires nonempty unique sources")
            for source in sources:
                manifest = source.manifest
                if (manifest.instrument_id != instrument_id
                        or manifest.quality_status is not DataQualityStatus.OK
                        or manifest.source_end is None
                        or manifest.source_end > manifest.retrieved_at
                        or manifest.retrieved_at > validated.as_of
                        or manifest.as_of > validated.as_of):
                    raise ValueError("analysis source is not point-in-time eligible")
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
    context = SnapshotAnalysisContext(as_of=run.analysis_as_of, by_analyst=result)
    context.reports(run.instrument_id, run.selected_analysts)
    return context
