"""Authenticated FastAPI contract, authorization, CSRF, and idempotency evidence."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timedelta
from io import StringIO
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from tradingagents._compat import UTC
from tradingagents.contracts import (
    ArtifactKind,
    AssetClass,
    CashBalance,
    InstrumentAliasContract,
    InstrumentContract,
    PolicyContract,
    PortfolioSnapshot,
    PriceInterval,
    RunManifest,
    RunStatus,
    Tradability,
)
from tradingagents.platform.api import ApiSettings, create_app
from tradingagents.platform.api.runtime import load_api_settings
from tradingagents.platform.artifacts import ArtifactService, LocalArtifactStore
from tradingagents.platform.auth import OwnerAuth
from tradingagents.platform.market_data import TimeSeriesSnapshotService, normalize_time_series
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
        time_series = normalize_time_series(
            instrument=instrument,
            dataset="ohlcv.daily",
            interval=PriceInterval.ONE_DAY,
            as_of=NOW - timedelta(hours=1),
            annualization_periods=252,
            bars=(
                {
                    "timestamp": NOW - timedelta(days=2),
                    "open": 100,
                    "high": 102,
                    "low": 99,
                    "close": 101,
                    "adjusted_close": 100,
                    "volume": 1_000_000,
                },
                {
                    "timestamp": NOW - timedelta(days=1),
                    "open": 101,
                    "high": 104,
                    "low": 100,
                    "close": 103,
                    "adjusted_close": 102,
                    "volume": 1_100_000,
                },
            ),
        )
        time_series_snapshot = TimeSeriesSnapshotService(
            repository,
            ArtifactService(LocalArtifactStore(artifact_root), repository),
        ).persist(
            owner_id=owner_id,
            series=time_series,
            vendor="test-fixture",
            retrieved_at=NOW,
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
            "time_series_snapshot": time_series_snapshot,
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
@pytest.mark.parametrize("case", ["valid", "future_policy", "wrong_asset", "foreign_policy"])
def test_risk_run_inputs_bind_owner_policy_asset_and_timestamp(api_context, case):
    client = api_context["client"]
    _login(client)
    owner = api_context["principal"].owner_id
    portfolio = PortfolioSnapshot(portfolio_id=uuid4(), owner_id=owner, as_of=NOW,
        base_currency="USD", cash=(CashBalance(currency="USD", amount="10000"),), positions=(),
        net_asset_value="10000", content_hash="sha256:" + "c" * 64)
    policy = PolicyContract(policy_id=uuid4(), owner_id=uuid4() if case == "foreign_policy" else owner,
        name="Synthetic risk input QA", policy_version="1", asset_class="crypto" if case == "wrong_asset" else "equity",
        effective_at=NOW + timedelta(days=1) if case == "future_policy" else NOW, parameters={})
    with client.app.state.database.session() as session:
        repository = PlatformRepository(session)
        repository.add_portfolio_snapshot(portfolio)
        repository.add_policy(policy)
    payload = {"instrument_id": str(api_context["instrument"].instrument_id),
        "analysis_as_of": NOW.isoformat(), "selected_analysts": ["market"], "decision_inputs": {
            "snapshots_by_analyst": {"market": [str(api_context["time_series_snapshot"].snapshot_id)]},
            "source_max_age_seconds": {"market": 172800}, "portfolio_snapshot_id": str(portfolio.portfolio_id),
            "policy_id": str(policy.policy_id), "policy_version": "1", "requested_target_weight": .2}}
    result = client.post("/api/v1/runs", headers=_csrf_headers(client, **{"Idempotency-Key": "risk-input-qa-001"}), json=payload)
    assert result.status_code == (202 if case == "valid" else 422)


@pytest.mark.unit
def test_analysis_profile_is_authenticated_and_uses_backend_roles(api_context):
    client = api_context["client"]
    path = f"/api/v1/instruments/{api_context['instrument'].instrument_id}/analysis-profile"
    assert client.get(path).status_code == 401
    _login(client)
    assert client.get(path).json() == {"name": "equity", "allowed_analysts": ["market", "social", "news", "fundamentals"], "investable": True}
    assert client.get(f"/api/v1/instruments/{uuid4()}/analysis-profile").status_code == 404


@pytest.mark.unit
def test_watchlist_is_persistent_idempotent_and_csrf_protected(api_context):
    client = api_context["client"]
    instrument_id = api_context["instrument"].instrument_id
    path = f"/api/v1/watchlist/{instrument_id}"
    assert client.get("/api/v1/watchlist").status_code == 401
    assert client.put(path, headers={"Origin": ORIGIN}).status_code == 401
    _login(client)
    assert client.get("/api/v1/watchlist").json() == []
    assert client.put(path, headers={"Origin": ORIGIN}).status_code == 403
    assert client.put(path, headers=_csrf_headers(client)).status_code == 200
    assert client.put(path, headers=_csrf_headers(client)).status_code == 200
    assert client.get("/api/v1/watchlist").json() == [api_context["instrument"].model_dump(mode="json")]
    assert client.get("/api/v1/watchlist", params={"offset": 1}).json() == []
    assert client.get("/api/v1/watchlist", params={"limit": 201}).status_code == 422
    assert client.put(f"/api/v1/watchlist/{uuid4()}", headers=_csrf_headers(client)).status_code == 404
    assert client.post("/api/v1/auth/logout", headers=_csrf_headers(client)).status_code == 200
    _login(client)
    assert len(client.get("/api/v1/watchlist").json()) == 1
    # A different owner cannot read or remove the current owner's entry.
    with client.app.state.database.session() as session:
        repository = PlatformRepository(session)
        assert repository.list_watchlist(uuid4()) == ()
        repository.remove_watchlist_entry(uuid4(), instrument_id)
    assert len(client.get("/api/v1/watchlist").json()) == 1
    assert client.delete(path, headers={"Origin": ORIGIN}).status_code == 403
    assert client.delete(path, headers=_csrf_headers(client)).status_code == 200
    assert client.delete(path, headers=_csrf_headers(client)).status_code == 200
    assert client.get("/api/v1/watchlist").json() == []


@pytest.mark.unit
def test_snapshot_discovery_reports_temporal_eligibility_without_claiming_content_validation(api_context):
    client = api_context["client"]
    instrument_id = api_context["instrument"].instrument_id
    path = f"/api/v1/instruments/{instrument_id}/snapshots"
    params = {"analysis_as_of": NOW.isoformat(), "max_age_seconds": 172800}
    assert client.get(path, params=params).status_code == 401
    _login(client)
    response = client.get(path, params=params)
    assert response.status_code == 200
    assert len(response.json()) == 1
    item = response.json()[0]
    assert item["snapshot"]["snapshot_id"] == str(api_context["time_series_snapshot"].snapshot_id)
    assert item["metadata_eligible"] is True
    assert item["content_validation"] == "required_on_run_creation"
    assert item["ineligibility_reasons"] == []
    stale = client.get(path, params={**params, "max_age_seconds": 0}).json()[0]
    assert stale["metadata_eligible"] is False
    assert "stale" in stale["ineligibility_reasons"]
    historical = client.get(path, params={**params, "analysis_as_of": (NOW - timedelta(days=2)).isoformat()}).json()[0]
    assert historical["metadata_eligible"] is False
    assert "not_available_at_analysis_time" in historical["ineligibility_reasons"]
    for changes in ({"analysis_as_of": "2026-09-23T12:00:00"},
                    {"analysis_as_of": (NOW + timedelta(days=1)).isoformat()},
                    {"max_age_seconds": -1}, {"limit": 201}, {"offset": -1}):
        assert client.get(path, params={**params, **changes}).status_code == 422
    assert client.get(path, params={**params, "offset": 1}).json() == []
    assert client.get(f"/api/v1/instruments/{uuid4()}/snapshots", params=params).status_code == 404
    # The manifest alone grants no access: payload ownership is required.
    from sqlalchemy import update

    from tradingagents.platform.persistence.models import ArtifactRow
    with client.app.state.database.session() as session:
        session.execute(update(ArtifactRow).where(
            ArtifactRow.snapshot_id == api_context["time_series_snapshot"].snapshot_id
        ).values(owner_id=uuid4()))
    assert client.get(path, params=params).json() == []


@pytest.mark.unit
def test_workspace_discovery_is_owner_scoped_bounded_and_read_only(api_context):
    client = api_context["client"]
    assert client.get("/api/v1/portfolios").status_code == 401
    assert client.get("/api/v1/policies").status_code == 401
    owner_id = api_context["principal"].owner_id
    portfolio = PortfolioSnapshot(
        portfolio_id=uuid4(), owner_id=owner_id, as_of=NOW, base_currency="USD",
        cash=(CashBalance(currency="USD", amount="10000"),), positions=(),
        net_asset_value="10000", content_hash="sha256:" + "c" * 64,
    )
    policy = PolicyContract(
        policy_id=uuid4(), owner_id=owner_id, name="Fixture policy", policy_version="1.0.0",
        asset_class=AssetClass.EQUITY, effective_at=NOW, parameters={"max_weight": 0.1},
    )
    other_portfolio = portfolio.model_copy(update={"portfolio_id": uuid4(), "owner_id": uuid4()})
    other_policy = policy.model_copy(update={"policy_id": uuid4(), "owner_id": uuid4()})
    older = portfolio.model_copy(update={"portfolio_id": uuid4(), "as_of": NOW - timedelta(days=1)})
    with client.app.state.database.session() as session:
        repository = PlatformRepository(session)
        for item in (portfolio, older, other_portfolio):
            repository.add_portfolio_snapshot(item)
        for item in (policy, other_policy):
            repository.add_policy(item)
    _login(client)
    assert client.get("/api/v1/portfolios", params={"limit": 1}).json() == [portfolio.model_dump(mode="json")]
    assert client.get("/api/v1/portfolios", params={"limit": 1, "offset": 1}).json() == [older.model_dump(mode="json")]
    assert client.get(f"/api/v1/portfolios/{portfolio.portfolio_id}").json() == portfolio.model_dump(mode="json")
    assert client.get(f"/api/v1/portfolios/{other_portfolio.portfolio_id}").status_code == 404
    assert client.get(f"/api/v1/portfolios/{uuid4()}").status_code == 404
    assert client.get("/api/v1/policies").json() == [policy.model_dump(mode="json")]
    assert client.get("/api/v1/policies", params={"asset_class": "crypto"}).json() == []
    assert client.get(f"/api/v1/policies/{policy.policy_id}/1.0.0").json() == policy.model_dump(mode="json")
    assert client.get(f"/api/v1/policies/{other_policy.policy_id}/1.0.0").status_code == 404
    assert client.get(f"/api/v1/policies/{policy.policy_id}/unknown").status_code == 404
    for path in ("portfolios", "policies"):
        for params in ({"limit": 0}, {"limit": 201}, {"offset": -1}, {"offset": 100001}):
            assert client.get(f"/api/v1/{path}", params=params).status_code == 422
    assert client.get("/api/v1/policies", params={"asset_class": "unknown"}).status_code == 422


@pytest.mark.unit
def test_run_artifact_discovery_excludes_storage_and_other_owners(api_context):
    client = api_context["client"]
    owner_id = api_context["principal"].owner_id
    run = api_context["other_run"].model_copy(update={"run_id": uuid4(), "owner_id": owner_id})
    path = f"/api/v1/runs/{run.run_id}/artifacts"
    assert client.get(path).status_code == 401
    with client.app.state.database.session() as session:
        repository = PlatformRepository(session)
        repository.save_run(run)
        service = ArtifactService(client.app.state.artifact_store, repository)
        artifact = service.create(owner_id=owner_id, run_id=run.run_id,
            kind=ArtifactKind.ANALYSIS_REPORT, media_type="text/markdown",
            content=b"Synthetic report", created_at=NOW)
    _login(client)
    response = client.get(path)
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json()[0]["artifact_id"] == str(artifact.artifact_id)
    assert "storage_key" not in response.text
    assert "owner_id" not in response.text
    assert client.get(path, params={"offset": 1}).json() == []
    assert client.get(path, params={"limit": 201}).status_code == 422
    assert client.get(f"/api/v1/runs/{api_context['other_run'].run_id}/artifacts").status_code == 404
    assert client.get(f"/api/v1/runs/{uuid4()}/artifacts").status_code == 404


def test_benchmark_response_includes_owner_readable_provenance(api_context):
    client = api_context["client"]
    instrument = api_context["instrument"]
    owner_id = api_context["principal"].owner_id
    benchmark = instrument.model_copy(update={"instrument_id": uuid4(), "symbol": "SPY",
        "canonical_symbol": "SPY", "display_name": "Synthetic benchmark", "asset_class": AssetClass.ETF})
    with client.app.state.database.session() as session:
        repo = PlatformRepository(session)
        repo.add_instrument(benchmark)
        service = TimeSeriesSnapshotService(repo, ArtifactService(client.app.state.artifact_store, repo))
        _, series = service.load(owner_id=owner_id, instrument_id=instrument.instrument_id,
                                 dataset="ohlcv.daily", as_of=NOW)
        source = service.persist(owner_id=owner_id,
            series=series.model_copy(update={"instrument_id": benchmark.instrument_id}),
            vendor="SYNTHETIC BENCHMARK", retrieved_at=NOW)
    _login(client)
    path = f"/api/v1/instruments/{instrument.instrument_id}/timeseries"
    response = client.get(path, params={"benchmark_instrument_id": str(benchmark.instrument_id)})
    assert response.status_code == 200
    assert response.json()["benchmark_snapshot"] == source.model_dump(mode="json")
    assert response.json()["view"]["benchmark"]["aligned_observations"] == 2
    assert response.json()["view"]["benchmark"]["excess_return"] == 0
    assert client.get(path).json()["benchmark_snapshot"] is None
    assert client.get(path, params={"benchmark_instrument_id": str(benchmark.instrument_id),
                                   "as_of": (NOW - timedelta(hours=2)).isoformat()}).status_code == 404


def test_snapshot_run_inputs_are_owner_validated_and_idempotent(api_context):
    client = api_context["client"]
    _login(client)
    source_id = str(api_context["time_series_snapshot"].snapshot_id)
    payload = {"instrument_id": str(api_context["instrument"].instrument_id),
               "analysis_as_of": NOW.isoformat(), "selected_analysts": ["market"],
               "decision_inputs": {"snapshots_by_analyst": {"market": [source_id]},
                                   "source_max_age_seconds": {"market": 172800}}}
    headers = _csrf_headers(client, **{"Idempotency-Key": "snapshot-request-001"})
    first = client.post("/api/v1/runs", headers=headers, json=payload)
    assert first.status_code == 202, first.text
    second = client.post("/api/v1/runs", headers=headers, json=payload)
    assert second.json() == first.json()
    assert first.json()["run"]["snapshot_ids"] == [source_id]
    assert first.json()["job"]["payload"]["decision_inputs"]["snapshots_by_analyst"] == {"market": [source_id]}
    payload["decision_inputs"]["snapshots_by_analyst"]["market"] = [str(uuid4())]
    assert client.post("/api/v1/runs", headers=headers, json=payload).status_code == 409
    headers["Idempotency-Key"] = "snapshot-request-002"
    assert client.post("/api/v1/runs", headers=headers, json=payload).status_code == 422
    payload["decision_inputs"]["snapshots_by_analyst"] = {"news": [source_id]}
    assert client.post("/api/v1/runs", headers=headers, json=payload).status_code == 422


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
def test_csrf_bootstrap_authenticates_and_preserves_cookie_scope(api_context):
    client = api_context["client"]
    assert client.get("/api/v1/auth/csrf").status_code == 401
    login = _login(client)
    assert all("Path=/api/v1" in value for value in login.headers.get_list("set-cookie"))
    response = client.get("/api/v1/auth/csrf")
    assert response.status_code == 200
    assert response.json() == {"csrf_token": client.cookies.get("ta_csrf")}
    assert response.headers["cache-control"] == "no-store"
    assert "set-cookie" not in response.headers
    cross_origin = client.get("/api/v1/auth/csrf", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in cross_origin.headers
    logout = client.post("/api/v1/auth/logout", headers={
        "Origin": ORIGIN, "X-CSRF-Token": response.json()["csrf_token"],
    })
    assert logout.status_code == 200
    assert client.get("/api/v1/auth/csrf").status_code == 401


@pytest.mark.unit
@pytest.mark.parametrize("csrf_value", [None, "forged-csrf-token-value-000000000000"])
def test_csrf_bootstrap_rejects_missing_or_forged_cookie(api_context, csrf_value):
    client = api_context["client"]
    _login(client)
    client.cookies.delete("ta_csrf")
    if csrf_value is not None:
        client.cookies.set("ta_csrf", csrf_value, path="/api/v1")
    response = client.get("/api/v1/auth/csrf")
    assert response.status_code == 403
    assert response.json() == {"detail": "CSRF validation failed"}


@pytest.mark.unit
def test_csrf_bootstrap_rejects_expired_session(api_context):
    client = api_context["client"]
    _login(client)
    client.app.state.settings = replace(
        client.app.state.settings, clock=lambda: NOW + timedelta(days=1)
    )
    assert client.get("/api/v1/auth/csrf").status_code == 401


@pytest.mark.unit
def test_csrf_bootstrap_rejects_another_session_token(api_context):
    client = api_context["client"]
    _login(client)
    old_csrf = client.cookies.get("ta_csrf")
    _login(client)
    client.cookies.delete("ta_csrf")
    client.cookies.set("ta_csrf", old_csrf, path="/api/v1")
    assert client.get("/api/v1/auth/csrf").status_code == 403


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
def test_normalized_time_series_api_is_point_in_time_scoped(api_context):
    client = api_context["client"]
    instrument = api_context["instrument"]
    _login(client)
    response = client.get(
        f"/api/v1/instruments/{instrument.instrument_id}/timeseries",
        params={"dataset": "ohlcv.daily", "as_of": NOW.isoformat()},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["snapshot"]["snapshot_id"] == str(
        api_context["time_series_snapshot"].snapshot_id
    )
    assert body["view"]["statistics"]["price_basis"] == "adjusted_close"
    assert body["view"]["statistics"]["total_return"] == pytest.approx(0.02)
    assert len(body["view"]["series"]["bars"]) == 2

    future = client.get(
        f"/api/v1/instruments/{instrument.instrument_id}/timeseries",
        params={"as_of": (NOW + timedelta(seconds=1)).isoformat()},
    )
    assert future.status_code == 422
    before_snapshot = client.get(
        f"/api/v1/instruments/{instrument.instrument_id}/timeseries",
        params={"as_of": (NOW - timedelta(days=3)).isoformat()},
    )
    assert before_snapshot.status_code == 404
    missing_benchmark = client.get(
        f"/api/v1/instruments/{instrument.instrument_id}/timeseries",
        params={
            "as_of": NOW.isoformat(),
            "benchmark_instrument_id": str(uuid4()),
        },
    )
    assert missing_benchmark.status_code == 404


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
