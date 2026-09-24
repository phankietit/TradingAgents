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
    )
}

__all__ = [
    "SCHEMA_VERSION",
    "CONTRACT_REGISTRY",
    "AssetClass",
    "ArtifactKind",
    "ArtifactManifest",
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
    "PositionSnapshot",
    "RunManifest",
    "RunEvent",
    "RunEventType",
    "RunStatus",
    "SnapshotManifest",
    "StrictContract",
    "TERMINAL_RUN_EVENTS",
    "Tradability",
    "VersionedContract",
    "Weight",
    "normalize_instrument_alias",
]
