"""Instrument master service over the platform repository."""

from __future__ import annotations

from collections.abc import Iterable

from tradingagents.contracts import (
    AssetClass,
    InstrumentAliasContract,
    InstrumentContract,
    Tradability,
)
from tradingagents.platform.persistence import PlatformRepository

from .catalog import INITIAL_INSTRUMENT_CATALOG, InstrumentSeed


class InstrumentMaster:
    def __init__(self, repository: PlatformRepository):
        self.repository = repository

    def register(
        self,
        instrument: InstrumentContract,
        aliases: Iterable[tuple[str, str]] = (),
    ) -> InstrumentContract:
        self.repository.add_instrument(instrument)
        for namespace, alias in aliases:
            self.repository.add_instrument_alias(
                InstrumentAliasContract.create(
                    instrument_id=instrument.instrument_id,
                    namespace=namespace,
                    alias=alias,
                )
            )
        return instrument

    def bootstrap(self, seeds: Iterable[InstrumentSeed] = INITIAL_INSTRUMENT_CATALOG) -> int:
        count = 0
        for seed in seeds:
            self.register(seed.instrument, seed.aliases)
            count += 1
        return count

    def resolve(
        self, alias: str, *, namespace: str | None = None
    ) -> InstrumentContract | None:
        return self.repository.resolve_instrument(alias, namespace=namespace)

    def list(
        self,
        *,
        asset_class: AssetClass | None = None,
        tradability: Tradability | None = None,
        venue: str | None = None,
        limit: int = 100,
    ) -> tuple[InstrumentContract, ...]:
        return self.repository.list_instruments(
            asset_class=asset_class,
            tradability=tradability,
            venue=venue,
            limit=limit,
        )
