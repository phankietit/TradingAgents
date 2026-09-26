"""Owner-scoped evaluation receipts reconstructed from immutable persisted sources."""

import hashlib
import json
from uuid import UUID, uuid5

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from tradingagents.contracts import (
    ArtifactKind,
    HistoricalEvaluation,
    NormalizedTimeSeries,
    RunStatus,
)
from tradingagents.platform.analysis.snapshots import load_snapshot_context

from .calendar import EvaluationSessionWindow
from .outcomes import calendar_snapshot_outcome
from .service import HistoricalEvaluationService, is_scorable_decision


class EvaluationCellSelection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    decision_id: UUID
    asset_snapshot_id: UUID
    benchmark_snapshot_id: UUID
    holding_sessions: int = Field(ge=1, le=2520, strict=True)


class EvaluationReplayRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    owner_id: UUID
    evaluated_at: AwareDatetime
    cells: tuple[EvaluationCellSelection, ...] = Field(min_length=1, max_length=1000)


class EvaluationReplayReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    request: EvaluationReplayRequest
    evaluation: HistoricalEvaluation
    calendars: dict[str, tuple[EvaluationSessionWindow, EvaluationSessionWindow]]


class PersistedEvaluationService:
    def __init__(self, artifacts):
        self.artifacts = artifacts
        self.repository = artifacts.repository

    def _series(self, snapshot_id, owner_id):
        snapshot = self.repository.get_snapshot(snapshot_id)
        artifact = self.repository.get_snapshot_artifact(snapshot_id, owner_id)
        if (snapshot is None or artifact is None or snapshot.content_hash != artifact.content_hash
                or snapshot.instrument_id != artifact.instrument_id):
            raise ValueError("owner outcome source unavailable")
        loaded = self.artifacts.read(artifact.artifact_id, owner_id)
        if loaded is None or "sha256:" + hashlib.sha256(loaded[1]).hexdigest() != snapshot.content_hash:
            raise ValueError("outcome payload integrity failure")
        return snapshot, NormalizedTimeSeries.model_validate_json(loaded[1])

    def reconstruct(self, request):
        request = EvaluationReplayRequest.model_validate(request.model_dump())
        cells = tuple(sorted(request.cells, key=lambda cell: str(cell.decision_id)))
        if len({cell.decision_id for cell in cells}) != len(cells):
            raise ValueError("duplicate evaluation decisions")
        request = request.model_copy(update={"cells": cells})
        decisions, observations, calendars, symbols, benchmarks = [], [], {}, set(), set()
        for selection in cells:
            decision = self.repository.get_decision(selection.decision_id, request.owner_id)
            if decision is None:
                raise ValueError("owner evaluation decision unavailable")
            run = self.repository.get_run(decision.run_id, request.owner_id)
            if run is None or run.decision_inputs is None or run.status is not RunStatus.SUCCEEDED:
                raise ValueError("evaluation requires snapshot-attested decision inputs")
            load_snapshot_context(self.artifacts, run, run.decision_inputs.snapshots_by_analyst)
            instrument = self.repository.get_instrument(decision.instrument_id)
            asset = self._series(selection.asset_snapshot_id, request.owner_id)
            benchmark = self._series(selection.benchmark_snapshot_id, request.owner_id)
            benchmark_instrument = self.repository.get_instrument(benchmark[0].instrument_id)
            if instrument is None or benchmark_instrument is None:
                raise ValueError("evaluation instrument unavailable")
            decisions.append(decision)
            symbols.add(instrument.canonical_symbol)
            benchmarks.add(benchmark_instrument.canonical_symbol)
            if not is_scorable_decision(decision):
                continue
            observation, windows = calendar_snapshot_outcome(decision=decision, instrument=instrument,
                benchmark_instrument=benchmark_instrument, asset=asset, benchmark=benchmark,
                holding_sessions=selection.holding_sessions, evaluated_at=request.evaluated_at)
            observations.append(observation)
            calendars[str(decision.decision_id)] = windows
        if len(benchmarks) != 1:
            raise ValueError("one evaluation requires one benchmark")
        config_hash = "sha256:" + hashlib.sha256(json.dumps(request.model_dump(mode="json"),
            sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        result = HistoricalEvaluationService().build(decisions=tuple(decisions), observations=tuple(observations),
            universe=tuple(sorted(symbols)), benchmark=next(iter(benchmarks)), config_hash=config_hash,
            created_at=request.evaluated_at)
        result = result.model_copy(update={"reproducible": True})
        return EvaluationReplayReceipt(request=request, evaluation=result, calendars=calendars)

    def create(self, request):
        receipt = self.reconstruct(request)
        artifact_id = uuid5(request.owner_id, f"evaluation:{receipt.evaluation.input_hash}")
        return self.artifacts.create(artifact_id=artifact_id, owner_id=request.owner_id,
            kind=ArtifactKind.HISTORICAL_EVALUATION, media_type="application/json",
            content=receipt.model_dump_json().encode(), created_at=request.evaluated_at)

    def verify(self, artifact_id, owner_id):
        loaded = self.artifacts.read(artifact_id, owner_id)
        if loaded is None:
            raise ValueError("owner evaluation receipt unavailable")
        manifest, payload = loaded
        if manifest.kind is not ArtifactKind.HISTORICAL_EVALUATION:
            raise ValueError("artifact is not an evaluation receipt")
        receipt = EvaluationReplayReceipt.model_validate_json(payload)
        if receipt.request.owner_id != owner_id or self.reconstruct(receipt.request) != receipt:
            raise ValueError("evaluation replay does not match immutable receipt")
        return receipt
