"""Consistent OK/STALE/NO_DATA/UNAVAILABLE/COVERAGE_GAP/INVALID semantics."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from tradingagents.contracts import DataHealthProbe, DataQualityStatus
from tradingagents.platform.artifacts import ArtifactService, LocalArtifactStore
from tradingagents.platform.data_health import DataHealthEngine
from tradingagents.platform.persistence import (
    Database,
    PlatformRepository,
    downgrade_database,
    upgrade_database,
)

AS_OF = datetime(2026, 9, 20, 20, tzinfo=UTC)
EVALUATED_AT = AS_OF + timedelta(minutes=5)


def _probe(dataset, **updates):
    values = {
        "dataset": dataset,
        "vendor": "fixture-vendor",
        "instrument_id": uuid4(),
        "as_of": AS_OF,
        "checked_at": EVALUATED_AT,
        "source_available": True,
        "coverage_supported": True,
        "schema_valid": True,
        "identity_valid": True,
        "eligible_records": 10,
        "excluded_future_records": 0,
        "latest_eligible_source_at": AS_OF - timedelta(minutes=1),
        "freshness_limit_seconds": 300,
    }
    values.update(updates)
    return DataHealthProbe(**values)


@pytest.mark.unit
def test_engine_classifies_all_six_statuses_without_conflation():
    probes = (
        _probe("ok"),
        _probe(
            "stale",
            latest_eligible_source_at=AS_OF - timedelta(minutes=10),
        ),
        _probe("no-data", eligible_records=0, latest_eligible_source_at=None),
        _probe(
            "unavailable",
            source_available=False,
            eligible_records=0,
            latest_eligible_source_at=None,
        ),
        _probe(
            "coverage",
            coverage_supported=False,
            eligible_records=0,
            latest_eligible_source_at=None,
        ),
        _probe("invalid", schema_valid=False),
    )
    report = DataHealthEngine().evaluate(
        probes=tuple(reversed(probes)), as_of=AS_OF, evaluated_at=EVALUATED_AT
    )
    statuses = {check.dataset: check.status for check in report.checks}
    assert statuses == {
        "ok": DataQualityStatus.OK,
        "stale": DataQualityStatus.STALE,
        "no-data": DataQualityStatus.NO_DATA,
        "unavailable": DataQualityStatus.UNAVAILABLE,
        "coverage": DataQualityStatus.COVERAGE_GAP,
        "invalid": DataQualityStatus.INVALID,
    }
    assert report.overall_status is DataQualityStatus.INVALID
    assert report.summary.total == 6
    assert report.summary.ok == report.summary.stale == report.summary.no_data == 1
    assert report.summary.unavailable == report.summary.coverage_gap == 1
    assert report.summary.invalid == 1


@pytest.mark.unit
def test_future_only_is_coverage_gap_but_future_eligible_is_invalid():
    engine = DataHealthEngine()
    future_only = engine.classify(
        _probe(
            "news",
            eligible_records=0,
            excluded_future_records=3,
            latest_eligible_source_at=None,
        )
    )
    assert future_only.status is DataQualityStatus.COVERAGE_GAP
    future_eligible = engine.classify(
        _probe(
            "price",
            latest_eligible_source_at=AS_OF + timedelta(seconds=1),
        )
    )
    assert future_eligible.status is DataQualityStatus.INVALID


@pytest.mark.unit
def test_contradictory_unavailable_payload_is_invalid_not_no_data():
    check = DataHealthEngine.classify(
        _probe("price", source_available=False, eligible_records=1)
    )
    assert check.status is DataQualityStatus.INVALID
    assert "cannot contain" in check.reason


@pytest.mark.unit
def test_report_is_deterministic_and_duplicate_identity_fails_closed():
    first = _probe("price", instrument_id=None, vendor="alpha")
    second = _probe("fundamentals", instrument_id=None, vendor="beta")
    engine = DataHealthEngine()
    report_a = engine.evaluate(
        probes=(first, second), as_of=AS_OF, evaluated_at=EVALUATED_AT
    )
    report_b = engine.evaluate(
        probes=(second, first), as_of=AS_OF, evaluated_at=EVALUATED_AT
    )
    assert report_a == report_b
    with pytest.raises(ValueError, match="unique identities"):
        engine.evaluate(
            probes=(first, first), as_of=AS_OF, evaluated_at=EVALUATED_AT
        )


@pytest.mark.unit
def test_data_health_report_round_trip_is_owner_scoped(tmp_path):
    url = f"sqlite:///{tmp_path / 'health.db'}"
    upgrade_database(url)
    database = Database(url)
    owner_id = uuid4()
    store = LocalArtifactStore(tmp_path / "artifacts")
    report = DataHealthEngine().evaluate(
        probes=(_probe("price"),), as_of=AS_OF, evaluated_at=EVALUATED_AT
    )
    try:
        with database.session() as session:
            DataHealthEngine(
                ArtifactService(store, PlatformRepository(session))
            ).persist(owner_id=owner_id, report=report)
        with database.session() as session:
            service = DataHealthEngine(ArtifactService(store, PlatformRepository(session)))
            assert service.load(owner_id=owner_id, report_id=report.report_id) == report
            with pytest.raises(LookupError, match="unavailable"):
                service.load(owner_id=uuid4(), report_id=report.report_id)
    finally:
        database.dispose()


@pytest.mark.integration
def test_postgresql_data_health_report_round_trip(tmp_path):
    url = os.getenv("TEST_POSTGRES_URL")
    if not url:
        pytest.skip("TEST_POSTGRES_URL is required for the PostgreSQL integration gate")
    upgrade_database(url)
    database = Database(url)
    owner_id = uuid4()
    store = LocalArtifactStore(tmp_path / "postgres-health-artifacts")
    report = DataHealthEngine().evaluate(
        probes=(_probe("price"),), as_of=AS_OF, evaluated_at=EVALUATED_AT
    )
    try:
        with database.session() as session:
            DataHealthEngine(
                ArtifactService(store, PlatformRepository(session))
            ).persist(owner_id=owner_id, report=report)
        with database.session() as session:
            loaded = DataHealthEngine(
                ArtifactService(store, PlatformRepository(session))
            ).load(owner_id=owner_id, report_id=report.report_id)
            assert loaded == report
    finally:
        database.dispose()
        downgrade_database(url)
