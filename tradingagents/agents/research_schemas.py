"""Snapshot-mode schemas; legacy CLI output contracts remain unchanged."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    FiniteFloat,
    create_model,
    field_validator,
    model_validator,
)

from tradingagents.agents.schemas import (
    DecisionEvidenceClaim,
    PortfolioDecision,
    ResearchPlan,
    TraderProposal,
)

Text = Annotated[str, Field(min_length=1, max_length=20000)]


class LocalizedResearchReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    en: Text = Field(description="Complete English research report in readable Markdown: outlook, evidence, opposing case, risks, invalidation, coverage and horizon. No sizing or execution.")
    vi: Text = Field(description="Faithful professional Vietnamese translation of en. Preserve all numbers, symbols, dates and units verbatim, using the same number formatting. No new conclusions.")

    @model_validator(mode="after")
    def preserve_numbers(self):
        from tradingagents.platform.analysis.research_validation import number_tokens

        if number_tokens(self.en) != number_tokens(self.vi):
            raise ValueError("localized reports must preserve numeric tokens")
        return self


class ObservedNumber(BaseModel):
    model_config = ConfigDict(extra="forbid")
    snapshot_id: UUID
    fact_id: str = Field(min_length=1, max_length=200)
    value: FiniteFloat
    decimal_places: int = Field(ge=0, le=8,
        description="Displayed rounding precision. Do not change units or convert percentages to ratios.")

# Keep provider tool names stable, while making the web decision's required
# fields agree with the strict platform consumer instead of silently dropping
# an otherwise parsed PortfolioDecision during mapping.
SnapshotPortfolioDecision = create_model(
    "PortfolioDecision", __base__=PortfolioDecision,
    confidence=(float, Field(ge=0, le=1, allow_inf_nan=False,
        description="Required uncalibrated assessment of evidence strength, not probability of profit. Do not fabricate certainty.")),
    risks=(tuple[Text, ...], Field(min_length=1, max_length=30)),
    invalidation_conditions=(tuple[Text, ...], Field(min_length=1, max_length=30)),
    investment_thesis=(Text, Field(description="Evidence-grounded research thesis with explicit coverage limitations.")),
    executive_summary=(Text, Field(description="Research outlook, strongest evidence, main uncertainty and horizon. No orders, allocations or sizing.")),
    rating=(PortfolioDecision.model_fields["rating"].annotation,
        Field(description="Research outlook only: Buy / Overweight / Hold / Underweight / Sell. Never an order or allocation.")),
    localized_report=(LocalizedResearchReport | None, Field(default=None,
        description="Required when bilingual output is requested; both languages express the same evidence and uncertainty.")),
    observed_numbers=(tuple[ObservedNumber, ...], Field(default=(), max_length=100,
        description="For each observed quantitative fact used in the final report, cite its exact snapshot_id and fact_id from verified fact_catalog, with value and rounding. Never create a fact_id.")),
)
# New generation is canonical English only. The historical schema above remains
# readable; localization is a separate, number-protected presentation stage.
CanonicalSnapshotDecision = create_model(
    "PortfolioDecision", __base__=SnapshotPortfolioDecision,
    localized_report=(Literal[None], Field(default=None,
        description="Must be null. A separate protected translation stage handles presentation.")),
)


class QuantityBinding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str = Field(pattern=r"^Q[A-Z]{1,5}$")
    snapshot_id: UUID
    fact_id: str = Field(min_length=1, max_length=200)
    decimal_places: int = Field(default=2, ge=0, le=8)


def _bound_financial_text(value):
    from tradingagents.platform.analysis.research_validation import unsupported_financial_numbers

    if value is not None and unsupported_financial_numbers(value, ()):
        raise ValueError("Every monetary or percent quantity must use a quantity binding, including approximations and conditions")
    return value


class BoundEvidenceClaim(DecisionEvidenceClaim):
    claim: Text = Field(description="Financial prose using {{QA}} quantity placeholders, never literal monetary amounts or percentages, including approximate or conditional quantities.")
    _bound_claim = field_validator("claim")(_bound_financial_text)


SnapshotReportDraft = create_model(
    "PortfolioDecision", __base__=CanonicalSnapshotDecision,
    __validators__={"bound_summary": field_validator("executive_summary", "time_horizon")(_bound_financial_text)},
    investment_thesis=(tuple[BoundEvidenceClaim, ...], Field(min_length=1, max_length=12,
        description="Evidence-linked thesis paragraphs, including strongest opposing case and coverage. Each paragraph carries supplied snapshot IDs.")),
    risks=(tuple[BoundEvidenceClaim, ...], Field(min_length=1, max_length=30)),
    invalidation_conditions=(tuple[BoundEvidenceClaim, ...], Field(min_length=1, max_length=30)),
    evidence_claims=(tuple[DecisionEvidenceClaim, ...], Field(default=(), max_length=0,
        description="Leave empty. Application compiles exact citations from thesis, risk and invalidation objects; do not duplicate prose.")),
    quantity_bindings=(tuple[QuantityBinding, ...], Field(default=(), max_length=100,
        description="Use {{QA}}, {{QB}}, etc. in prose. Bind each placeholder to an immutable fact ID; the application resolves and rounds its value. Never supply numeric values yourself.")),
    observed_numbers=(tuple[ObservedNumber, ...], Field(default=(), max_length=0,
        description="Leave empty. Application-generated from quantity_bindings.")),
    price_target=(Literal[None], Field(default=None)),
)
SnapshotResearchPlan = create_model(
    "ResearchPlan", __base__=ResearchPlan,
    strategic_actions=(Text, Field(description="Conditional research scenarios and evidence to monitor. No quantities, sizing, allocation percentages or derivative strategies.")),
)
SnapshotTraderProposal = create_model(
    "TraderProposal", __base__=TraderProposal,
    position_sizing=(Literal[None], Field(default=None, description="Must be null: deterministic portfolio policy owns sizing.")),
)
