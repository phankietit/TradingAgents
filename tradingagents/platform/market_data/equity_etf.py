"""Vendor-neutral, point-in-time equity and ETF snapshot pipeline."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID, uuid4

from tradingagents.contracts import (
    ArtifactKind,
    AssetClass,
    DataQualityStatus,
    DatasetCoverage,
    EquityETFDataset,
    EquityETFSnapshotBundle,
    ETFProfile,
    FilingRecord,
    FundamentalFact,
    InstrumentContract,
    NewsRecord,
    SnapshotManifest,
)
from tradingagents.platform.artifacts import ArtifactService
from tradingagents.platform.persistence import ImmutableRecordConflict, PlatformRepository

from .timeseries import TimeSeriesSnapshotService

RecordT = TypeVar("RecordT")


@dataclass(frozen=True)
class SourceBatch(Generic[RecordT]):
    vendor: str
    status: DataQualityStatus
    records: tuple[RecordT, ...] = ()
    reason: str = "source batch supplied"

    def __post_init__(self):
        if not self.vendor.strip():
            raise ValueError("source batch vendor is required")
        if not self.reason.strip():
            raise ValueError("source batch reason is required")
        if self.status is not DataQualityStatus.OK and self.records:
            raise ValueError("a non-OK source batch must not contain apparently valid records")


QUALITY_PRIORITY = {
    DataQualityStatus.OK: 0,
    DataQualityStatus.NO_DATA: 1,
    DataQualityStatus.STALE: 2,
    DataQualityStatus.COVERAGE_GAP: 3,
    DataQualityStatus.UNAVAILABLE: 4,
    DataQualityStatus.INVALID: 5,
}


def _coverage(
    *,
    dataset: EquityETFDataset,
    batch: SourceBatch,
    eligible_count: int,
    excluded_future_count: int,
) -> DatasetCoverage:
    status = batch.status
    reason = batch.reason
    if status is DataQualityStatus.OK and eligible_count == 0:
        if excluded_future_count:
            status = DataQualityStatus.COVERAGE_GAP
            reason = "source rows exist but none were public by as_of"
        else:
            status = DataQualityStatus.NO_DATA
            reason = "source was reachable but returned no eligible rows"
    return DatasetCoverage(
        dataset=dataset,
        vendors=(batch.vendor,),
        status=status,
        eligible_count=eligible_count,
        excluded_future_count=excluded_future_count,
        reason=reason,
    )


def _assert_unique(records: tuple[RecordT, ...], key, label: str) -> None:
    keys = [key(record) for record in records]
    if len(keys) != len(set(keys)):
        raise ValueError(f"{label} records must be unique")


class EquityETFSnapshotPipeline:
    def __init__(
        self,
        repository: PlatformRepository,
        artifacts: ArtifactService,
    ):
        self.repository = repository
        self.artifacts = artifacts
        self.time_series = TimeSeriesSnapshotService(repository, artifacts)

    def load(
        self,
        *,
        owner_id: UUID,
        instrument_id: UUID,
        as_of: datetime,
    ) -> tuple[SnapshotManifest, EquityETFSnapshotBundle]:
        snapshot = self.repository.latest_snapshot(
            instrument_id=instrument_id,
            dataset="equity_etf.bundle",
            as_of=as_of,
        )
        if snapshot is None:
            raise LookupError("no eligible equity/ETF snapshot bundle")
        artifact = self.repository.get_snapshot_artifact(snapshot.snapshot_id, owner_id)
        if artifact is None:
            raise LookupError("equity/ETF snapshot payload is unavailable")
        loaded = self.artifacts.read(artifact.artifact_id, owner_id)
        if loaded is None:
            raise LookupError("equity/ETF snapshot payload is unavailable")
        _artifact, payload = loaded
        bundle = EquityETFSnapshotBundle.model_validate_json(payload)
        if bundle.instrument_id != instrument_id or bundle.bundle_id != snapshot.snapshot_id:
            raise ValueError("equity/ETF payload identity does not match its snapshot")
        return snapshot, bundle

    def build_equity(
        self,
        *,
        owner_id: UUID,
        instrument: InstrumentContract,
        as_of: datetime,
        retrieved_at: datetime,
        price_dataset: str,
        filings: SourceBatch[FilingRecord],
        fundamentals: SourceBatch[FundamentalFact],
        news: SourceBatch[NewsRecord],
        pipeline_id: str,
        bundle_id: UUID | None = None,
    ) -> tuple[SnapshotManifest, EquityETFSnapshotBundle]:
        if instrument.asset_class is not AssetClass.EQUITY:
            raise ValueError("equity pipeline requires an equity instrument")
        eligible_filings, excluded_filings = self._filter(
            filings, as_of, "filed_at", EquityETFDataset.FILINGS
        )
        eligible_fundamentals, excluded_fundamentals = self._filter(
            fundamentals, as_of, "filed_at", EquityETFDataset.FUNDAMENTALS
        )
        eligible_news, excluded_news = self._filter(
            news, as_of, "published_at", EquityETFDataset.NEWS
        )
        _assert_unique(eligible_filings, lambda item: item.accession_number, "filing")
        _assert_unique(
            eligible_fundamentals,
            lambda item: (item.metric, item.period_end, item.filed_at, item.source_id),
            "fundamental",
        )
        _assert_unique(eligible_news, lambda item: item.article_id, "news")
        price_snapshot, _series = self.time_series.load(
            owner_id=owner_id,
            instrument_id=instrument.instrument_id,
            dataset=price_dataset,
            as_of=as_of,
        )
        coverage = (
            self._price_coverage(price_snapshot),
            excluded_filings,
            excluded_fundamentals,
            excluded_news,
        )
        bundle = self._bundle(
            bundle_id=bundle_id,
            instrument=instrument,
            as_of=as_of,
            retrieved_at=retrieved_at,
            price_snapshot=price_snapshot,
            filings=eligible_filings,
            fundamentals=eligible_fundamentals,
            news=eligible_news,
            fund_profile=None,
            coverage=coverage,
        )
        return self._persist(owner_id=owner_id, bundle=bundle, pipeline_id=pipeline_id)

    def build_etf(
        self,
        *,
        owner_id: UUID,
        instrument: InstrumentContract,
        as_of: datetime,
        retrieved_at: datetime,
        price_dataset: str,
        news: SourceBatch[NewsRecord],
        fund_metadata: SourceBatch[ETFProfile],
        pipeline_id: str,
        bundle_id: UUID | None = None,
    ) -> tuple[SnapshotManifest, EquityETFSnapshotBundle]:
        if instrument.asset_class is not AssetClass.ETF:
            raise ValueError("ETF pipeline requires an ETF instrument")
        eligible_news, news_coverage = self._filter(
            news, as_of, "published_at", EquityETFDataset.NEWS
        )
        eligible_profiles, profile_coverage = self._filter(
            fund_metadata, as_of, "holdings_as_of", EquityETFDataset.FUND_METADATA
        )
        if len(eligible_profiles) > 1:
            raise ValueError("ETF pipeline accepts one fund metadata vintage per snapshot")
        _assert_unique(eligible_news, lambda item: item.article_id, "news")
        price_snapshot, _series = self.time_series.load(
            owner_id=owner_id,
            instrument_id=instrument.instrument_id,
            dataset=price_dataset,
            as_of=as_of,
        )
        coverage = (self._price_coverage(price_snapshot), news_coverage, profile_coverage)
        bundle = self._bundle(
            bundle_id=bundle_id,
            instrument=instrument,
            as_of=as_of,
            retrieved_at=retrieved_at,
            price_snapshot=price_snapshot,
            filings=(),
            fundamentals=(),
            news=eligible_news,
            fund_profile=eligible_profiles[0] if eligible_profiles else None,
            coverage=coverage,
        )
        return self._persist(owner_id=owner_id, bundle=bundle, pipeline_id=pipeline_id)

    @staticmethod
    def _filter(
        batch: SourceBatch[RecordT],
        as_of: datetime,
        timestamp_name: str,
        dataset: EquityETFDataset,
    ) -> tuple[tuple[RecordT, ...], DatasetCoverage]:
        if batch.status is not DataQualityStatus.OK:
            return (), DatasetCoverage(
                dataset=dataset,
                vendors=(batch.vendor,),
                status=batch.status,
                eligible_count=0,
                excluded_future_count=0,
                reason=batch.reason,
            )
        eligible = tuple(
            sorted(
                (
                    record
                    for record in batch.records
                    if getattr(record, timestamp_name) <= as_of
                ),
                key=lambda record: getattr(record, timestamp_name),
            )
        )
        excluded = len(batch.records) - len(eligible)
        return eligible, _coverage(
            dataset=dataset,
            batch=batch,
            eligible_count=len(eligible),
            excluded_future_count=excluded,
        )

    @staticmethod
    def _price_coverage(snapshot: SnapshotManifest) -> DatasetCoverage:
        return DatasetCoverage(
            dataset=EquityETFDataset.PRICE,
            vendors=(snapshot.vendor,),
            status=snapshot.quality_status,
            eligible_count=int(snapshot.metadata.get("observations", 0)),
            excluded_future_count=0,
            reason="immutable normalized price snapshot",
        )

    @staticmethod
    def _bundle(
        *,
        bundle_id: UUID | None,
        instrument: InstrumentContract,
        as_of: datetime,
        retrieved_at: datetime,
        price_snapshot: SnapshotManifest,
        filings: tuple[FilingRecord, ...],
        fundamentals: tuple[FundamentalFact, ...],
        news: tuple[NewsRecord, ...],
        fund_profile: ETFProfile | None,
        coverage: tuple[DatasetCoverage, ...],
    ) -> EquityETFSnapshotBundle:
        quality = max((item.status for item in coverage), key=QUALITY_PRIORITY.__getitem__)
        reasons = tuple(
            f"{item.dataset.value}: {item.reason}"
            for item in coverage
            if item.status is not DataQualityStatus.OK
        )
        return EquityETFSnapshotBundle(
            bundle_id=bundle_id or uuid4(),
            instrument_id=instrument.instrument_id,
            asset_class=instrument.asset_class,
            as_of=as_of,
            retrieved_at=retrieved_at,
            price_snapshot_id=price_snapshot.snapshot_id,
            filings=filings,
            fundamentals=fundamentals,
            news=news,
            fund_profile=fund_profile,
            coverage=coverage,
            quality_status=quality,
            quality_reasons=reasons,
        )

    def _persist(
        self,
        *,
        owner_id: UUID,
        bundle: EquityETFSnapshotBundle,
        pipeline_id: str,
    ) -> tuple[SnapshotManifest, EquityETFSnapshotBundle]:
        price_snapshot = self.repository.get_snapshot(bundle.price_snapshot_id)
        if price_snapshot is None:
            raise ValueError("bundle price snapshot no longer exists")
        source_times = [
            value
            for value in (price_snapshot.source_start, price_snapshot.source_end)
            if value is not None
        ]
        source_times.extend(item.filed_at for item in bundle.filings)
        source_times.extend(item.filed_at for item in bundle.fundamentals)
        source_times.extend(item.published_at for item in bundle.news)
        if bundle.fund_profile is not None:
            source_times.append(bundle.fund_profile.holdings_as_of)
        content = json.dumps(
            bundle.model_dump(mode="json"),
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        content_hash = "sha256:" + hashlib.sha256(content).hexdigest()
        manifest = SnapshotManifest(
            snapshot_id=bundle.bundle_id,
            instrument_id=bundle.instrument_id,
            dataset="equity_etf.bundle",
            vendor=pipeline_id,
            as_of=bundle.as_of,
            retrieved_at=bundle.retrieved_at,
            source_start=min(source_times) if source_times else None,
            source_end=max(source_times) if source_times else None,
            content_hash=content_hash,
            quality_status=bundle.quality_status,
            quality_reasons=bundle.quality_reasons,
            metadata={
                "asset_class": bundle.asset_class.value,
                "price_snapshot_id": str(bundle.price_snapshot_id),
                "coverage": [item.model_dump(mode="json") for item in bundle.coverage],
            },
        )
        self.repository.add_snapshot(manifest)
        existing = self.repository.get_snapshot_artifact(manifest.snapshot_id, owner_id)
        if existing is not None:
            if existing.content_hash != manifest.content_hash:
                raise ImmutableRecordConflict("snapshot artifact already has different content")
            return manifest, bundle
        self.artifacts.create(
            owner_id=owner_id,
            kind=ArtifactKind.SNAPSHOT_PAYLOAD,
            media_type="application/vnd.tradingagents.equity-etf-snapshot+json",
            content=content,
            instrument_id=bundle.instrument_id,
            snapshot_id=manifest.snapshot_id,
            created_at=bundle.retrieved_at,
            expected_hash=content_hash,
        )
        return manifest, bundle
