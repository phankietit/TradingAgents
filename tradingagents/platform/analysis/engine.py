"""Platform adapter for the existing :class:`TradingAgentsGraph` runtime.

The adapter deliberately returns research output, not an executable proposal.
Portfolio policy and approval remain separate deterministic stages.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from copy import deepcopy
from datetime import date
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from tradingagents.agents.schemas import PortfolioDecision
from tradingagents.agents.utils.agent_utils import build_instrument_context
from tradingagents.contracts import InstrumentContract
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.portfolio import PortfolioContext

from .decisions import StructuredDecisionNarrative
from .profiles import resolve_analysis_profile, select_analysts
from .snapshots import SnapshotAnalysisContext


class AnalysisRequest(BaseModel):
    """Validated, provider-neutral input to one research run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    instrument: InstrumentContract
    analysis_date: date
    selected_analysts: tuple[str, ...] | None = None
    portfolio: PortfolioContext | None = None
    config_overrides: Mapping[str, Any] = Field(default_factory=dict)
    snapshot_context: SnapshotAnalysisContext | None = None


class AnalysisResult(BaseModel):
    """Raw graph result retained for later evidence and schema validation."""

    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    instrument: InstrumentContract
    analysis_date: date
    selected_analysts: tuple[str, ...]
    profile_name: str
    reference_only: bool
    final_state: dict[str, Any]
    narrative_signal: str
    decision_payload: StructuredDecisionNarrative | None = None
    material_claims: dict[str, tuple[UUID, ...]] = Field(default_factory=dict)


GraphFactory = Callable[..., TradingAgentsGraph]


class AnalysisEngine:
    """Construct and run the legacy graph behind a stable platform interface."""

    def __init__(
        self,
        *,
        base_config: Mapping[str, Any] | None = None,
        graph_factory: GraphFactory = TradingAgentsGraph,
    ) -> None:
        self._base_config = deepcopy(dict(base_config or DEFAULT_CONFIG))
        self._graph_factory = graph_factory

    def analyze(self, request: AnalysisRequest) -> AnalysisResult:
        profile = resolve_analysis_profile(request.instrument)
        analysts = select_analysts(profile, request.selected_analysts)
        config = deepcopy(self._base_config)
        config.update(deepcopy(dict(request.config_overrides)))
        snapshot_options = {}
        if request.snapshot_context is not None:
            if request.snapshot_context.as_of.date() != request.analysis_date:
                raise ValueError("snapshot clock does not match analysis date")
            snapshot_options["snapshot_reports"] = request.snapshot_context.reports(
                request.instrument.instrument_id, analysts)
        graph = self._graph_factory(
            selected_analysts=analysts,
            config=config,
            **snapshot_options,
        )
        if request.snapshot_context is not None:
            final_state, signal = graph.propagate_snapshots(
                request.instrument.canonical_symbol, request.analysis_date.isoformat(),
                asset_type=profile.legacy_asset_type, portfolio=request.portfolio,
                instrument_context=(build_instrument_context(
                    request.instrument.canonical_symbol, profile.legacy_asset_type,
                    curr_date=request.analysis_date.isoformat())
                    + "\nCanonical instrument metadata: " + request.instrument.model_dump_json()),
            )
        else:
            final_state, signal = graph.propagate(
                request.instrument.canonical_symbol,
                request.analysis_date.isoformat(),
                asset_type=profile.legacy_asset_type,
                portfolio=request.portfolio,
            )
        decision_payload = None
        material_claims = {}
        raw_decision = final_state.get("structured_decision")
        if raw_decision is not None:
            try:
                parsed = PortfolioDecision.model_validate(raw_decision)
                decision_payload = StructuredDecisionNarrative.model_validate({
                    "rating": parsed.rating.value,
                    "confidence": parsed.confidence,
                    "thesis": parsed.investment_thesis,
                    "risks": parsed.risks,
                    "invalidation_conditions": parsed.invalidation_conditions,
                })
                if len({item.claim for item in parsed.evidence_claims}) == len(parsed.evidence_claims):
                    material_claims = {item.claim: item.snapshot_ids for item in parsed.evidence_claims}
            except (ValueError, TypeError):
                # Never parse prose or invent missing confidence/risk fields.
                pass
        return AnalysisResult(
            instrument=request.instrument,
            analysis_date=request.analysis_date,
            selected_analysts=analysts,
            profile_name=profile.name,
            reference_only=not profile.investable,
            final_state=dict(final_state),
            narrative_signal=str(signal),
            decision_payload=decision_payload,
            material_claims=material_claims,
        )
