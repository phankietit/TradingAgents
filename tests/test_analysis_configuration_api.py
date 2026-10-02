"""Configuration disclosure is authenticated and never implies runtime health."""

from tests.test_platform_api import _login, api_context as api_context


def test_configuration_is_private_and_not_a_provider_probe(api_context, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-secret-must-not-leak")
    client = api_context["client"]
    path = "/api/v1/analysis-configuration"
    assert client.get(path).status_code == 401
    _login(client)
    response = client.get(path)
    assert response.status_code == 200
    assert response.json() == {
        "provider": "openai", "quick_model": "quick", "deep_model": "deep",
        "worker_status": "UNVERIFIED", "provider_connection": "UNVERIFIED",
        "max_job_attempts": 3,
        "execution_limits": {"wall_seconds": 1800, "model_calls": 128},
        "deadline_mode": "cooperative_boundaries",
        "default_worker_supervision": "spawned_process",
    }
    assert "no-store" in response.headers["cache-control"]
    assert "synthetic-secret" not in response.text
