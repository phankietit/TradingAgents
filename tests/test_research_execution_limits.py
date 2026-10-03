"""Immutable opt-in allowance; source binding and legacy omission remain intact."""

from uuid import uuid4

import pytest

from tests.test_platform_api import NOW, _csrf_headers, _login, api_context as api_context
from tradingagents.contracts.runs import ResearchExecutionLimits
from tradingagents.platform.persistence import ImmutableRecordConflict, PlatformRepository


@pytest.mark.parametrize("value", [
    {"wall_seconds": True}, {"wall_seconds": "3600"}, {"wall_seconds": 59},
    {"wall_seconds": 7201}, {"model_calls": False}, {"model_calls": 0},
    {"model_calls": 129}, {"timeout": 600},
])
def test_allowance_rejects_coercion_unbounded_values_and_unowned_sdk_options(value):
    with pytest.raises(ValueError):
        ResearchExecutionLimits.model_validate(value)


def test_api_freezes_explicit_allowance_in_manifest_job_hash_and_idempotency(api_context):
    client = api_context["client"]
    _login(client)
    payload = {"instrument_id": str(api_context["instrument"].instrument_id),
        "analysis_as_of": NOW.isoformat(), "selected_analysts": ["market"],
        "decision_inputs": {"snapshots_by_analyst": {"market": [str(api_context["time_series_snapshot"].snapshot_id)]},
            "source_max_age_seconds": {"market": 172800}},
        "execution_limits": {"wall_seconds": 3600, "model_calls": 128}}
    headers = _csrf_headers(client, **{"Idempotency-Key": str(uuid4())})
    first = client.post("/api/v1/runs", json=payload, headers=headers)
    assert first.status_code == 202, first.text
    stored = first.json()
    assert stored["run"]["execution_limits"] == payload["execution_limits"]
    assert stored["job"]["payload"]["execution_limits"] == payload["execution_limits"]
    replay = client.post("/api/v1/runs", json=payload, headers=headers)
    assert replay.status_code == 202 and replay.json()["run"]["run_id"] == stored["run"]["run_id"]
    payload["execution_limits"] = {"wall_seconds": 1800, "model_calls": 128}
    assert client.post("/api/v1/runs", json=payload, headers=headers).status_code == 409
    changed = client.post("/api/v1/runs", json=payload,
        headers=_csrf_headers(client, **{"Idempotency-Key": str(uuid4())}))
    assert changed.status_code == 202
    assert changed.json()["run"]["config_hash"] != stored["run"]["config_hash"]
    from uuid import UUID

    with client.app.state.database.session() as session:
        repo = PlatformRepository(session)
        run = repo.get_run(UUID(stored["run"]["run_id"]), api_context["principal"].owner_id)
        with pytest.raises(ImmutableRecordConflict):
            repo.save_run(run.model_copy(update={"execution_limits": ResearchExecutionLimits()}))


def test_explicit_allowance_requires_snapshot_run_and_does_not_rewrite_legacy(api_context):
    client = api_context["client"]
    _login(client)
    payload = {"instrument_id": str(api_context["instrument"].instrument_id),
        "analysis_as_of": NOW.isoformat(), "selected_analysts": ["market"],
        "execution_limits": {"wall_seconds": 3600, "model_calls": 128}}
    headers = _csrf_headers(client, **{"Idempotency-Key": str(uuid4())})
    assert client.post("/api/v1/runs", json=payload, headers=headers).status_code == 422
    del payload["execution_limits"]
    legacy = client.post("/api/v1/runs", json=payload, headers=headers)
    assert legacy.status_code == 202
    assert legacy.json()["run"]["execution_limits"] is None
    assert "execution_limits" not in legacy.json()["job"]["payload"]
