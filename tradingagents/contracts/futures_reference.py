"""Reference-only equity-index futures metadata and gap contracts."""

from __future__ import annotations

from datetime import date
from enum import Enum
from uuid import UUID

from pydantic import AwareDatetime, Field, FiniteFloat, model_validator

from .base import NonEmptyText, StrictContract, VersionedContract
from .data import DataQualityStatus


class RollAdjustmentMethod(str, Enum):
    UNADJUSTED = "unadjusted"
    BACKWARD_DIFFERENCE = "backward_difference"
    BACKWARD_RATIO = "backward_ratio"


class FuturesGapKind(str, Enum):
    SESSION_BREAK = "session_break"
    MISSING_BAR = "missing_bar"
    ROLL_TRANSITION = "roll_transition"


class GapDisposition(str, Enum):
    EXPECTED = "expected"
    PRESERVED = "preserved"
    UNAVAILABLE = "unavailable"


class FuturesContractReference(StrictContract):
    root_symbol: NonEmptyText
    contract_symbol: NonEmptyText
    expiry_date: date
    last_trade_at: AwareDatetime
    observed_at: AwareDatetime
    vendor: NonEmptyText


class RolloverMetadata(StrictContract):
    from_contract: NonEmptyText
    to_contract: NonEmptyText
    effective_at: AwareDatetime
    observed_at: AwareDatetime
    method: RollAdjustmentMethod
    adjustment_value: FiniteFloat | None = None
    vendor: NonEmptyText

    @model_validator(mode="after")
    def validate_roll(self):
        if self.from_contract == self.to_contract:
            raise ValueError("rollover contracts must differ")
        if self.observed_at > self.effective_at:
            raise ValueError("rollover metadata must be observed by its effective time")
        if self.method is RollAdjustmentMethod.UNADJUSTED and self.adjustment_value is not None:
            raise ValueError("unadjusted rollover must not contain an adjustment value")
        if self.method is not RollAdjustmentMethod.UNADJUSTED and self.adjustment_value is None:
            raise ValueError("adjusted rollover requires an adjustment value")
        if self.method is RollAdjustmentMethod.BACKWARD_RATIO and self.adjustment_value <= 0:
            raise ValueError("ratio rollover adjustment must be positive")
        return self


class FuturesSessionWindow(StrictContract):
    trading_date: date
    observed_at: AwareDatetime
    overnight_open: AwareDatetime
    rth_open: AwareDatetime
    rth_close: AwareDatetime
    session_close: AwareDatetime
    calendar: NonEmptyText = "CME_Equity"

    @model_validator(mode="after")
    def validate_window(self):
        if not (
            self.overnight_open < self.rth_open < self.rth_close <= self.session_close
        ):
            raise ValueError("futures session windows must be chronologically ordered")
        return self


class FuturesDataGap(StrictContract):
    start: AwareDatetime
    end: AwareDatetime
    kind: FuturesGapKind
    disposition: GapDisposition
    reason: NonEmptyText

    @model_validator(mode="after")
    def validate_gap(self):
        if self.start >= self.end:
            raise ValueError("futures data gap start must precede end")
        if self.kind is FuturesGapKind.SESSION_BREAK and self.disposition is not GapDisposition.EXPECTED:
            raise ValueError("session breaks must be marked expected")
        return self


class FuturesReferenceSnapshot(VersionedContract):
    reference_id: UUID
    instrument_id: UUID
    root_symbol: NonEmptyText
    as_of: AwareDatetime
    retrieved_at: AwareDatetime
    continuous_series_snapshot_id: UUID
    active_contract: FuturesContractReference
    next_contract: FuturesContractReference | None = None
    rollovers: tuple[RolloverMetadata, ...] = ()
    sessions: tuple[FuturesSessionWindow, ...] = Field(min_length=1)
    gaps: tuple[FuturesDataGap, ...] = ()
    quality_status: DataQualityStatus
    quality_reasons: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_reference_boundary(self):
        if self.root_symbol not in {"NQ", "ES"}:
            raise ValueError("initial futures references are limited to NQ and ES")
        if self.retrieved_at < self.as_of:
            raise ValueError("retrieved_at must not precede as_of")
        contracts = (self.active_contract,) + (
            (self.next_contract,) if self.next_contract is not None else ()
        )
        if any(contract.root_symbol != self.root_symbol for contract in contracts):
            raise ValueError("contract roots must match the reference root")
        if any(contract.observed_at > self.as_of for contract in contracts):
            raise ValueError("contract identity must be observable by as_of")
        if any(roll.observed_at > self.as_of for roll in self.rollovers):
            raise ValueError("rollover metadata must be observable by as_of")
        if any(gap.end > self.as_of for gap in self.gaps):
            raise ValueError("futures gaps must not extend beyond as_of")
        if any(window.observed_at > self.as_of for window in self.sessions):
            raise ValueError("session metadata must be observable by as_of")
        return self
