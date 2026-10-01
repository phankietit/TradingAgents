"""AAPL SEC current-vintage preparation remains owner-bound and optional."""

from unittest.mock import Mock
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from tests.test_platform_sec import NOW, collect, document, fact
from tests.test_price_preparation import AAPL, ORIGIN, login
from tradingagents.platform.analysis.fundamental_facts import SnapshotFundamentalFacts
from tradingagents.platform.analysis.snapshots import AnalysisSnapshot, SnapshotAnalysisContext
from tradingagents.platform.api import ApiSettings, create_app
from tradingagents.platform.artifacts import ArtifactService
from tradingagents.platform.auth import OwnerAuth
from tradingagents.platform.instruments import InstrumentMaster
from tradingagents.platform.instruments.catalog import INITIAL_INSTRUMENT_CATALOG
from tradingagents.platform.jobs.analysis import publication_warning
from tradingagents.platform.market_data.sec_facts import SecSnapshotService
from tradingagents.platform.persistence import Database, PlatformRepository, upgrade_database


@pytest.fixture
def sec_api(tmp_path):
    url = f"sqlite:///{tmp_path / 'sec-api.db'}"
    upgrade_database(url)
    database = Database(url)
    with database.session() as session:
        OwnerAuth(session).bootstrap_owner(
            "fixture@example.com", "synthetic-prepare-password", now=NOW,
        )
        InstrumentMaster(PlatformRepository(session)).bootstrap()
    database.dispose()
    app = create_app(ApiSettings(
        database_url=url, artifact_root=tmp_path / "artifacts",
        allowed_origin=ORIGIN, secure_cookies=False, clock=lambda: NOW,
    ))
    with TestClient(app) as client:
        yield client, app


def test_sec_prepare_auth_reuse_and_structured_fact_binding(sec_api):
    client, app = sec_api
    collection = collect(document([fact(100_000_000, "2025-11-01")]))
    app.state.collect_sec_facts = Mock(return_value=collection)
    path = f"/api/v1/instruments/{AAPL.instrument_id}/prepare-fundamentals"
    assert client.post(path, headers={"Origin": ORIGIN}).status_code == 401
    headers = login(client)
    assert client.post(path, headers={"Origin": ORIGIN}).status_code == 403
    first = client.post(path, headers=headers)
    assert first.status_code == 200, first.text
    result = first.json()
    assert result["status"] == "ready" and not result["reused"]
    manifest = result["snapshot"]
    assert manifest["dataset"] == "fundamentals"
    assert manifest["metadata"]["vintage"] == "current_retrieval_filed_date_filter"
    assert client.post(path, headers=headers).json()["reused"] is True
    app.state.collect_sec_facts.assert_called_once()
    owner = UUID(client.get("/api/v1/auth/me").json()["owner_id"])
    with app.state.database.session() as session:
        repository = PlatformRepository(session)
        service = SecSnapshotService(repository, ArtifactService(app.state.artifact_store, repository))
        loaded, payload = service.load(owner_id=owner, snapshot_id=UUID(manifest["snapshot_id"]),
            instrument_id=AAPL.instrument_id, as_of=NOW, max_age_seconds=31536000)
        artifact = repository.get_snapshot_artifact(loaded.snapshot_id, owner)
        content = ArtifactService(app.state.artifact_store, repository).read(artifact.artifact_id, owner)[1]
    assert payload.facts[0].filed_at.isoformat() == "2025-11-01"
    context = SnapshotAnalysisContext(as_of=NOW,
        by_analyst={"fundamentals": (AnalysisSnapshot(manifest=manifest, payload=content.decode()),)},
        source_max_age_seconds={"fundamentals": 31536000})
    reports = context.reports(AAPL.instrument_id, ("fundamentals",))
    assert "not a complete company profile" in publication_warning(context)
    import json
    source = json.loads(reports["fundamentals"])[0]
    facts = SnapshotFundamentalFacts(source)
    assert facts.resolve_fact("sec.total_assets.annual.2025-09-27.usd_millions") == 100
    assert facts.page()["facts"][0]["accession"] == "0000320193-26-000001"
    response = client.post("/api/v1/runs", headers={**headers,
        "Idempotency-Key": "sec-fixture-run-1"}, json={
        "instrument_id": str(AAPL.instrument_id),
        "analysis_as_of": NOW.isoformat(),
        "selected_analysts": ["fundamentals"],
        "decision_inputs": {"snapshots_by_analyst": {
            "fundamentals": [manifest["snapshot_id"]]},
            "source_max_age_seconds": {"fundamentals": 31536000}},
    })
    assert response.status_code == 202, response.text
    assert response.json()["run"]["snapshot_ids"] == [manifest["snapshot_id"]]
    older = client.get(f"/api/v1/instruments/{AAPL.instrument_id}/snapshots",
        params={"analysis_as_of": "2026-09-30T12:00:00Z",
                "max_age_seconds": 31536000}).json()
    assert older[0]["metadata_eligible"] is False
    assert "not_available_at_analysis_time" in older[0]["ineligibility_reasons"]


def test_sec_does_not_prepare_etf_or_futures(sec_api):
    client, app = sec_api
    app.state.collect_sec_facts = Mock()
    headers = login(client)
    for seed in (INITIAL_INSTRUMENT_CATALOG[1], INITIAL_INSTRUMENT_CATALOG[5]):
        response = client.post(
            f"/api/v1/instruments/{seed.instrument.instrument_id}/prepare-fundamentals",
            headers=headers)
        assert response.json()["status"] == "unsupported"
    app.state.collect_sec_facts.assert_not_called()


def test_synthetic_fixture_never_calls_live_sec(tmp_path):
    from scripts.web_fixture import create_app as fixture_app
    from tradingagents.dataflows.platform_sec import SecPreparationError

    app = fixture_app(ApiSettings(
        database_url=f"sqlite:///{tmp_path / 'fixture.db'}",
        artifact_root=tmp_path / "artifacts",
        allowed_origin=ORIGIN, secure_cookies=False,
    ))
    with pytest.raises(SecPreparationError, match="unavailable"):
        app.state.collect_sec_facts(AAPL)
    app.state.database.dispose()
