"""Run-bound evidence persisted through the existing immutable artifact store."""

from collections.abc import Mapping, Sequence
from uuid import UUID

from tradingagents.contracts import ArtifactKind, EvidenceGraph
from tradingagents.platform.artifacts import ArtifactService

from .evidence import EvidenceGraphBuilder


class EvidenceGraphService:
    def __init__(self, artifacts: ArtifactService):
        self.artifacts = artifacts
        self.repository = artifacts.repository

    def create(self, *, owner_id: UUID, run_id: UUID, material_claims: Mapping[str, Sequence[UUID]]):
        run = self.repository.get_run(run_id, owner_id)
        if run is None:
            raise ValueError("run not found")
        used = {key for keys in material_claims.values() for key in keys}
        if not used <= set(run.snapshot_ids):
            raise ValueError("evidence source is not bound to this run")
        snapshots = []
        for snapshot_id in sorted(used, key=str):
            snapshot = self.repository.get_snapshot(snapshot_id)
            if snapshot is None or snapshot.instrument_id != run.instrument_id:
                raise ValueError("evidence source instrument does not match the run")
            snapshots.append(snapshot)
        graph = EvidenceGraphBuilder().build(
            run_id=run_id, as_of=run.analysis_as_of,
            snapshots=snapshots, material_claims=material_claims,
        )
        return self.artifacts.create(
            artifact_id=graph.graph_id, owner_id=owner_id,
            kind=ArtifactKind.DECISION_EVIDENCE, media_type="application/json",
            content=graph.model_dump_json().encode(), run_id=run_id,
            instrument_id=run.instrument_id, created_at=run.created_at,
        )

    def read(self, artifact_id: UUID, owner_id: UUID) -> EvidenceGraph | None:
        result = self.artifacts.read(artifact_id, owner_id)
        if result is None:
            return None
        manifest, content = result
        if manifest.kind is not ArtifactKind.DECISION_EVIDENCE:
            raise ValueError("artifact is not decision evidence")
        graph = EvidenceGraph.model_validate_json(content)
        if graph.graph_id != manifest.artifact_id or graph.run_id != manifest.run_id:
            raise ValueError("evidence artifact context mismatch")
        run = self.repository.get_run(graph.run_id, owner_id)
        if run is None or graph.as_of != run.analysis_as_of:
            raise ValueError("evidence run context mismatch")
        return graph
