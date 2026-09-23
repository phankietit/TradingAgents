"""Authenticated FastAPI contract, authorization, CSRF, and idempotency evidence."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from tradingagents.contracts import (
    ArtifactKind,
    AssetClass,
    InstrumentContract,
    RunManifest,
    RunStatus,
    Tradability,
)
from tradingagents.platform.api import ApiSettings, create_app
from tradingagents.platform.api.runtime import load_api_settings
from tradingagents.platform.artifacts import ArtifactService, LocalArtifactStore
from tradingagents.platform.auth import OwnerAuth
from tradingagents.platform.persistence import Database, PlatformRepository, upgrade_database

NOW = datetime(2026, 9, 23, 12, 0, tzinfo=UTC)
ORIGIN = "http://testserver"
PASSWORD = "correct horse battery staple"


@pytest.fixture
def api_context(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'api.db'}"
    artifact_root = tmp_path / "artifacts"
    upgrade_database(database_url)
    database = Database(database_url)
    owner_id = uuid4()
    instrument = InstrumentContract(
        instrument_id=uuid4(),
        symbol="AAPL",
        canonical_symbol="AAPL",
        display_name="Apple Inc.",
        asset_class=AssetClass.EQUITY,
        tradability=Tradability.INVESTABLE,
        venue="NASDAQ",
        quote_currency="USD",
        timezone="America/New_York",
        session_calendar="XNYS",
        benchmark_symbol="SPY",
    )
    other_run = RunManifest(
        run_id=uuid4(),
        owner_id=uuid4(),
        instrument_id=instrument.instrument_id,
        analysis_as_of=NOW - timedelta(days=1),
        status=RunStatus.QUEUED,
        created_at=NOW,
        selected_analysts=("market",),
        llm_provider="openai",
        quick_model="quick",
        deep_model="deep",
        config_hash="sha256:" + "f" * 64,
        prompt_version="1",
    )
    with database.session() as session:
        principal = OwnerAuth(session).bootstrap_owner(
            "owner@example.com", PASSWORD, owner_id=owner_id, now=NOW
        )
        repository = PlatformRepository(session)
        repository.add_instrument(instrument)
        repository.save_run(other_run)
        artifact = ArtifactService(LocalArtifactStore(artifact_root), repository).create(
            owner_id=owner_id,
            kind=ArtifactKind.ANALYSIS_REPORT,
            media_type="text/markdown",
            content=b"# Private owner report",
            created_at=NOW,
        )
        other_artifact = ArtifactService(LocalArtifactStore(artifact_root), repository).create(
            owner_id=uuid4(),
            kind=ArtifactKind.ANALYSIS_REPORT,
            media_type="text/plain",
            content=b"other owner",
            created_at=NOW,
        )
    database.dispose()

    settings = ApiSettings(
        database_url=database_url,
        artifact_root=artifact_root,
        allowed_origin=ORIGIN,
        secure_cookies=False,
        quick_model="quick",
        deep_model="deep",
        clock=lambda: NOW,
    )
    app = create_app(settings)
    with TestClient(app) as client:
        yield {
            "client": client,
            "principal": principal,
            "instrument": instrument,
            "other_run": other_run,
            "artifact": artifact,
            "other_artifact": other_artifact,
        }


def _login(client: TestClient):
    response = client.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN},
        json={"email": "owner@example.com", "password": PASSWORD},
    )
    assert response.status_code == 200
    return response


def _csrf_headers(client: TestClient, **extra):
    headers = {"Origin": ORIGIN, "X-CSRF-Token": client.cookies.get("ta_csrf")}
    headers.update(extra)
    return headers


def _run_payload(instrument_id):
    return {
        "instrument_id": str(instrument_id),
        "analysis_as_of": (NOW - timedelta(days=1)).isoformat(),
        "selected_analysts": ["market", "news"],
    }


@pytest.mark.unit
def test_health_security_headers_and_authentication_boundary(api_context):
    client = api_context["client"]
    live = client.get("/health/live")
    ready = client.get("/health/ready")
    assert live.json() == {"status": "ok"}
    assert ready.json() == {"status": "ready"}
    assert live.headers["x-frame-options"] == "DENY"
    assert client.get("/api/v1/instruments").status_code == 401

    wrong_origin = client.post(
        "/api/v1/auth/login",
        headers={"Origin": "https://evil.example"},
        json={"email": "owner@example.com", "password": PASSWORD},
    )
    assert wrong_origin.status_code == 403
    wrong_password = client.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN},
        json={"email": "owner@example.com", "password": "wrong password value"},
    )
    assert wrong_password.status_code == 401
    rejected_password = "x" * 1025
    invalid = client.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN},
        json={"email": "owner@example.com", "password": rejected_password},
    )
    assert invalid.status_code == 422
    assert rejected_password not in invalid.text


@pytest.mark.unit
def test_login_sets_private_session_and_me_uses_server_principal(api_context):
    client = api_context["client"]
    response = _login(client)
    assert response.json()["owner_id"] == str(api_context["principal"].owner_id)
    assert "HttpOnly" in response.headers.get_list("set-cookie")[0]
    assert client.cookies.get("ta_session")
    assert client.cookies.get("ta_csrf")
    assert client.get("/api/v1/auth/me").json()["email"] == "owner@example.com"


@pytest.mark.unit
def test_mutation_requires_origin_and_session_bound_csrf(api_context):
    client = api_context["client"]
    _login(client)
    payload = _run_payload(api_context["instrument"].instrument_id)
    missing_csrf = client.post(
        "/api/v1/runs",
        headers={"Origin": ORIGIN, "Idempotency-Key": "run-request-001"},
        json=payload,
    )
    assert missing_csrf.status_code == 403
    forged_csrf = client.post(
        "/api/v1/runs",
        headers={
            "Origin": ORIGIN,
            "Idempotency-Key": "run-request-001",
            "X-CSRF-Token": "forged-csrf-token-value-000000000000",
        },
        json=payload,
    )
    assert forged_csrf.status_code == 403


@pytest.mark.unit
def test_create_run_is_idempotent_and_exposes_owner_scoped_status(api_context):
    client = api_context["client"]
    _login(client)
    headers = _csrf_headers(client, **{"Idempotency-Key": "run-request-001"})
    payload = _run_payload(api_context["instrument"].instrument_id)
    first = client.post("/api/v1/runs", headers=headers, json=payload)
    second = client.post("/api/v1/runs", headers=headers, json=payload)
    assert first.status_code == second.status_code == 202
    assert first.json() == second.json()
    run_id = first.json()["run"]["run_id"]
    job_id = first.json()["job"]["job_id"]
    assert client.get(f"/api/v1/runs/{run_id}").status_code == 200
    assert client.get(f"/api/v1/jobs/{job_id}").json()["status"] == "queued"
    assert [item["run_id"] for item in client.get("/api/v1/runs").json()] == [run_id]

    changed = dict(payload)
    changed["selected_analysts"] = ["market"]
    conflict = client.post("/api/v1/runs", headers=headers, json=changed)
    assert conflict.status_code == 409


@pytest.mark.unit
def test_future_run_and_cross_owner_resources_fail_closed(api_context):
    client = api_context["client"]
    _login(client)
    future = _run_payload(api_context["instrument"].instrument_id)
    future["analysis_as_of"] = (NOW + timedelta(seconds=1)).isoformat()
    response = client.post(
        "/api/v1/runs",
        headers=_csrf_headers(client, **{"Idempotency-Key": "run-request-future"}),
        json=future,
    )
    assert response.status_code == 422
    assert client.get(f"/api/v1/runs/{api_context['other_run'].run_id}").status_code == 404
    assert (
        client.get(f"/api/v1/artifacts/{api_context['other_artifact'].artifact_id}").status_code
        == 404
    )


@pytest.mark.unit
def test_cancel_queued_run_and_download_private_artifact(api_context):
    client = api_context["client"]
    _login(client)
    created = client.post(
        "/api/v1/runs",
        headers=_csrf_headers(client, **{"Idempotency-Key": "run-request-cancel"}),
        json=_run_payload(api_context["instrument"].instrument_id),
    ).json()
    run_id = created["run"]["run_id"]
    cancelled = client.post(f"/api/v1/runs/{run_id}/cancel", headers=_csrf_headers(client))
    assert cancelled.json()["status"] == "cancelled"
    assert client.get(f"/api/v1/runs/{run_id}").json()["status"] == "cancelled"

    artifact = client.get(f"/api/v1/artifacts/{api_context['artifact'].artifact_id}")
    assert artifact.status_code == 200
    assert artifact.content == b"# Private owner report"
    assert artifact.headers["content-type"] == "application/octet-stream"


@pytest.mark.unit
def test_openapi_contract_has_cookie_auth_and_no_caller_owner_field(api_context):
    schema = api_context["client"].get("/openapi.json").json()
    security = schema["components"]["securitySchemes"]["APIKeyCookie"]
    assert security == {"type": "apiKey", "in": "cookie", "name": "ta_session"}
    run_request = schema["components"]["schemas"]["RunCreateRequest"]
    assert "owner_id" not in run_request["properties"]
    assert "/api/v1/runs" in schema["paths"]
    assert "/api/v1/runs/{run_id}/cancel" in schema["paths"]


@pytest.mark.unit
def test_runtime_settings_are_explicit_and_secure_by_default(tmp_path):
    with pytest.raises(RuntimeError, match="TRADINGAGENTS_DATABASE_URL"):
        load_api_settings({})
    settings = load_api_settings(
        {
            "TRADINGAGENTS_DATABASE_URL": f"sqlite:///{tmp_path / 'api.db'}",
            "TRADINGAGENTS_ARTIFACT_ROOT": str(tmp_path / "artifacts"),
            "TRADINGAGENTS_ALLOWED_ORIGIN": "https://portfolio.example.com",
        }
    )
    assert settings.secure_cookies is True
    assert settings.database_url not in repr(settings)
    with pytest.raises(ValueError, match="HTTPS"):
        load_api_settings(
            {
                "TRADINGAGENTS_DATABASE_URL": f"sqlite:///{tmp_path / 'api.db'}",
                "TRADINGAGENTS_ARTIFACT_ROOT": str(tmp_path / "artifacts"),
                "TRADINGAGENTS_ALLOWED_ORIGIN": "http://portfolio.example.com",
            }
        )
