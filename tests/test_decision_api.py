"""Authenticated human review uses the same persisted lifecycle gates."""

from datetime import timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from tests.test_decision_event_persistence import seed
from tests.test_decision_lifecycle import NOW
from tradingagents.platform.api import ApiSettings, create_app
from tradingagents.platform.auth import OwnerAuth


@pytest.fixture
def context(tmp_path):
    database, decision = seed(tmp_path)
    password = "test-only long owner password"
    with database.session() as session:
        OwnerAuth(session).bootstrap_owner("owner@example.com", password,
                                          owner_id=decision.owner_id, now=NOW)
    settings = ApiSettings(
        database_url=f"sqlite:///{tmp_path / 'decisions.db'}",
        artifact_root=tmp_path / "artifacts", allowed_origin="http://testserver",
        secure_cookies=False, clock=lambda: NOW + timedelta(minutes=1),
    )
    with TestClient(create_app(settings)) as client:
        yield client, decision, password
    database.dispose()


def login(client, password):
    response = client.post("/api/v1/auth/login", json={"email": "owner@example.com", "password": password},
                           headers={"Origin": "http://testserver"})
    assert response.status_code == 200
    return {"Origin": "http://testserver", "X-CSRF-Token": client.cookies["ta_csrf"]}


def body(decision):
    return {"event_id": str(uuid4()), "expected_status": "ready_for_approval",
            "action": "approve", "reason": "Reviewed evidence and risk results",
            "policy_id": str(decision.policy_checks[0].policy_id),
            "policy_version": decision.policy_checks[0].policy_version}


def test_api_requires_session_csrf_and_matching_owner(context):
    client, decision, password = context
    path = f"/api/v1/decisions/{decision.decision_id}"
    assert client.get(path + "/state").status_code == 401
    headers = login(client, password)
    assert client.post(path + "/transitions", json=body(decision), headers={"Origin": "http://testserver"}).status_code == 403
    assert client.get(f"/api/v1/decisions/{uuid4()}/state").status_code == 404
    spoofed = {**body(decision), "actor_id": str(uuid4())}
    assert client.post(path + "/transitions", json=spoofed, headers=headers).status_code == 422


def test_api_approval_projects_current_status_and_retries_idempotently(context):
    client, decision, password = context
    headers = login(client, password)
    path = f"/api/v1/decisions/{decision.decision_id}"
    request = body(decision)
    result = client.post(path + "/transitions", json=request, headers=headers)
    assert result.status_code == 200, result.text
    assert result.json()["current_status"] == "approved"
    assert result.json()["candidate"]["status"] == "ready_for_approval"
    retry = client.post(path + "/transitions", json=request, headers=headers)
    assert retry.status_code == 200
    assert len(retry.json()["events"]) == 1
    state = client.get(path + "/state").json()
    assert state["current_status"] == "approved"
    conflict = client.post(path + "/transitions", json={**request, "reason": "Changed reason"}, headers=headers)
    assert conflict.status_code == 409


def test_api_rejects_unmatched_policy_without_recording_approval(context):
    client, decision, password = context
    headers = login(client, password)
    path = f"/api/v1/decisions/{decision.decision_id}"
    response = client.post(path + "/transitions", json={**body(decision), "policy_version": "unreviewed"}, headers=headers)
    assert response.status_code == 409
    state = client.get(path + "/state").json()
    assert state["current_status"] == "ready_for_approval"
    assert state["events"] == []
