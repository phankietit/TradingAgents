"""Deterministic asset-specific analyst and prompt boundaries."""

from __future__ import annotations

from dataclasses import dataclass

from tradingagents.contracts import AssetClass, InstrumentContract, Tradability


@dataclass(frozen=True)
class AssetAnalysisProfile:
    name: str
    legacy_asset_type: str
    allowed_analysts: tuple[str, ...]
    investable: bool


PROFILES = {
    AssetClass.EQUITY: AssetAnalysisProfile(
        "equity", "stock", ("market", "social", "news", "fundamentals"), True
    ),
    AssetClass.ETF: AssetAnalysisProfile(
        "etf", "etf", ("market", "news"), True
    ),
    AssetClass.CASH_INDEX: AssetAnalysisProfile(
        "cash-index-reference", "reference", ("market", "news"), False
    ),
    AssetClass.REFERENCE_FUTURE: AssetAnalysisProfile(
        "futures-reference", "reference", ("market", "news"), False
    ),
    AssetClass.CRYPTO: AssetAnalysisProfile(
        "large-cap-crypto", "crypto", ("market", "social", "news"), True
    ),
}

CRYPTO_ALLOWLIST = frozenset({"BTC-USD", "ETH-USD"})


def resolve_analysis_profile(instrument: InstrumentContract) -> AssetAnalysisProfile:
    profile = PROFILES[instrument.asset_class]
    if (
        instrument.asset_class is AssetClass.CRYPTO
        and instrument.canonical_symbol.upper() not in CRYPTO_ALLOWLIST
    ):
        raise ValueError("initial crypto scope is limited to BTC-USD and ETH-USD")
    if profile.investable and instrument.tradability is not Tradability.INVESTABLE:
        raise ValueError(f"{profile.name} profile requires an investable instrument")
    if not profile.investable and instrument.tradability is not Tradability.REFERENCE_ONLY:
        raise ValueError(f"{profile.name} profile must remain reference_only")
    return profile


def select_analysts(
    profile: AssetAnalysisProfile, requested: tuple[str, ...] | None
) -> tuple[str, ...]:
    if requested is None:
        return profile.allowed_analysts
    unknown = tuple(name for name in requested if name not in profile.allowed_analysts)
    if unknown:
        raise ValueError(
            f"analysts {unknown!r} are not allowed for the {profile.name} profile"
        )
    if not requested:
        raise ValueError("at least one analyst is required")
    if len(requested) != len(set(requested)):
        raise ValueError("duplicate analysts are not allowed")
    return requested
