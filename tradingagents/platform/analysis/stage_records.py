"""Private immutable research fragments, never checkpoints or decisions.

Only role-owned reader text is retained. Messages, prompts, model reasoning,
tool payloads, arbitrary state and executable portfolio fields are excluded.
"""

from typing import Annotated, Literal
from uuid import UUID, uuid5

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from tradingagents.contracts import ArtifactKind
from tradingagents.contracts.base import ContentHash, NonEmptyText
from tradingagents.platform.analysis.observer import STAGES

STAGE_PATHS = {
    "Market Analyst": {"market_report": ("market_report",)},
    "Sentiment Analyst": {"sentiment_report": ("sentiment_report",)},
    "News Analyst": {"news_report": ("news_report",)},
    "Fundamentals Analyst": {"fundamentals_report": ("fundamentals_report",)},
    "Bull Researcher": {"argument": ("investment_debate_state", "current_response")},
    "Bear Researcher": {"argument": ("investment_debate_state", "current_response")},
    "Research Manager": {"investment_plan": ("investment_plan",)},
    "Trader": {"trader_investment_plan": ("trader_investment_plan",)},
    "Aggressive Analyst": {"argument": ("risk_debate_state", "current_aggressive_response")},
    "Conservative Analyst": {"argument": ("risk_debate_state", "current_conservative_response")},
    "Neutral Analyst": {"argument": ("risk_debate_state", "current_neutral_response")},
    "Portfolio Manager": {"research_conclusion": ("final_trade_decision",)},
    "Financial validation": {"research_conclusion": ("final_trade_decision",)},
    "Report presentation": {
        "report_en": ("structured_decision", "localized_report", "en"),
        "report_vi": ("structured_decision", "localized_report", "vi"),
    },
}


def stage_sections(stage, outputs):
    result = {}
    for label, path in STAGE_PATHS.get(stage, {}).items():
        value = outputs
        for component in path:
            value = value.get(component) if isinstance(value, dict) else None
        if isinstance(value, str) and value.strip():
            result[label] = value
    return result


class ResearchStageRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    run_id: UUID
    instrument_id: UUID
    analysis_as_of: AwareDatetime
    config_hash: ContentHash
    prompt_version: NonEmptyText
    snapshot_ids: tuple[UUID, ...]
    snapshot_attestation: Literal["PASS", "UNVERIFIED"]
    attempt: int = Field(ge=1)
    sequence: int = Field(ge=1)
    stage: str
    research_quality: Literal["unvalidated"] = "unvalidated"
    approval_eligible: Literal[False] = False
    # Reject oversized fragments; never silently truncate source or research.
    sections: dict[str, Annotated[str, Field(min_length=1, max_length=1_000_000)]] = Field(min_length=1, max_length=2)

    @model_validator(mode="after")
    def allowed_reader_fields(self):
        if self.stage not in STAGES or not set(self.sections) <= set(STAGE_PATHS[self.stage]):
            raise ValueError("unsupported research stage fields")
        return self


class ResearchStageService:
    def __init__(self, artifacts):
        self.artifacts = artifacts

    def persist(self, run, *, stage, outputs, attempt, sequence, snapshot_attestation):
        """Caller must use the job's lease/cancellation-fenced publication session."""
        if snapshot_attestation != ("PASS" if run.decision_inputs is not None else "UNVERIFIED"):
            raise ValueError("research stage attestation differs from run inputs")
        sections = stage_sections(stage, outputs)
        if not sections:
            return None
        record = ResearchStageRecord(run_id=run.run_id, instrument_id=run.instrument_id,
            analysis_as_of=run.analysis_as_of, config_hash=run.config_hash,
            prompt_version=run.prompt_version, snapshot_ids=run.snapshot_ids,
            snapshot_attestation=snapshot_attestation, stage=stage,
            attempt=attempt, sequence=sequence, sections=sections)
        return self.artifacts.create(owner_id=run.owner_id, run_id=run.run_id,
            instrument_id=run.instrument_id, kind=ArtifactKind.RESEARCH_STAGE,
            artifact_id=uuid5(run.run_id, f"research-stage-v1:{attempt}:{sequence}"),
            media_type="application/json", content=record.model_dump_json().encode("utf-8"))

    def read(self, artifact_id, owner_id):
        stored = self.artifacts.read(artifact_id, owner_id)
        if stored is None:
            return None
        manifest, content = stored
        if manifest.kind is not ArtifactKind.RESEARCH_STAGE:
            raise ValueError("not a research stage record")
        record = ResearchStageRecord.model_validate_json(content)
        run = self.artifacts.repository.get_run(record.run_id, owner_id)
        if (run is None or manifest.run_id != record.run_id
                or manifest.instrument_id != record.instrument_id
                or run.instrument_id != record.instrument_id
                or run.analysis_as_of != record.analysis_as_of
                or run.config_hash != record.config_hash
                or run.prompt_version != record.prompt_version
                or run.snapshot_ids != record.snapshot_ids
                or record.snapshot_attestation != ("PASS" if run.decision_inputs is not None else "UNVERIFIED")):
            raise ValueError("research stage context mismatch")
        return record
