"""Reproducible large-cap equity screening without LLM or vendor calls."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from uuid import NAMESPACE_URL, UUID, uuid5

from tradingagents.contracts import (
    ArtifactKind,
    AssetClass,
    DataQualityStatus,
    ScreenedStock,
    ScreeningExclusionCode,
    StockScreenerPolicy,
    StockScreeningExclusion,
    StockScreeningInput,
    StockUniverseSnapshot,
    Tradability,
)
from tradingagents.platform.artifacts import ArtifactService


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _content_hash(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical_bytes(value)).hexdigest()


class DeterministicStockScreener:
    def __init__(self, artifacts: ArtifactService | None = None):
        self.artifacts = artifacts

    def screen(
        self,
        *,
        inputs: tuple[StockScreeningInput, ...],
        policy: StockScreenerPolicy,
        as_of: datetime,
        generated_at: datetime,
    ) -> StockUniverseSnapshot:
        ordered_inputs = tuple(
            sorted(inputs, key=lambda item: item.instrument.canonical_symbol.casefold())
        )
        self._validate_inputs(ordered_inputs, as_of)
        input_hash = _content_hash(
            {
                "as_of": as_of.isoformat(),
                "policy": policy.model_dump(mode="json"),
                "inputs": [item.model_dump(mode="json") for item in ordered_inputs],
            }
        )

        eligible: list[StockScreeningInput] = []
        exclusions: list[StockScreeningExclusion] = []
        for item in ordered_inputs:
            codes, reasons = self._exclusion_reasons(item, policy)
            if codes:
                exclusions.append(
                    StockScreeningExclusion(
                        instrument_id=item.instrument.instrument_id,
                        canonical_symbol=item.instrument.canonical_symbol,
                        codes=tuple(codes),
                        reasons=tuple(reasons),
                    )
                )
            else:
                eligible.append(item)

        market_cap_ranks = {
            item.instrument.instrument_id: rank
            for rank, item in enumerate(
                sorted(
                    eligible,
                    key=lambda value: (
                        -value.market_cap_usd,
                        value.instrument.canonical_symbol.casefold(),
                    ),
                ),
                start=1,
            )
        }
        liquidity_ranks = {
            item.instrument.instrument_id: rank
            for rank, item in enumerate(
                sorted(
                    eligible,
                    key=lambda value: (
                        -value.average_dollar_volume_20d_usd,
                        value.instrument.canonical_symbol.casefold(),
                    ),
                ),
                start=1,
            )
        }
        ranked = sorted(
            eligible,
            key=lambda item: (
                policy.market_cap_rank_weight
                * market_cap_ranks[item.instrument.instrument_id]
                + policy.liquidity_rank_weight
                * liquidity_ranks[item.instrument.instrument_id],
                -item.market_cap_usd,
                -item.average_dollar_volume_20d_usd,
                item.instrument.canonical_symbol.casefold(),
            ),
        )
        selected = ranked[: policy.max_candidates]
        for item in ranked[policy.max_candidates :]:
            exclusions.append(
                StockScreeningExclusion(
                    instrument_id=item.instrument.instrument_id,
                    canonical_symbol=item.instrument.canonical_symbol,
                    codes=(ScreeningExclusionCode.OUTSIDE_LIMIT,),
                    reasons=(f"rank is outside max_candidates={policy.max_candidates}",),
                )
            )

        candidates = tuple(
            ScreenedStock(
                rank=rank,
                instrument_id=item.instrument.instrument_id,
                canonical_symbol=item.instrument.canonical_symbol,
                source_snapshot_id=item.source_snapshot_id,
                market_cap_usd=item.market_cap_usd,
                average_dollar_volume_20d_usd=item.average_dollar_volume_20d_usd,
                annualized_volatility=item.annualized_volatility,
                market_cap_rank=market_cap_ranks[item.instrument.instrument_id],
                liquidity_rank=liquidity_ranks[item.instrument.instrument_id],
                ranking_score=(
                    policy.market_cap_rank_weight
                    * market_cap_ranks[item.instrument.instrument_id]
                    + policy.liquidity_rank_weight
                    * liquidity_ranks[item.instrument.instrument_id]
                ),
            )
            for rank, item in enumerate(selected, start=1)
        )
        ordered_exclusions = tuple(
            sorted(exclusions, key=lambda item: item.canonical_symbol.casefold())
        )
        universe_hash = _content_hash(
            {
                "input_hash": input_hash,
                "generated_at": generated_at.isoformat(),
                "candidates": [item.model_dump(mode="json") for item in candidates],
                "exclusions": [
                    item.model_dump(mode="json") for item in ordered_exclusions
                ],
            }
        )
        return StockUniverseSnapshot(
            screening_snapshot_id=uuid5(NAMESPACE_URL, universe_hash),
            as_of=as_of,
            generated_at=generated_at,
            policy=policy,
            input_count=len(ordered_inputs),
            input_hash=input_hash,
            universe_hash=universe_hash,
            candidates=candidates,
            exclusions=ordered_exclusions,
        )

    def persist(self, *, owner_id: UUID, snapshot: StockUniverseSnapshot):
        artifacts = self._require_artifacts()
        content = _canonical_bytes(snapshot.model_dump(mode="json"))
        return artifacts.create(
            owner_id=owner_id,
            kind=ArtifactKind.SCREENING_SNAPSHOT,
            media_type="application/vnd.tradingagents.stock-universe+json",
            content=content,
            artifact_id=snapshot.screening_snapshot_id,
            created_at=snapshot.generated_at,
        )

    def load(self, *, owner_id: UUID, screening_snapshot_id: UUID) -> StockUniverseSnapshot:
        artifacts = self._require_artifacts()
        loaded = artifacts.read(screening_snapshot_id, owner_id)
        if loaded is None:
            raise LookupError("screening snapshot is unavailable")
        manifest, payload = loaded
        if manifest.kind is not ArtifactKind.SCREENING_SNAPSHOT:
            raise ValueError("artifact is not a screening snapshot")
        snapshot = StockUniverseSnapshot.model_validate_json(payload)
        if snapshot.screening_snapshot_id != screening_snapshot_id:
            raise ValueError("screening payload identity does not match its artifact")
        return snapshot

    def _require_artifacts(self) -> ArtifactService:
        if self.artifacts is None:
            raise RuntimeError("artifact service is required for persistence")
        return self.artifacts

    @staticmethod
    def _validate_inputs(
        inputs: tuple[StockScreeningInput, ...], as_of: datetime
    ) -> None:
        instrument_ids = [item.instrument.instrument_id for item in inputs]
        symbols = [item.instrument.canonical_symbol.casefold() for item in inputs]
        if len(instrument_ids) != len(set(instrument_ids)):
            raise ValueError("screening inputs must have unique instrument IDs")
        if len(symbols) != len(set(symbols)):
            raise ValueError("screening inputs must have unique canonical symbols")
        if any(item.observed_at > as_of for item in inputs):
            raise ValueError("screening inputs must be observable by as_of")

    @staticmethod
    def _exclusion_reasons(
        item: StockScreeningInput, policy: StockScreenerPolicy
    ) -> tuple[list[ScreeningExclusionCode], list[str]]:
        instrument = item.instrument
        codes: list[ScreeningExclusionCode] = []
        reasons: list[str] = []

        def exclude(code: ScreeningExclusionCode, reason: str) -> None:
            codes.append(code)
            reasons.append(reason)

        if instrument.asset_class is not AssetClass.EQUITY:
            exclude(ScreeningExclusionCode.NON_EQUITY, "instrument is not an equity")
        if instrument.tradability is not Tradability.INVESTABLE:
            exclude(
                ScreeningExclusionCode.NOT_INVESTABLE,
                "instrument is not marked investable",
            )
        if instrument.venue.upper() not in policy.allowed_venues:
            exclude(
                ScreeningExclusionCode.VENUE_NOT_ALLOWED,
                f"venue {instrument.venue} is outside the allowed universe",
            )
        if instrument.quote_currency.upper() != policy.quote_currency:
            exclude(
                ScreeningExclusionCode.CURRENCY_NOT_ALLOWED,
                f"quote currency {instrument.quote_currency} is not allowed",
            )
        if item.quality_status is not DataQualityStatus.OK:
            exclude(
                ScreeningExclusionCode.DATA_QUALITY,
                f"source quality is {item.quality_status.value}",
            )
        if item.market_cap_usd < policy.min_market_cap_usd:
            exclude(ScreeningExclusionCode.MARKET_CAP, "market cap is below threshold")
        if (
            item.average_dollar_volume_20d_usd
            < policy.min_average_dollar_volume_20d_usd
        ):
            exclude(ScreeningExclusionCode.LIQUIDITY, "liquidity is below threshold")
        if item.last_price_usd < policy.min_last_price_usd:
            exclude(ScreeningExclusionCode.PRICE, "last price is below threshold")
        if item.history_days < policy.min_history_days:
            exclude(ScreeningExclusionCode.HISTORY, "price history is below threshold")
        if item.annualized_volatility > policy.max_annualized_volatility:
            exclude(
                ScreeningExclusionCode.VOLATILITY,
                "annualized volatility is above threshold",
            )
        return codes, reasons
