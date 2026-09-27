"""Current-price preparation: real contracts, fake provider, no paid/network calls."""

from datetime import datetime, timedelta
from unittest.mock import Mock

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from tradingagents._compat import UTC
from tradingagents.dataflows.platform_prices import (
    PricePreparationError,
    approved_symbol,
    history_start,
    normalize_yahoo,
    session_closes,
)
from tradingagents.platform.api import ApiSettings, create_app
from tradingagents.platform.auth import OwnerAuth
from tradingagents.platform.instruments import InstrumentMaster
from tradingagents.platform.instruments.catalog import INITIAL_INSTRUMENT_CATALOG
from tradingagents.platform.persistence import Database, PlatformRepository, upgrade_database

NOW = datetime(2026, 9, 23, 12, tzinfo=UTC)
AAPL = INITIAL_INSTRUMENT_CATALOG[0].instrument
ORIGIN = "http://testserver"


def price_frame(instrument=AAPL, now=NOW):
    days = [
        day
        for day, close in session_closes(instrument, now).items()
        if history_start(now) <= close <= now - timedelta(hours=1)
    ]
    return pd.DataFrame(
        {
            "Open": 100.0,
            "High": 102.0,
            "Low": 99.0,
            "Close": 101.0,
            "Adj Close": 100.5,
            "Volume": 1000.0,
        },
        index=pd.DatetimeIndex(days).tz_localize(instrument.timezone),
    )


def metadata(instrument=AAPL):
    return {
        "symbol": instrument.canonical_symbol,
        "currency": "USD",
        "instrumentType": "CRYPTOCURRENCY"
        if instrument.asset_class.value == "crypto"
        else "EQUITY",
        "exchangeTimezoneName": instrument.timezone,
    }


def test_completed_sessions_timezone_and_crypto():
    for instrument in (AAPL, INITIAL_INSTRUMENT_CATALOG[-1].instrument):
        series = normalize_yahoo(instrument, price_frame(instrument), metadata(instrument), now=NOW)
        assert series.as_of == NOW
        assert all(bar.timestamp <= NOW - timedelta(hours=1) for bar in series.bars)
        assert len(series.bars) > (1800 if instrument.asset_class.value == "crypto" else 1200)
        assert series.bars[-1].close == 101
        assert series.bars[-1].adjusted_close == 100.5


@pytest.mark.parametrize(
    "case,code",
    [
        ("empty", "no_data"),
        ("gap", "coverage_gap"),
        ("stale", "stale"),
        ("duplicate", "invalid"),
        ("nan", "invalid"),
        ("currency", "invalid"),
    ],
)
def test_failures_are_distinct(case, code):
    frame, meta = price_frame(), metadata()
    if case == "empty":
        frame = frame.iloc[:0]
    if case == "gap":
        frame = frame.drop(frame.index[10])
    if case == "stale":
        frame = frame.iloc[:-1]
    if case == "duplicate":
        frame = pd.concat([frame, frame.iloc[-1:]])
    if case == "nan":
        frame.iloc[10, 0] = float("nan")
    if case == "currency":
        meta["currency"] = "EUR"
    with pytest.raises(PricePreparationError, match=code):
        normalize_yahoo(AAPL, frame, meta, now=NOW)


def test_excludes_open_session_and_rejects_unapproved_identity():
    frame = price_frame()
    frame.loc[pd.Timestamp(NOW.date(), tz=AAPL.timezone)] = [100, 102, 99, 101, 100.5, 1000]
    assert len(normalize_yahoo(AAPL, frame, metadata(), now=NOW).bars) == len(frame) - 1
    with pytest.raises(PricePreparationError, match="unsupported"):
        approved_symbol(AAPL.model_copy(update={"quote_currency": "EUR"}))
    with pytest.raises(PricePreparationError, match="unsupported"):
        approved_symbol(INITIAL_INSTRUMENT_CATALOG[5].instrument)


@pytest.fixture
def prepared_api(tmp_path):
    url = f"sqlite:///{tmp_path / 'prepare.db'}"
    upgrade_database(url)
    database = Database(url)
    with database.session() as session:
        OwnerAuth(session).bootstrap_owner(
            "fixture@example.com", "synthetic-prepare-password", now=NOW
        )
        InstrumentMaster(PlatformRepository(session)).bootstrap()
    database.dispose()
    app = create_app(
        ApiSettings(
            database_url=url,
            artifact_root=tmp_path / "artifacts",
            allowed_origin=ORIGIN,
            secure_cookies=False,
            clock=lambda: NOW,
        )
    )
    app.state.fetch_daily_prices = Mock(
        return_value=normalize_yahoo(AAPL, price_frame(), metadata(), now=NOW)
    )
    with TestClient(app) as client:
        yield client, app


def login(client):
    assert (
        client.post(
            "/api/v1/auth/login",
            headers={"Origin": ORIGIN},
            json={"email": "fixture@example.com", "password": "synthetic-prepare-password"},
        ).status_code
        == 200
    )
    return {"Origin": ORIGIN, "X-CSRF-Token": client.cookies["ta_csrf"]}


def test_prepare_auth_reuse_and_snapshot_discovery(prepared_api):
    client, app = prepared_api
    path = f"/api/v1/instruments/{AAPL.instrument_id}/prepare-data"
    assert client.post(path, headers={"Origin": ORIGIN}).status_code == 401
    headers = login(client)
    assert client.post(path, headers={"Origin": ORIGIN}).status_code == 403
    first = client.post(path, headers=headers)
    assert first.status_code == 200, first.text
    assert first.json()["status"] == "ready", first.text
    assert first.json()["reused"] is False
    second = client.post(path, headers=headers).json()
    assert second["reused"] is True
    assert first.json()["snapshot"]["snapshot_id"] == second["snapshot"]["snapshot_id"]
    assert app.state.fetch_daily_prices.call_count == 1
    result = client.get(
        f"/api/v1/instruments/{AAPL.instrument_id}/snapshots",
        params={"analysis_as_of": NOW.isoformat(), "max_age_seconds": 604800},
    ).json()
    assert result[0]["metadata_eligible"] is True
    assert result[0]["supported_analysts"] == ["market"]
    assert client.get("/api/v1/runs").json() == []
    historical = client.get(
        f"/api/v1/instruments/{AAPL.instrument_id}/snapshots",
        params={
            "analysis_as_of": (NOW - timedelta(hours=1)).isoformat(),
            "max_age_seconds": 604800,
        },
    ).json()
    assert historical[0]["metadata_eligible"] is False


@pytest.mark.parametrize(
    "code", ["no_data", "stale", "coverage_gap", "invalid", "unavailable", "rate_limited"]
)
def test_failed_prepare_does_not_publish_or_call_ai(prepared_api, code):
    client, app = prepared_api
    app.state.fetch_daily_prices.side_effect = PricePreparationError(code)
    headers = login(client)
    path = f"/api/v1/instruments/{AAPL.instrument_id}/prepare-data"
    assert client.post(path, headers=headers).json()["status"] == code
    retry = client.post(path, headers=headers).json()
    assert retry["status"] == "cooldown"
    assert retry["last_failure"] == (None if code == "invalid" else code)
    assert 1 <= retry["retry_after_seconds"] <= 60
    assert app.state.fetch_daily_prices.call_count == 1
    assert (
        client.get(
            f"/api/v1/instruments/{AAPL.instrument_id}/snapshots",
            params={"analysis_as_of": NOW.isoformat(), "max_age_seconds": 604800},
        ).json()
        == []
    )


def test_reference_future_is_explicitly_unsupported(prepared_api):
    client, app = prepared_api
    future = INITIAL_INSTRUMENT_CATALOG[5].instrument
    response = client.post(
        f"/api/v1/instruments/{future.instrument_id}/prepare-data", headers=login(client)
    )
    assert response.json()["status"] == "unsupported"
    app.state.fetch_daily_prices.assert_not_called()


def test_calendar_early_close_and_dst():
    from datetime import date

    closes = session_closes(AAPL, NOW)
    assert closes[date(2025, 11, 28)].hour == 18
    assert closes[date(2026, 1, 5)].hour == 21
    assert closes[date(2026, 7, 6)].hour == 20


def test_five_calendar_years_preserve_leap_day_semantics():
    now = datetime(2024, 2, 29, 12, tzinfo=UTC)
    assert history_start(now) == datetime(2019, 2, 28, 12, tzinfo=UTC)
    assert history_start(NOW) == datetime(2021, 9, 23, 12, tzinfo=UTC)


@pytest.mark.parametrize("vendor", ["yfinance.daily.v1", "yfinance.daily.v2"])
def test_short_saved_history_is_preserved_but_not_reused(prepared_api, vendor):
    from uuid import UUID

    from tradingagents.platform.artifacts import ArtifactService
    from tradingagents.platform.market_data import TimeSeriesSnapshotService

    client, app = prepared_api
    headers = login(client)
    owner = UUID(client.get("/api/v1/auth/me").json()["owner_id"])
    series = app.state.fetch_daily_prices.return_value
    short_series = series.model_copy(update={"bars": series.bars[-250:]})
    with app.state.database.session() as session:
        repository = PlatformRepository(session)
        old = TimeSeriesSnapshotService(
            repository, ArtifactService(app.state.artifact_store, repository)
        ).persist(owner_id=owner, series=short_series, vendor=vendor, retrieved_at=NOW)
    result = client.post(
        f"/api/v1/instruments/{AAPL.instrument_id}/prepare-data", headers=headers
    ).json()
    assert result["status"] == "ready"
    assert result["reused"] is False
    assert result["snapshot"]["snapshot_id"] != str(old.snapshot_id)
    assert result["snapshot"]["metadata"]["observations"] > 1200
    with app.state.database.session() as session:
        assert PlatformRepository(session).get_snapshot(old.snapshot_id) == old
    app.state.fetch_daily_prices.assert_called_once()


def test_short_acquisition_cannot_publish_as_five_years(prepared_api):
    client, app = prepared_api
    series = app.state.fetch_daily_prices.return_value
    app.state.fetch_daily_prices.return_value = series.model_copy(
        update={"bars": series.bars[-250:]}
    )
    result = client.post(
        f"/api/v1/instruments/{AAPL.instrument_id}/prepare-data", headers=login(client)
    ).json()
    assert result["status"] == "coverage_gap"
    assert result["snapshot"] is None


def test_acquisition_has_hard_deadline(monkeypatch):
    import subprocess

    from tradingagents.dataflows.platform_prices import fetch_daily_prices

    run = Mock(side_effect=subprocess.TimeoutExpired("synthetic", 45))
    monkeypatch.setattr(subprocess, "run", run)
    with pytest.raises(PricePreparationError, match="unavailable"):
        fetch_daily_prices(AAPL)
    assert run.call_args.kwargs["timeout"] == 45


def test_corrupt_saved_evidence_is_not_reused(prepared_api, monkeypatch):
    from tradingagents.platform.artifacts import ArtifactIntegrityError

    client, app = prepared_api
    headers = login(client)
    path = f"/api/v1/instruments/{AAPL.instrument_id}/prepare-data"
    assert client.post(path, headers=headers).json()["status"] == "ready"
    monkeypatch.setattr(
        app.state.artifact_store, "get_bytes", Mock(side_effect=ArtifactIntegrityError("fixture"))
    )
    assert client.post(path, headers=headers).json()["status"] == "invalid"
    assert app.state.fetch_daily_prices.call_count == 1


def test_synthetic_fixture_never_calls_yahoo(tmp_path):
    from scripts.web_fixture import create_app as fixture_app

    app = fixture_app(
        ApiSettings(
            database_url=f"sqlite:///{tmp_path / 'fixture.db'}",
            artifact_root=tmp_path / "artifacts",
            allowed_origin=ORIGIN,
            secure_cookies=False,
        )
    )
    with pytest.raises(PricePreparationError, match="unavailable"):
        app.state.fetch_daily_prices(AAPL)
    app.state.database.dispose()
