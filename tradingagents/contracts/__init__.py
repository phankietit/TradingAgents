"""Public platform domain contracts, versioned independently from persistence."""

from .artifacts import ArtifactKind, ArtifactManifest
from .base import SCHEMA_VERSION, ContentHash, StrictContract, VersionedContract, Weight
from .data import DataQualityStatus, EvidenceReference, SnapshotManifest
from .decisions import DecisionCandidate, DecisionRating, DecisionStatus
from .equity_etf import (
    DatasetCoverage,
    EquityETFDataset,
    EquityETFSnapshotBundle,
    ETFProfile,
    FilingRecord,
    FundamentalFact,
    FundHolding,
    NewsRecord,
)
from .events import TERMINAL_RUN_EVENTS, RunEvent, RunEventType
from .futures_reference import (
    FuturesContractReference,
    FuturesDataGap,
    FuturesGapKind,
    FuturesReferenceSnapshot,
    FuturesSessionWindow,
    GapDisposition,
    RollAdjustmentMethod,
    RolloverMetadata,
)
from .instruments import (
    AssetClass,
    InstrumentAliasContract,
    InstrumentContract,
    Tradability,
    normalize_instrument_alias,
)
from .jobs import JobKind, JobRecord, JobStatus
from .policy import PolicyCheck, PolicyContract, PolicyResult
from .portfolio import CashBalance, PortfolioSnapshot, PositionSnapshot
from .runs import RunManifest, RunStatus
from .timeseries import (
    BenchmarkComparison,
    NormalizedTimeSeries,
    OHLCVBar,
    PriceBasis,
    PriceInterval,
    ReturnPoint,
    TimeSeriesStatistics,
    TimeSeriesView,
)

CONTRACT_REGISTRY = {
    contract.__name__: contract
    for contract in (
        InstrumentContract,
        InstrumentAliasContract,
        ArtifactManifest,
        SnapshotManifest,
        RunManifest,
        JobRecord,
        RunEvent,
        EvidenceReference,
        DecisionCandidate,
        PortfolioSnapshot,
        PolicyContract,
        PolicyCheck,
        NormalizedTimeSeries,
        TimeSeriesView,
        EquityETFSnapshotBundle,
        FuturesReferenceSnapshot,
    )
}

__all__ = [
    "SCHEMA_VERSION",
    "CONTRACT_REGISTRY",
    "AssetClass",
    "ArtifactKind",
    "ArtifactManifest",
    "BenchmarkComparison",
    "CashBalance",
    "ContentHash",
    "DataQualityStatus",
    "DecisionCandidate",
    "DecisionRating",
    "DecisionStatus",
    "DatasetCoverage",
    "EvidenceReference",
    "EquityETFDataset",
    "EquityETFSnapshotBundle",
    "ETFProfile",
    "FilingRecord",
    "FundHolding",
    "FundamentalFact",
    "FuturesContractReference",
    "FuturesDataGap",
    "FuturesGapKind",
    "FuturesReferenceSnapshot",
    "FuturesSessionWindow",
    "GapDisposition",
    "InstrumentContract",
    "InstrumentAliasContract",
    "JobKind",
    "JobRecord",
    "JobStatus",
    "PolicyCheck",
    "PolicyContract",
    "PolicyResult",
    "PortfolioSnapshot",
    "NormalizedTimeSeries",
    "NewsRecord",
    "OHLCVBar",
    "PriceBasis",
    "PriceInterval",
    "ReturnPoint",
    "RollAdjustmentMethod",
    "RolloverMetadata",
    "PositionSnapshot",
    "RunManifest",
    "RunEvent",
    "RunEventType",
    "RunStatus",
    "SnapshotManifest",
    "StrictContract",
    "TERMINAL_RUN_EVENTS",
    "Tradability",
    "TimeSeriesStatistics",
    "TimeSeriesView",
    "VersionedContract",
    "Weight",
    "normalize_instrument_alias",
]
