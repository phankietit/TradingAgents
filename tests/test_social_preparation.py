"""Real authenticated API/storage orchestration, synthetic source collector."""

from threading import Event, Thread
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest

from tests import test_macro_preparation as _api_fixture
from tests.test_platform_social import AAPL, NOW, collect, envelope
from tests.test_price_preparation import ORIGIN, login
from tradingagents.contracts import RunManifest
from tradingagents.dataflows.platform_social import SocialPreparationError
from tradingagents.platform.analysis.snapshots import load_snapshot_context
from tradingagents.platform.artifacts import ArtifactService
from tradingagents.platform.instruments.catalog import INITIAL_INSTRUMENT_CATALOG
from tradingagents.platform.persistence import PlatformRepository

PATH = f"/api/v1/instruments/{AAPL.instrument_id}/prepare-social"
macro_api = _api_fixture.macro_api


def test_auth_csrf_owner_reuse_full_source_run_pinning_no_ai(macro_api):
    client, app = macro_api
    app.state.collect_social = Mock(return_value=collect())
    body = {"vendor": "stocktwits"}
    assert client.post(PATH, headers={"Origin": ORIGIN}, json=body).status_code == 401
    headers = login(client)
    assert client.post(PATH, headers={"Origin": ORIGIN}, json=body).status_code == 403
    first = client.post(PATH, headers=headers, json=body).json()
    assert first["status"] == "ready" and not first["reused"]
    assert client.get("/api/v1/runs").json() == []
    second = client.post(PATH, headers=headers, json=body).json()
    assert second["reused"] and first["snapshot"] == second["snapshot"]
    app.state.collect_social.assert_called_once_with(AAPL, "stocktwits", analysis_as_of=NOW)
    app.state.collect_social = Mock(return_value=collect(vendor="reddit"))
    other = client.post(PATH, headers=headers, json={"vendor": "reddit"}).json()
    assert other["status"] == "ready" and other["snapshot"]["snapshot_id"] != first["snapshot"]["snapshot_id"]
    ids = [first["snapshot"]["snapshot_id"], other["snapshot"]["snapshot_id"]]
    response = client.post("/api/v1/runs", headers={**headers, "Idempotency-Key": "social-fixture"},
        json={"instrument_id": str(AAPL.instrument_id), "analysis_as_of": NOW.isoformat(),
            "selected_analysts": ["social"], "decision_inputs": {"snapshots_by_analyst": {"social": ids},
                "source_max_age_seconds": {"social": 604800}}})
    assert response.status_code == 202
    run = RunManifest.model_validate(response.json()["run"])
    with app.state.database.session() as session:
        context = load_snapshot_context(ArtifactService(app.state.artifact_store, PlatformRepository(session)), run,
            {"social": tuple(UUID(value) for value in ids)})
        assert {source.manifest.vendor for source in context.by_analyst["social"]} == {"reddit", "stocktwits"}


@pytest.mark.parametrize("body", [{}, {"vendor": "X"}, {"vendor": "https://evil.invalid"},
    {"vendor": "stocktwits", "analysis_as_of": NOW.isoformat()},
    {"vendor": "reddit", "api_key": "PRIVATE_DO_NOT_ECHO"}])
def test_strict_original_vendor_only(macro_api, body):
    client, app = macro_api
    app.state.collect_social = Mock()
    response = client.post(PATH, headers=login(client), json=body)
    assert response.status_code == 422 and "PRIVATE_DO_NOT_ECHO" not in response.text
    app.state.collect_social.assert_not_called()


@pytest.mark.parametrize("raw,status", [(envelope([]), "no_data"), (b"invalid", "invalid")])
def test_failures_audited_cooldown_and_never_job(macro_api, raw, status):
    client, app = macro_api
    app.state.collect_social = Mock(return_value=collect(raw))
    headers = login(client)
    response = client.post(PATH, headers=headers, json={"vendor": "stocktwits"}).json()
    assert response["status"] == status and response["snapshot"]["quality_status"] == status.upper()
    response = client.post(PATH, headers=headers, json={"vendor": "stocktwits"}).json()
    assert response["status"] == "cooldown"
    assert client.get("/api/v1/runs").json() == []


def test_mismatch_refuses_without_snapshot_or_job(macro_api):
    client, app = macro_api
    app.state.collect_social = Mock(return_value=collect().model_copy(update={"venue": "wrong"}))
    result = client.post(PATH, headers=login(client), json={"vendor": "stocktwits"}).json()
    assert result["status"] == "invalid" and result["snapshot"] is None
    assert client.get("/api/v1/runs").json() == []


def test_reference_future_and_unknown_id_no_substitute(macro_api):
    client, app = macro_api
    app.state.collect_social = Mock()
    headers = login(client)
    future = next(row.instrument for row in INITIAL_INSTRUMENT_CATALOG
        if row.instrument.canonical_symbol == "NQ=F")
    result = client.post(f"/api/v1/instruments/{future.instrument_id}/prepare-social",
        headers=headers, json={"vendor": "reddit"}).json()
    assert result["status"] == "unsupported" and result["snapshot"] is None
    assert client.post(f"/api/v1/instruments/{uuid4()}/prepare-social",
        headers=headers, json={"vendor": "reddit"}).status_code == 404
    app.state.collect_social.assert_not_called()


def test_actual_concurrent_macro_refused_while_social_acquires_then_lock_released(macro_api):
    client, app = macro_api
    headers = login(client)
    entered, release = Event(), Event()
    results = []

    def fetch(*_args, **_kwargs):
        entered.set()
        assert release.wait(5)
        return collect()

    app.state.collect_social = fetch
    app.state.collect_fred_series = Mock()
    worker = Thread(target=lambda: results.append(client.post(PATH, headers=headers,
        json={"vendor": "stocktwits"}).json()))
    worker.start()
    try:
        assert entered.wait(5)
        result = client.post(f"/api/v1/instruments/{AAPL.instrument_id}/prepare-macro",
            headers=headers, json={"series_id": "DGS10"}).json()
        assert result["status"] == "busy"
        app.state.collect_fred_series.assert_not_called()
    finally:
        release.set()
        worker.join(5)
    assert not worker.is_alive() and results[0]["status"] == "ready"
    assert client.post(PATH, headers=headers, json={"vendor": "stocktwits"}).json()["reused"] is True


def test_fixture_refuses_live_social(tmp_path):
    from scripts.web_fixture import create_app as fixture_app
    from tradingagents.platform.api import ApiSettings

    app = fixture_app(ApiSettings(database_url=f"sqlite:///{tmp_path / 'fixture.db'}",
        artifact_root=tmp_path / "artifacts", allowed_origin=ORIGIN, secure_cookies=False))
    try:
        for vendor in ("reddit", "stocktwits"):
            with pytest.raises(SocialPreparationError, match="^unavailable$"):
                app.state.collect_social(AAPL, vendor)
    finally:
        app.state.database.dispose()
