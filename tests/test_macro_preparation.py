"""Authenticated immutable macro preparation; offline SQLite/API evidence only."""

from datetime import timedelta
from threading import Event, Thread
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from tests.test_platform_fred import NOW, collect, documents
from tests.test_price_preparation import AAPL, ORIGIN, login
from tradingagents.contracts import DataQualityStatus
from tradingagents.dataflows.platform_fred import MacroPreparationError, collect_fred_series
from tradingagents.dataflows.platform_news import collect_yahoo_news
from tradingagents.platform.analysis.snapshots import load_snapshot_context
from tradingagents.platform.api import ApiSettings, create_app
from tradingagents.platform.artifacts import ArtifactService
from tradingagents.platform.auth import OwnerAuth
from tradingagents.platform.instruments import InstrumentMaster
from tradingagents.platform.instruments.catalog import INITIAL_INSTRUMENT_CATALOG
from tradingagents.platform.market_data.macro import MacroSnapshotService
from tradingagents.platform.persistence import Database, PlatformRepository, upgrade_database

PATH = f"/api/v1/instruments/{AAPL.instrument_id}/prepare-macro"
BODY = {"series_id": "DGS10"}


@pytest.fixture
def macro_api(tmp_path):
    url = f"sqlite:///{tmp_path / 'macro-api.db'}"
    upgrade_database(url)
    database = Database(url)
    with database.session() as session:
        OwnerAuth(session).bootstrap_owner("fixture@example.com", "synthetic-prepare-password", now=NOW)
        InstrumentMaster(PlatformRepository(session)).bootstrap()
    database.dispose()
    app = create_app(ApiSettings(database_url=url, artifact_root=tmp_path / "artifacts",
        allowed_origin=ORIGIN, secure_cookies=False, clock=lambda: NOW))
    with TestClient(app) as client:
        yield client, app


def test_macro_auth_csrf_reuse_owner_bytes_and_mixed_run_binding(macro_api):
    client, app = macro_api
    app.state.collect_fred_series = Mock(return_value=collect())
    assert client.post(PATH, headers={"Origin": ORIGIN}, json=BODY).status_code == 401
    headers = login(client)
    assert client.post(PATH, headers={"Origin": ORIGIN}, json=BODY).status_code == 403
    result = client.post(PATH, headers=headers, json=BODY).json()
    assert result["status"] == "ready" and not result["reused"]
    manifest = result["snapshot"]
    assert manifest["dataset"] == "macro" and manifest["quality_status"] == "OK"
    assert manifest["metadata"]["units"] == "Percent"
    assert manifest["metadata"]["observations"] == 1
    assert client.get("/api/v1/runs").json() == []  # Preparation itself never calls AI/queues research.
    assert client.post(PATH, headers=headers, json=BODY).json()["reused"] is True
    app.state.collect_fred_series.assert_called_once_with(AAPL, "DGS10", lookback_days=365, analysis_as_of=NOW)
    owner = UUID(client.get("/api/v1/auth/me").json()["owner_id"])
    with app.state.database.session() as session:
        repository = PlatformRepository(session)
        artifacts = ArtifactService(app.state.artifact_store, repository)
        service = MacroSnapshotService(repository, artifacts)
        with pytest.raises(LookupError):
            service.load(owner_id=uuid4(), snapshot_id=UUID(manifest["snapshot_id"]),
                instrument_id=AAPL.instrument_id, as_of=NOW, max_age_seconds=604800)
        _, loaded = service.load(owner_id=owner, snapshot_id=UUID(manifest["snapshot_id"]),
            instrument_id=AAPL.instrument_id, as_of=NOW, max_age_seconds=604800)
        assert loaded == collect()
    app.state.collect_yahoo_news = Mock(return_value=collect_yahoo_news(AAPL, clock=lambda: NOW,
        fetch=lambda *_: [{"content": {"title": "Synthetic independent headline", "pubDate": NOW.isoformat(),
            "provider": {"displayName": "Fixture publisher"},
            "canonicalUrl": {"url": "https://example.com/news"}}}]))
    news = client.post(f"/api/v1/instruments/{AAPL.instrument_id}/prepare-news", headers=headers).json()
    assert news["status"] == "ready", news
    ids = [manifest["snapshot_id"], news["snapshot"]["snapshot_id"]]
    accepted = client.post("/api/v1/runs", headers={**headers, "Idempotency-Key": "macro-mixed-fixture"},
        json={"instrument_id": str(AAPL.instrument_id), "analysis_as_of": NOW.isoformat(),
              "selected_analysts": ["news"], "decision_inputs": {"snapshots_by_analyst": {"news": ids},
                  "source_max_age_seconds": {"news": 604800}}})
    assert accepted.status_code == 202, accepted.text
    assert set(accepted.json()["run"]["snapshot_ids"]) == set(ids)
    from tradingagents.contracts import RunManifest
    run = RunManifest.model_validate(accepted.json()["run"])
    with app.state.database.session() as session:
        repository = PlatformRepository(session)
        context = load_snapshot_context(ArtifactService(app.state.artifact_store, repository), run,
            {"news": tuple(UUID(value) for value in ids)})
        assert {value.manifest.dataset for value in context.by_analyst["news"]} == {"macro", "news"}
        assert "DGS10" in context.reports(AAPL.instrument_id, ("news",))["news"]


@pytest.mark.parametrize("body", [{}, {"series_id": "../DGS10"}, {"series_id": "dgs10"},
    {"series_id": 1}, {**BODY, "lookback_days": "365"}, {**BODY, "lookback_days": True},
    {**BODY, "lookback_days": 0}, {**BODY, "lookback_days": 36526},
    {**BODY, "analysis_as_of": NOW.isoformat()}, {**BODY, "api_key": "SYNTHETIC"}])
def test_strict_body_and_no_historical_client_cutoff(macro_api, body):
    client, app = macro_api
    app.state.collect_fred_series = Mock()
    response = client.post(PATH, headers=login(client), json=body)
    assert response.status_code == 422
    app.state.collect_fred_series.assert_not_called()


@pytest.mark.parametrize("case,status", [("empty", "coverage_gap"), ("missing", "no_data"),
    ("stale", "stale"), ("invalid", "invalid"), ("unavailable", "unavailable")])
def test_failed_collections_audited_not_usable_then_cooldown(macro_api, case, status):
    client, app = macro_api
    raw = documents()
    if case == "empty":
        raw["series/observations"].update(observations=[], count=0)
    elif case == "missing":
        raw["series/observations"]["observations"][0]["value"] = "."
    elif case == "stale":
        raw["series/observations"]["observations"][0]["date"] = "2026-01-01"
    elif case == "invalid":
        raw["series"]["seriess"][0]["id"] = "OTHER"
    collection = collect(raw)
    if case == "unavailable":
        collection = collection.model_copy(update={"observations": (), "quality_status": DataQualityStatus.UNAVAILABLE,
            "reason": "vendor_request_failed"})
    app.state.collect_fred_series = Mock(return_value=collection)
    headers = login(client)
    response = client.post(PATH, headers=headers, json=BODY).json()
    assert response["status"] == status and response["snapshot"]["quality_status"] == status.upper()
    found = client.get(f"/api/v1/instruments/{AAPL.instrument_id}/snapshots",
        params={"analysis_as_of": NOW.isoformat(), "max_age_seconds": 604800}).json()
    assert found[0]["metadata_eligible"] is False
    retry = client.post(PATH, headers=headers, json=BODY).json()
    assert retry["status"] == "cooldown" and 1 <= retry["retry_after_seconds"] <= 60
    assert client.get("/api/v1/runs").json() == []


@pytest.mark.parametrize("update", [{"venue": "wrong"}, {"series_id": "OTHER"},
    {"analysis_as_of": NOW - timedelta(seconds=1)}, {"retrieved_at": NOW + timedelta(seconds=1)},
    {"observation_start": NOW.date() - timedelta(days=367)}])
def test_scope_mismatch_is_not_persisted(macro_api, update):
    client, app = macro_api
    app.state.collect_fred_series = Mock(return_value=collect().model_copy(update=update))
    response = client.post(PATH, headers=login(client), json=BODY).json()
    assert response["status"] == "invalid" and response["snapshot"] is None
    assert client.get(f"/api/v1/instruments/{AAPL.instrument_id}/snapshots",
        params={"analysis_as_of": NOW.isoformat(), "max_age_seconds": 604800}).json() == []


def test_reference_future_and_unknown_id_have_no_macro_substitute(macro_api):
    client, app = macro_api
    app.state.collect_fred_series = Mock()
    headers = login(client)
    future = INITIAL_INSTRUMENT_CATALOG[5].instrument
    assert client.post(f"/api/v1/instruments/{future.instrument_id}/prepare-macro",
        headers=headers, json=BODY).json()["status"] == "unsupported"
    assert client.post(f"/api/v1/instruments/{uuid4()}/prepare-macro", headers=headers, json=BODY).status_code == 404
    app.state.collect_fred_series.assert_not_called()


def test_window_changes_do_not_reuse_or_overwrite_history(macro_api):
    client, app = macro_api
    headers = login(client)

    def fetch(instrument, series_id, *, lookback_days, analysis_as_of):
        raw = documents()
        raw["series/observations"]["observation_start"] = (collect().vintage_date - timedelta(days=lookback_days)).isoformat()
        return collect_fred_series(instrument, series_id, clock=lambda: analysis_as_of,
            lookback_days=lookback_days, request=lambda path, _params: raw[path])

    app.state.collect_fred_series = Mock(side_effect=fetch)
    first = client.post(PATH, headers=headers, json=BODY).json()
    second = client.post(PATH, headers=headers, json={**BODY, "lookback_days": 36525}).json()
    assert first["status"] == second["status"] == "ready"
    assert second["reused"] is False
    assert first["snapshot"]["snapshot_id"] != second["snapshot"]["snapshot_id"]
    assert client.post(PATH, headers=headers, json=BODY).json()["snapshot"] == first["snapshot"]
    assert app.state.collect_fred_series.call_count == 2


def test_collection_exceptions_are_redacted_and_not_empty(macro_api):
    client, app = macro_api
    app.state.collect_fred_series = Mock(side_effect=RuntimeError("PRIVATE_DO_NOT_ECHO"))
    response = client.post(PATH, headers=login(client), json=BODY)
    assert response.json()["status"] == "unavailable" and response.json()["snapshot"] is None
    assert "PRIVATE_DO_NOT_ECHO" not in response.text


def test_fixture_refuses_live_macro(tmp_path):
    from scripts.web_fixture import create_app as fixture_app

    app = fixture_app(ApiSettings(database_url=f"sqlite:///{tmp_path / 'fixture.db'}",
        artifact_root=tmp_path / "artifacts", allowed_origin=ORIGIN, secure_cookies=False))
    with pytest.raises(MacroPreparationError, match="^unavailable$"):
        app.state.collect_fred_series(AAPL, "DGS10", lookback_days=365)
    app.state.database.dispose()


def test_preparation_lock_refuses_concurrent_headline_acquisition_then_releases(macro_api):
    client, app = macro_api
    headers = login(client)
    entered, release = Event(), Event()
    results = []

    def fetch(*_args, **_kwargs):
        entered.set()
        assert release.wait(5)
        return collect()

    app.state.collect_fred_series = fetch
    app.state.collect_yahoo_news = Mock()
    worker = Thread(target=lambda: results.append(client.post(PATH, headers=headers, json=BODY).json()))
    worker.start()
    try:
        assert entered.wait(5)
        response = client.post(f"/api/v1/instruments/{AAPL.instrument_id}/prepare-news", headers=headers)
        assert response.json()["status"] == "busy"
        app.state.collect_yahoo_news.assert_not_called()
    finally:
        release.set()
        worker.join(5)
    assert not worker.is_alive() and results[0]["status"] == "ready"
    assert client.post(PATH, headers=headers, json=BODY).json()["reused"] is True
