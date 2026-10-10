"""Authenticated current-news preparation does not imply historical coverage."""

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from tests.test_price_preparation import AAPL, NOW, ORIGIN, login
from tradingagents.contracts import DataQualityStatus
from tradingagents.dataflows.platform_news import collect_yahoo_news
from tradingagents.platform.api import ApiSettings, create_app
from tradingagents.platform.auth import OwnerAuth
from tradingagents.platform.instruments import InstrumentMaster
from tradingagents.platform.instruments.catalog import INITIAL_INSTRUMENT_CATALOG
from tradingagents.platform.persistence import Database, PlatformRepository, upgrade_database


def _article():
    return {"content": {
        "title": "Research update", "summary": "Untrusted fixture text",
        "provider": {"displayName": "Fixture publisher"},
        "canonicalUrl": {"url": "https://example.com/news"},
        "pubDate": NOW.isoformat(),
    }}


def _collection(instrument, raw):
    return collect_yahoo_news(
        instrument, clock=lambda: NOW, fetch=lambda *_: raw,
    )


@pytest.fixture
def news_api(tmp_path):
    url = f"sqlite:///{tmp_path / 'news-api.db'}"
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


def test_news_prepare_auth_reuse_discovery_and_run_binding(news_api):
    client, app = news_api
    app.state.collect_yahoo_news = Mock(return_value=_collection(AAPL, [_article()]))
    path = f"/api/v1/instruments/{AAPL.instrument_id}/prepare-news"
    assert client.post(path, headers={"Origin": ORIGIN}).status_code == 401
    headers = login(client)
    assert client.post(path, headers={"Origin": ORIGIN}).status_code == 403
    first = client.post(path, headers=headers)
    assert first.status_code == 200, first.text
    result = first.json()
    assert result["status"] == "ready" and not result["reused"]
    assert result["snapshot"]["quality_status"] == "OK"
    assert result["snapshot"]["metadata"]["coverage"] == "recent_feed_not_exhaustive"
    assert client.post(path, headers=headers).json()["reused"] is True
    app.state.collect_yahoo_news.assert_called_once()
    discovery = client.get(
        f"/api/v1/instruments/{AAPL.instrument_id}/snapshots",
        params={"analysis_as_of": NOW.isoformat(), "max_age_seconds": 604800},
    ).json()
    assert discovery[0]["supported_analysts"] == ["news"]
    assert discovery[0]["metadata_eligible"] is True
    response = client.post(
        "/api/v1/runs",
        headers={**headers, "Idempotency-Key": "news-fixture-run-1"},
        json={
            "instrument_id": str(AAPL.instrument_id),
            "analysis_as_of": NOW.isoformat(),
            "selected_analysts": ["news"],
            "decision_inputs": {
                "snapshots_by_analyst": {"news": [result["snapshot"]["snapshot_id"]]},
                "source_max_age_seconds": {"news": 604800},
            },
        },
    )
    assert response.status_code == 202, response.text
    assert response.json()["run"]["snapshot_ids"] == [result["snapshot"]["snapshot_id"]]


def test_recent_news_publication_disclosure_is_not_model_optional(news_api):
    from uuid import UUID

    from tradingagents.platform.analysis.snapshots import AnalysisSnapshot, SnapshotAnalysisContext
    from tradingagents.platform.artifacts import ArtifactService
    from tradingagents.platform.jobs.analysis import publication_warning

    client, app = news_api
    app.state.collect_yahoo_news = Mock(return_value=_collection(AAPL, [_article()]))
    result = client.post(
        f"/api/v1/instruments/{AAPL.instrument_id}/prepare-news", headers=login(client),
    ).json()
    manifest = result["snapshot"]
    owner = UUID(client.get("/api/v1/auth/me").json()["owner_id"])
    with app.state.database.session() as session:
        repository = PlatformRepository(session)
        artifact = repository.get_snapshot_artifact(UUID(manifest["snapshot_id"]), owner)
        loaded = ArtifactService(app.state.artifact_store, repository).read(artifact.artifact_id, owner)
    context = SnapshotAnalysisContext(
        as_of=NOW,
        by_analyst={"news": (AnalysisSnapshot(manifest=manifest, payload=loaded[1].decode()),)},
        source_max_age_seconds={"news": 604800},
    )
    warning = publication_warning(context)
    assert "not an exhaustive" in warning
    assert "Thiếu nguồn là chưa có dữ liệu, không phải trung lập" in warning


@pytest.mark.parametrize("raw,status", [
    ([], DataQualityStatus.NO_DATA),
    ([{}], DataQualityStatus.INVALID),
])
def test_bad_news_is_audited_but_not_eligible(news_api, raw, status):
    client, app = news_api
    app.state.collect_yahoo_news = Mock(return_value=_collection(AAPL, raw))
    headers = login(client)
    path = f"/api/v1/instruments/{AAPL.instrument_id}/prepare-news"
    response = client.post(path, headers=headers)
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == status.value.lower()
    assert result["snapshot"]["quality_status"] == status.value
    discovery = client.get(
        f"/api/v1/instruments/{AAPL.instrument_id}/snapshots",
        params={"analysis_as_of": NOW.isoformat(), "max_age_seconds": 604800},
    ).json()
    assert discovery[0]["metadata_eligible"] is False
    assert client.post(path, headers=headers).json()["status"] == "cooldown"
    assert client.get("/api/v1/runs").json() == []


def test_reference_future_has_no_silent_news_substitute(news_api):
    client, app = news_api
    future = INITIAL_INSTRUMENT_CATALOG[5].instrument
    app.state.collect_yahoo_news = Mock()
    response = client.post(
        f"/api/v1/instruments/{future.instrument_id}/prepare-news", headers=login(client),
    )
    assert response.json()["status"] == "unsupported"
    app.state.collect_yahoo_news.assert_not_called()


def test_vendor_outage_does_not_publish_a_news_snapshot(news_api):
    client, app = news_api
    app.state.collect_yahoo_news = Mock(
        return_value=_collection(AAPL, [])
            .model_copy(update={"quality_status": DataQualityStatus.UNAVAILABLE,
                                "reason": "vendor_request_failed"})
    )
    response = client.post(
        f"/api/v1/instruments/{AAPL.instrument_id}/prepare-news",
        headers=login(client),
    )
    assert response.json()["status"] == "unavailable"
    assert response.json()["snapshot"]["quality_status"] == "UNAVAILABLE"


def test_synthetic_fixture_never_calls_live_news(tmp_path):
    from scripts.web_fixture import create_app as fixture_app
    from tradingagents.dataflows.platform_news import NewsPreparationError

    app = fixture_app(ApiSettings(
        database_url=f"sqlite:///{tmp_path / 'fixture.db'}",
        artifact_root=tmp_path / "artifacts",
        allowed_origin=ORIGIN, secure_cookies=False,
    ))
    with pytest.raises(NewsPreparationError, match="unavailable"):
        app.state.collect_yahoo_news(AAPL)
    app.state.database.dispose()
