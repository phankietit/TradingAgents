"""Public platform domain contracts, versioned independently from persistence."""

from .artifacts import ArtifactKind, ArtifactManifest
from .base import SCHEMA_VERSION, ContentHash, StrictContract, VersionedContract, Weight
from .data import DataQualityStatus, EvidenceReference, SnapshotManifest
from .decisions import DecisionCandidate, DecisionRating, DecisionStatus
from .instruments import AssetClass, InstrumentContract, Tradability
from .jobs import JobKind, JobRecord, JobStatus
from .policy import PolicyCheck, PolicyContract, PolicyResult
from .portfolio import CashBalance, PortfolioSnapshot, PositionSnapshot
from .runs import RunManifest, RunStatus

CONTRACT_REGISTRY = {
    contract.__name__: contract
    for contract in (
        InstrumentContract,
        ArtifactManifest,
        SnapshotManifest,
        RunManifest,
        JobRecord,
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
    "JobKind",
    "JobRecord",
    "JobStatus",
    "PolicyCheck",
    "PolicyContract",
    "PolicyResult",
    "PortfolioSnapshot",
    "PositionSnapshot",
    "RunManifest",
    "RunStatus",
    "SnapshotManifest",
    "StrictContract",
    "Tradability",
    "VersionedContract",
    "Weight",
]
