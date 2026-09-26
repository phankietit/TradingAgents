"""Platform adapter for the existing :class:`TradingAgentsGraph` runtime.

The adapter deliberately returns research output, not an executable proposal.
Portfolio policy and approval remain separate deterministic stages.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from copy import deepcopy
from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from tradingagents.contracts import InstrumentContract
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.portfolio import PortfolioContext


class AnalysisRequest(BaseModel):
    """Validated, provider-neutral input to one research run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    instrument: InstrumentContract
    analysis_date: date
    selected_analysts: tuple[str, ...] = Field(min_length=1)
    portfolio: PortfolioContext | None = None
    config_overrides: Mapping[str, Any] = Field(default_factory=dict)


class AnalysisResult(BaseModel):
    """Raw graph result retained for later evidence and schema validation."""

    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    instrument: InstrumentContract
    analysis_date: date
    selected_analysts: tuple[str, ...]
    final_state: dict[str, Any]
    narrative_signal: str


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
        config = deepcopy(self._base_config)
        config.update(deepcopy(dict(request.config_overrides)))
        graph = self._graph_factory(
            selected_analysts=request.selected_analysts,
            config=config,
        )
        final_state, signal = graph.propagate(
            request.instrument.canonical_symbol,
            request.analysis_date.isoformat(),
            asset_type=self._legacy_asset_type(request.instrument),
            portfolio=request.portfolio,
        )
        return AnalysisResult(
            instrument=request.instrument,
            analysis_date=request.analysis_date,
            selected_analysts=request.selected_analysts,
            final_state=dict(final_state),
            narrative_signal=str(signal),
        )

    @staticmethod
    def _legacy_asset_type(instrument: InstrumentContract) -> str:
        return "crypto" if instrument.asset_class.value == "crypto" else "stock"
