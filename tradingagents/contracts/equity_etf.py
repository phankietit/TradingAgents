"""Point-in-time equity and ETF snapshot bundle contracts."""

from __future__ import annotations

from enum import Enum
from uuid import UUID

from pydantic import AwareDatetime, Field, FiniteFloat, HttpUrl, model_validator

from .base import NonEmptyText, StrictContract, VersionedContract
from .data import DataQualityStatus
from .instruments import AssetClass


class EquityETFDataset(str, Enum):
    PRICE = "price"
    FILINGS = "filings"
    FUNDAMENTALS = "fundamentals"
    NEWS = "news"
    FUND_METADATA = "fund_metadata"


class DatasetCoverage(StrictContract):
    dataset: EquityETFDataset
    vendors: tuple[str, ...] = ()
    status: DataQualityStatus
    eligible_count: int = Field(ge=0)
    excluded_future_count: int = Field(ge=0)
    reason: NonEmptyText


class FilingRecord(StrictContract):
    accession_number: NonEmptyText
    form: NonEmptyText
    period_end: AwareDatetime
    filed_at: AwareDatetime
    vendor: NonEmptyText
    source_url: HttpUrl | None = None

    @model_validator(mode="after")
    def filed_after_period(self):
        if self.filed_at < self.period_end:
            raise ValueError("filing filed_at must not precede period_end")
        return self


class FundamentalFact(StrictContract):
    metric: NonEmptyText
    value: FiniteFloat
    unit: NonEmptyText
    period_end: AwareDatetime
    filed_at: AwareDatetime
    form: NonEmptyText
    vendor: NonEmptyText
    source_id: NonEmptyText

    @model_validator(mode="after")
    def filed_after_period(self):
        if self.filed_at < self.period_end:
            raise ValueError("fundamental filed_at must not precede period_end")
        return self


class NewsRecord(StrictContract):
    article_id: NonEmptyText
    headline: NonEmptyText
    source: NonEmptyText
    vendor: NonEmptyText
    published_at: AwareDatetime
    source_url: HttpUrl | None = None


class FundHolding(StrictContract):
    canonical_symbol: NonEmptyText
    weight: FiniteFloat = Field(ge=0, le=1)


class ETFProfile(StrictContract):
    benchmark_symbol: NonEmptyText
    issuer: NonEmptyText
    expense_ratio: FiniteFloat = Field(ge=0, le=1)
    holdings_as_of: AwareDatetime
    vendor: NonEmptyText
    holdings: tuple[FundHolding, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_holdings(self):
        symbols = [holding.canonical_symbol for holding in self.holdings]
        if len(symbols) != len(set(symbols)):
            raise ValueError("ETF holdings must use unique canonical symbols")
        if sum(holding.weight for holding in self.holdings) > 1.000001:
            raise ValueError("ETF holding weights must not exceed 100 percent")
        return self


class EquityETFSnapshotBundle(VersionedContract):
    bundle_id: UUID
    instrument_id: UUID
    asset_class: AssetClass
    as_of: AwareDatetime
    retrieved_at: AwareDatetime
    price_snapshot_id: UUID
    filings: tuple[FilingRecord, ...] = ()
    fundamentals: tuple[FundamentalFact, ...] = ()
    news: tuple[NewsRecord, ...] = ()
    fund_profile: ETFProfile | None = None
    coverage: tuple[DatasetCoverage, ...]
    quality_status: DataQualityStatus
    quality_reasons: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_asset_and_point_in_time_boundaries(self):
        if self.asset_class not in {AssetClass.EQUITY, AssetClass.ETF}:
            raise ValueError("equity/ETF bundles require an equity or ETF instrument")
        if self.retrieved_at < self.as_of:
            raise ValueError("retrieved_at must not precede as_of")
        if any(item.filed_at > self.as_of for item in self.filings):
            raise ValueError("filings must be public on or before as_of")
        if any(item.filed_at > self.as_of for item in self.fundamentals):
            raise ValueError("fundamentals must be filed on or before as_of")
        if any(item.published_at > self.as_of for item in self.news):
            raise ValueError("news must be published on or before as_of")
        if self.asset_class is AssetClass.EQUITY and self.fund_profile is not None:
            raise ValueError("equity snapshots must not contain ETF fund metadata")
        if self.asset_class is AssetClass.ETF:
            if self.fundamentals:
                raise ValueError("ETF snapshots must not use company fundamentals")
            if self.fund_profile and self.fund_profile.holdings_as_of > self.as_of:
                raise ValueError("ETF holdings vintage must not exceed as_of")
            if self.quality_status is DataQualityStatus.OK and self.fund_profile is None:
                raise ValueError("an OK ETF snapshot requires point-in-time fund metadata")
        datasets = [item.dataset for item in self.coverage]
        if len(datasets) != len(set(datasets)):
            raise ValueError("snapshot coverage datasets must be unique")
        return self
