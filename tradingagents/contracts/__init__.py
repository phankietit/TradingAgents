"""Public platform domain contracts, versioned independently from persistence."""

from .artifacts import ArtifactKind, ArtifactManifest
from .base import SCHEMA_VERSION, ContentHash, StrictContract, VersionedContract, Weight
from .data import DataQualityStatus, EvidenceReference, SnapshotManifest
from .decisions import DecisionCandidate, DecisionRating, DecisionStatus
from .events import TERMINAL_RUN_EVENTS, RunEvent, RunEventType
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
    "EvidenceReference",
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
    "OHLCVBar",
    "PriceBasis",
    "PriceInterval",
    "ReturnPoint",
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
