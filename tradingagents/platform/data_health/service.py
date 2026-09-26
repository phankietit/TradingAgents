"""Classify and aggregate data health without masking missing vendor evidence."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime
from uuid import NAMESPACE_URL, UUID, uuid5

from tradingagents.contracts import (
    ArtifactKind,
    DataHealthCheck,
    DataHealthProbe,
    DataHealthReport,
    DataHealthSummary,
    DataQualityStatus,
    worst_data_quality_status,
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


class DataHealthEngine:
    def __init__(self, artifacts: ArtifactService | None = None):
        self.artifacts = artifacts

    def evaluate(
        self,
        *,
        probes: tuple[DataHealthProbe, ...],
        as_of: datetime,
        evaluated_at: datetime,
    ) -> DataHealthReport:
        if not probes:
            raise ValueError("at least one data health probe is required")
        if any(probe.as_of != as_of for probe in probes):
            raise ValueError("all data health probes must match report as_of")
        ordered = tuple(
            sorted(
                probes,
                key=lambda item: (
                    str(item.instrument_id) if item.instrument_id is not None else "",
                    item.dataset.casefold(),
                    item.vendor.casefold(),
                ),
            )
        )
        identities = [
            (item.instrument_id, item.dataset.casefold(), item.vendor.casefold())
            for item in ordered
        ]
        if len(identities) != len(set(identities)):
            raise ValueError("data health probes must have unique identities")
        checks = tuple(self.classify(probe) for probe in ordered)
        counts = Counter(item.status for item in checks)
        summary = DataHealthSummary(
            ok=counts[DataQualityStatus.OK],
            stale=counts[DataQualityStatus.STALE],
            no_data=counts[DataQualityStatus.NO_DATA],
            unavailable=counts[DataQualityStatus.UNAVAILABLE],
            coverage_gap=counts[DataQualityStatus.COVERAGE_GAP],
            invalid=counts[DataQualityStatus.INVALID],
        )
        report_material = {
            "as_of": as_of.isoformat(),
            "evaluated_at": evaluated_at.isoformat(),
            "probes": [item.model_dump(mode="json") for item in ordered],
            "checks": [item.model_dump(mode="json") for item in checks],
            "summary": summary.model_dump(mode="json"),
        }
        report_hash = "sha256:" + hashlib.sha256(
            _canonical_bytes(report_material)
        ).hexdigest()
        return DataHealthReport(
            report_id=uuid5(NAMESPACE_URL, report_hash),
            as_of=as_of,
            evaluated_at=evaluated_at,
            report_hash=report_hash,
            overall_status=worst_data_quality_status(
                [item.status for item in checks]
            ),
            summary=summary,
            checks=checks,
        )

    @staticmethod
    def classify(probe: DataHealthProbe) -> DataHealthCheck:
        status: DataQualityStatus
        reason: str
        contradictory_payload = not probe.source_available and (
            probe.eligible_records > 0
            or probe.excluded_future_records > 0
            or probe.latest_eligible_source_at is not None
        )
        future_eligible = (
            probe.latest_eligible_source_at is not None
            and probe.latest_eligible_source_at > probe.as_of
        )
        if not probe.schema_valid:
            status = DataQualityStatus.INVALID
            reason = "source payload failed schema validation"
        elif not probe.identity_valid:
            status = DataQualityStatus.INVALID
            reason = "source payload failed instrument identity validation"
        elif contradictory_payload:
            status = DataQualityStatus.INVALID
            reason = "unavailable source cannot contain observed records"
        elif future_eligible:
            status = DataQualityStatus.INVALID
            reason = "latest eligible source timestamp exceeds as_of"
        elif not probe.source_available:
            status = DataQualityStatus.UNAVAILABLE
            reason = "vendor, authentication, network, or rate limit prevented observation"
        elif not probe.coverage_supported:
            status = DataQualityStatus.COVERAGE_GAP
            reason = "source cannot cover the requested point-in-time window"
        elif probe.eligible_records == 0 and probe.excluded_future_records > 0:
            status = DataQualityStatus.COVERAGE_GAP
            reason = "source rows exist but none were eligible by as_of"
        elif probe.eligible_records == 0:
            status = DataQualityStatus.NO_DATA
            reason = "reachable source returned no eligible records"
        elif probe.latest_eligible_source_at is None:
            status = DataQualityStatus.INVALID
            reason = "eligible records require a latest source timestamp"
        else:
            age = (probe.as_of - probe.latest_eligible_source_at).total_seconds()
            if age > probe.freshness_limit_seconds:
                status = DataQualityStatus.STALE
                reason = "latest eligible source record exceeds the freshness limit"
            else:
                status = DataQualityStatus.OK
                reason = "eligible source data passed coverage and freshness checks"
        age_seconds = None
        if probe.latest_eligible_source_at is not None and not future_eligible:
            age_seconds = (probe.as_of - probe.latest_eligible_source_at).total_seconds()
        return DataHealthCheck(
            dataset=probe.dataset,
            vendor=probe.vendor,
            instrument_id=probe.instrument_id,
            status=status,
            reason=reason,
            eligible_records=probe.eligible_records,
            excluded_future_records=probe.excluded_future_records,
            latest_eligible_source_at=probe.latest_eligible_source_at,
            age_seconds=age_seconds,
            diagnostics=probe.diagnostics,
        )

    def persist(self, *, owner_id: UUID, report: DataHealthReport):
        return self._require_artifacts().create(
            owner_id=owner_id,
            kind=ArtifactKind.DATA_HEALTH_REPORT,
            media_type="application/vnd.tradingagents.data-health+json",
            content=_canonical_bytes(report.model_dump(mode="json")),
            artifact_id=report.report_id,
            created_at=report.evaluated_at,
        )

    def load(self, *, owner_id: UUID, report_id: UUID) -> DataHealthReport:
        loaded = self._require_artifacts().read(report_id, owner_id)
        if loaded is None:
            raise LookupError("data health report is unavailable")
        manifest, payload = loaded
        if manifest.kind is not ArtifactKind.DATA_HEALTH_REPORT:
            raise ValueError("artifact is not a data health report")
        report = DataHealthReport.model_validate_json(payload)
        if report.report_id != report_id:
            raise ValueError("data health payload identity does not match its artifact")
        return report

    def _require_artifacts(self) -> ArtifactService:
        if self.artifacts is None:
            raise RuntimeError("artifact service is required for persistence")
        return self.artifacts
