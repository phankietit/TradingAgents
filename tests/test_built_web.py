"""Same-origin built UI serving, file confinement, and unchanged API auth gates."""

from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tradingagents.platform.api import ApiSettings, create_app
from tradingagents.platform.api.runtime import load_api_settings
from tradingagents.platform.api.web import CSP
from tradingagents.platform.auth import OwnerAuth
from tradingagents.platform.persistence import Database, upgrade_database

ORIGIN = "http://127.0.0.1:8000"


@pytest.fixture
def built_settings(tmp_path):
    root = tmp_path / "dist"
    assets = root / "assets"
    assets.mkdir(parents=True)
    (root / "index.html").write_text('<html><div id="root"></div><script src="/assets/app.js"></script></html>')
    (assets / "app.js").write_text("console.log('synthetic fixture');")
    (assets / "app.css").write_text("body { color: white; }")
    for name in ["app.js.map", "private.json", ".hidden.js", "source.tsx"]:
        (assets / name).write_text("MUST NOT BE SERVED")
    private = tmp_path / "private.js"
    private.write_text("MUST NOT BE SERVED")
    (assets / "outside.js").symlink_to(private)
    (root / ".env").write_text("SYNTHETIC_SECRET=not-real")
    url = f"sqlite:///{tmp_path / 'api.db'}"
    upgrade_database(url)
    database = Database(url)
    with database.session() as session:
        OwnerAuth(session).bootstrap_owner("fixture@example.com", "synthetic-local-password")
    database.dispose()
    return ApiSettings(database_url=url, artifact_root=tmp_path / "artifacts",
                       allowed_origin=ORIGIN, secure_cookies=False, web_root=root)


def test_index_assets_headers_and_api_routing(built_settings):
    with TestClient(create_app(built_settings), base_url=ORIGIN) as client:
        for path in ["/", "/index.html"]:
            response = client.get(path)
            assert response.status_code == 200
            assert '<div id="root">' in response.text
            assert response.headers["content-security-policy"] == CSP
            assert response.headers["cache-control"] == "no-store"
            assert response.headers["x-frame-options"] == "DENY"
            assert response.headers["x-content-type-options"] == "nosniff"
            assert response.headers["referrer-policy"] == "no-referrer"
            assert "camera=()" in response.headers["permissions-policy"]
            assert client.head(path).status_code == 200
        assert "javascript" in client.get("/assets/app.js").headers["content-type"]
        assert "text/css" in client.get("/assets/app.css").headers["content-type"]
        assert client.get("/api/v1/auth/me").status_code == 401
        assert client.get("/health/live").json() == {"status": "ok"}
        for path in ["/markets", "/api/unknown", "/api/v1/unknown", "/assets/missing.js"]:
            response = client.get(path)
            assert response.status_code == 404
            assert 'id="root"' not in response.text  # Never disguise API/file misses as HTML.


@pytest.mark.parametrize("path", [
    "/.env", "/src/main.tsx", "/package.json", "/assets/app.js.map", "/assets/private.json",
    "/assets/.hidden.js", "/assets/source.tsx", "/assets/outside.js", "/assets/%2e%2e/private.js",
    "/assets/%2e%2e/%2e%2e/private.js", "/assets/%2e%2e/index.html",
])
def test_static_confinement(built_settings, path):
    with TestClient(create_app(built_settings), base_url=ORIGIN) as client:
        response = client.get(path)
        assert response.status_code == 404
        assert "MUST NOT BE SERVED" not in response.text
        assert "SYNTHETIC_SECRET" not in response.text


def test_same_origin_auth_csrf_and_rebinding_boundary(built_settings):
    with TestClient(create_app(built_settings), base_url=ORIGIN) as client:
        credentials = {"email": "fixture@example.com", "password": "synthetic-local-password"}
        assert client.post("/api/v1/auth/login", json=credentials).status_code == 403
        assert client.post("/api/v1/auth/login", json=credentials,
                           headers={"Origin": "http://other.invalid"}).status_code == 403
        assert client.post("/api/v1/auth/login", json=credentials,
                           headers={"Origin": ORIGIN}).status_code == 200
        assert client.get("/api/v1/auth/me").status_code == 200
        csrf = client.get("/api/v1/auth/csrf").json()["csrf_token"]
        assert client.post("/api/v1/auth/logout", headers={"Origin": ORIGIN}).status_code == 403
        for path in ["/", "/assets/app.js", "/api/v1/auth/me", "/health/live"]:
            assert client.get(path, headers={"Host": "rebound.invalid:8000"}).status_code == 400
        assert client.post("/api/v1/auth/logout", headers={"Origin": ORIGIN, "X-CSRF-Token": csrf}).status_code == 200
        assert client.get("/api/v1/auth/me").status_code == 401


def test_static_is_opt_in_and_rejects_missing_build_or_nonlocal_origin(built_settings, tmp_path):
    with TestClient(create_app(replace(built_settings, web_root=None)), base_url=ORIGIN) as client:
        assert client.get("/").status_code == 404
        assert client.get("/assets/app.js").status_code == 404
    with pytest.raises(ValueError, match="built index"):
        create_app(replace(built_settings, web_root=tmp_path))
    with pytest.raises(ValueError, match="built web requires"):
        replace(built_settings, allowed_origin="http://public.invalid:8000")
    with pytest.raises(ValueError, match="built web requires"):
        replace(built_settings, allowed_origin="http://127.0.0.1")


def test_web_runtime_settings_and_port_guard(built_settings, monkeypatch):
    from tradingagents.platform.api import runtime

    values = {"TRADINGAGENTS_DATABASE_URL": built_settings.database_url,
              "TRADINGAGENTS_ARTIFACT_ROOT": str(built_settings.artifact_root),
              "TRADINGAGENTS_ALLOWED_ORIGIN": ORIGIN, "TRADINGAGENTS_SECURE_COOKIES": "false",
              "TRADINGAGENTS_WEB_ROOT": str(built_settings.web_root), "TRADINGAGENTS_API_PORT": "8001"}
    assert load_api_settings(values).web_root == Path(values["TRADINGAGENTS_WEB_ROOT"])
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    with pytest.raises(RuntimeError, match="origin port must equal"):
        runtime.main([])
    monkeypatch.setenv("TRADINGAGENTS_API_PORT", "8000")
    calls = []
    monkeypatch.setattr(runtime.uvicorn, "run", lambda app, **kwargs: calls.append(kwargs))
    runtime.main([])
    assert calls[0]["host"] == "127.0.0.1"
    assert calls[0]["port"] == 8000
    assert calls[0]["access_log"] is False
