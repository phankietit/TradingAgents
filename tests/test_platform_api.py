"""Authenticated FastAPI contract, authorization, CSRF, and idempotency evidence."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from io import StringIO
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from tradingagents.contracts import (
    ArtifactKind,
    AssetClass,
    InstrumentAliasContract,
    InstrumentContract,
    RunManifest,
    RunStatus,
    Tradability,
)
from tradingagents.platform.api import ApiSettings, create_app
from tradingagents.platform.api.runtime import load_api_settings
from tradingagents.platform.artifacts import ArtifactService, LocalArtifactStore
from tradingagents.platform.auth import OwnerAuth
from tradingagents.platform.observability import configure_platform_logging
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
        repository.add_instrument_alias(
            InstrumentAliasContract.create(
                instrument_id=instrument.instrument_id,
                namespace="common",
                alias="APPLE",
            )
        )
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
    assert live.headers["x-request-id"]
    supplied = client.get("/health/live", headers={"X-Request-ID": "request-1234"})
    assert supplied.headers["x-request-id"] == "request-1234"
    replaced = client.get("/health/live", headers={"X-Request-ID": "bad"})
    assert replaced.headers["x-request-id"] != "bad"
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
def test_instrument_master_api_filters_resolves_and_returns_aliases(api_context):
    client = api_context["client"]
    instrument = api_context["instrument"]
    _login(client)

    equities = client.get("/api/v1/instruments", params={"asset_class": "equity"})
    assert equities.status_code == 200
    assert [item["canonical_symbol"] for item in equities.json()] == ["AAPL"]
    assert client.get(
        "/api/v1/instruments", params={"tradability": "reference_only"}
    ).json() == []
    assert client.get("/api/v1/instruments", params={"venue": "NASDAQ"}).status_code == 200
    assert client.get("/api/v1/instruments", params={"asset_class": "unknown"}).status_code == 422

    resolved = client.get("/api/v1/instruments/resolve", params={"alias": " apple "})
    assert resolved.status_code == 200
    assert resolved.json()["instrument"]["instrument_id"] == str(instrument.instrument_id)
    assert {item["namespace"] for item in resolved.json()["aliases"]} == {
        "canonical",
        "common",
    }
    assert client.get(
        "/api/v1/instruments/resolve",
        params={"alias": "APPLE", "namespace": "common"},
    ).status_code == 200
    assert client.get(
        f"/api/v1/instruments/{instrument.instrument_id}"
    ).status_code == 200
    assert client.get(
        "/api/v1/instruments/resolve", params={"alias": "missing"}
    ).status_code == 404


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

    events = client.get(f"/api/v1/runs/{run_id}/events")
    assert events.status_code == 200
    assert events.headers["content-type"].startswith("text/event-stream")
    assert "retry: 2000\n\n" in events.text
    assert "id: 1\nevent: run.queued\n" in events.text
    assert "id: 2\nevent: run.cancelled\n" in events.text
    resumed = client.get(f"/api/v1/runs/{run_id}/events", headers={"Last-Event-ID": "1"})
    assert "event: run.queued" not in resumed.text
    assert "id: 2\nevent: run.cancelled\n" in resumed.text
    metrics = client.get("/api/v1/observability/metrics")
    assert "tradingagents_sse_connections_active 0" in metrics.text

    artifact = client.get(f"/api/v1/artifacts/{api_context['artifact'].artifact_id}")
    assert artifact.status_code == 200
    assert artifact.content == b"# Private owner report"
    assert artifact.headers["content-type"] == "application/octet-stream"


@pytest.mark.unit
def test_sse_cursor_and_owner_are_validated_before_streaming(api_context):
    client = api_context["client"]
    _login(client)
    run_id = api_context["other_run"].run_id
    assert client.get(f"/api/v1/runs/{run_id}/events").status_code == 404
    invalid = client.get(f"/api/v1/runs/{run_id}/events", headers={"Last-Event-ID": "not-a-number"})
    assert invalid.status_code == 400


@pytest.mark.unit
def test_openapi_contract_has_cookie_auth_and_no_caller_owner_field(api_context):
    schema = api_context["client"].get("/openapi.json").json()
    security = schema["components"]["securitySchemes"]["APIKeyCookie"]
    assert security == {"type": "apiKey", "in": "cookie", "name": "ta_session"}
    run_request = schema["components"]["schemas"]["RunCreateRequest"]
    assert "owner_id" not in run_request["properties"]
    assert "/api/v1/runs" in schema["paths"]
    assert "/api/v1/runs/{run_id}/cancel" in schema["paths"]
    assert "/api/v1/runs/{run_id}/events" in schema["paths"]
    assert "/api/v1/observability/metrics" in schema["paths"]


@pytest.mark.unit
def test_metrics_are_authenticated_and_use_route_templates(api_context):
    client = api_context["client"]
    assert client.get("/api/v1/observability/metrics").status_code == 401
    _login(client)
    run_id = api_context["other_run"].run_id
    assert client.get(f"/api/v1/runs/{run_id}").status_code == 404
    response = client.get("/api/v1/observability/metrics")
    assert response.status_code == 200
    assert "/api/v1/runs/{run_id}" in response.text
    assert str(run_id) not in response.text


@pytest.mark.unit
def test_http_log_uses_correlation_and_route_template_without_private_request_data(api_context):
    client = api_context["client"]
    _login(client)
    stream = StringIO()
    configure_platform_logging(stream=stream)
    run_id = api_context["other_run"].run_id
    response = client.get(
        f"/api/v1/runs/{run_id}?private_query=do-not-log",
        headers={"X-Request-ID": "request-log-1"},
    )
    assert response.status_code == 404
    records = [json.loads(line) for line in stream.getvalue().splitlines()]
    record = records[-1]
    assert record["request_id"] == "request-log-1"
    assert record["route"] == "/api/v1/runs/{run_id}"
    assert str(run_id) not in stream.getvalue()
    assert "do-not-log" not in stream.getvalue()


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
