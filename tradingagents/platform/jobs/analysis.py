"""Durable research handler; unattested legacy graph data cannot authorize readiness."""

import json
from datetime import UTC
from uuid import uuid5

from tradingagents.contracts import ArtifactKind, DataQualityStatus
from tradingagents.platform.analysis import (
    AnalysisEngine,
    AnalysisRequest,
    DecisionCandidateFactory,
)
from tradingagents.platform.artifacts import ArtifactService
from tradingagents.platform.persistence import PlatformRepository


class AnalysisJobHandler:
    """Run the existing graph outside DB transactions, persist one immutable result.

    Legacy tools do not yet attest every read to a run-bound snapshot. Retain
    useful research but withhold approval-ready decisions until that evidence
    exists. A free-text fallback is never parsed into a structured decision.
    """

    def __init__(self, database, artifact_store, *, engine=None, prompt_version="1"):
        self.database = database
        self.artifact_store = artifact_store
        self.engine = engine or AnalysisEngine()
        self.prompt_version = prompt_version

    def __call__(self, job, context):
        context.raise_if_cancelled()
        context.heartbeat()
        report_id = uuid5(job.run_id, "analysis-report-v1")
        decision_id = uuid5(job.run_id, "decision-v1")
        with self.database.session() as session:
            repository = PlatformRepository(session, artifact_store=self.artifact_store)
            run = repository.get_run(job.run_id, job.owner_id)
            if run is None or run.prompt_version != self.prompt_version:
                raise ValueError("run or supported prompt version unavailable")
            expected_payload = {
                "instrument_id": str(run.instrument_id),
                "analysis_as_of": run.analysis_as_of.astimezone(UTC).isoformat(),
                "selected_analysts": list(run.selected_analysts),
                "config_hash": run.config_hash,
            }
            if job.payload != expected_payload:
                raise ValueError("analysis job does not match its immutable run")
            artifacts = ArtifactService(self.artifact_store, repository)
            existing = artifacts.read(report_id, job.owner_id)
            candidate = repository.get_decision(decision_id, job.owner_id)
            if existing is not None and candidate is not None:
                if existing[0].run_id != run.run_id or candidate.run_id != run.run_id:
                    raise ValueError("analysis output context mismatch")
                return (report_id,)
            if existing is not None or candidate is not None:
                raise ValueError("incomplete analysis output transaction")
            instrument = repository.get_instrument(run.instrument_id)
            if instrument is None:
                raise ValueError("run instrument unavailable")
        result = self.engine.analyze(AnalysisRequest(
            instrument=instrument, analysis_date=run.analysis_as_of.date(),
            selected_analysts=run.selected_analysts,
            config_overrides={"llm_provider": run.llm_provider,
                              "quick_think_llm": run.quick_model,
                              "deep_think_llm": run.deep_model},
        ))
        context.raise_if_cancelled()
        context.heartbeat()  # Reject a lost/expired lease before publishing.
        raw = result.decision_payload.model_dump(mode="json") if result.decision_payload else {}
        candidate = DecisionCandidateFactory().build(
            decision_id=decision_id, raw_output=raw, run_id=run.run_id,
            owner_id=run.owner_id, instrument_id=run.instrument_id,
            as_of=run.analysis_as_of, evidence=(), data_quality=DataQualityStatus.UNAVAILABLE,
        )
        # Deliberately exclude raw graph messages, which may contain provider
        # objects or unrelated prompt context. Preserve the research artifact.
        report = {
            "run_id": str(run.run_id), "decision_id": str(decision_id),
            "profile": result.profile_name, "reference_only": result.reference_only,
            "selected_analysts": result.selected_analysts,
            "narrative": result.final_state.get("final_trade_decision", result.narrative_signal),
            "structured_narrative": raw or None,
            "snapshot_attestation": "UNVERIFIED",
        }
        with context.publication_session() as session:
            repository = PlatformRepository(session, artifact_store=self.artifact_store)
            ArtifactService(self.artifact_store, repository).create(
                artifact_id=report_id, owner_id=run.owner_id, run_id=run.run_id,
                instrument_id=run.instrument_id, kind=ArtifactKind.ANALYSIS_REPORT,
                media_type="application/json", created_at=run.created_at,
                content=json.dumps(report, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(),
            )
            repository.add_decision(candidate)
        return (report_id,)
