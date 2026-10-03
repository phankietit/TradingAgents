"""Authenticated linked approval mechanics, not live finance or browser proof."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from tests.test_continuation_consent import PASSWORD, history
from tests.test_decision_api import body
from tests.test_decision_lifecycle import _approval
from tests.test_linked_results import ready_linked as ready_linked
from tradingagents.platform.analysis.linked_execution import LinkedExecutionError
from tradingagents.platform.analysis.linked_results import read_linked_completion
from tradingagents.platform.api import ApiSettings, create_app
from tradingagents.platform.persistence import PlatformRepository
from tradingagents.platform.persistence.models import DecisionLifecycleEventRow, DecisionRow


@pytest.mark.parametrize("ready_linked", [False,
    pytest.param("postgres", marks=pytest.mark.integration)], indirect=True)
@pytest.mark.parametrize("same_event", [True, False])
def test_linked_concurrent_owner_transitions_have_one_committed_history(ready_linked, same_event):
    values, _, candidate = ready_linked
    database, _, _, _, publisher, context, _, _, _ = values
    event = _approval(candidate)
    other = event if same_event else event.model_copy(update={"event_id": uuid4()})
    barrier = Barrier(2)
    before = history(database)

    def write(action):
        barrier.wait(timeout=10)
        try:
            with database.session() as session:
                PlatformRepository(session, artifact_store=publisher.artifact_store).add_decision_event(action)
            return "committed"
        except (ValueError, SQLAlchemyError):
            return "refused"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(write, (event, other)))
    # SQLite may refuse its simultaneous writer; actual PostgreSQL row lock
    # must return the same committed acknowledgement to both same-event callers.
    assert results.count("committed") >= 1
    if not same_event:
        assert results.count("committed") == 1
    elif database.engine.dialect.name == "postgresql":
        assert results == ["committed", "committed"]
    with database.session() as session:
        assert len(PlatformRepository(session).list_decision_events(candidate.decision_id, candidate.owner_id)) == 1
        assert read_linked_completion(session=session, artifact_store=publisher.artifact_store,
            owner_id=context.owner_id, execution_id=context.execution_id) is not None
    assert history(database) == before


def test_linked_api_owner_csrf_policy_and_idempotent_projection(ready_linked):
    values, _, candidate = ready_linked
    database, _, _, _, publisher, context, _, _, _ = values
    before = history(database)
    settings = ApiSettings(database_url=database.engine.url.render_as_string(hide_password=False),
        artifact_root=publisher.artifact_store.root, allowed_origin="http://testserver",
        secure_cookies=False, clock=lambda: context._lease.started_at + timedelta(minutes=1))
    path = f"/api/v1/decisions/{candidate.decision_id}"
    request = body(candidate)
    with TestClient(create_app(settings)) as client:
        assert client.get(path + "/state").status_code == 401
        login = client.post("/api/v1/auth/login", json={
            "email": "consent-fixture@example.test", "password": PASSWORD}, headers={"Origin": "http://testserver"})
        assert login.status_code == 200
        headers = {"Origin": "http://testserver", "X-CSRF-Token": client.cookies["ta_csrf"]}
        assert client.post(path + "/transitions", json=request, headers={"Origin": "http://testserver"}).status_code == 403
        assert client.post(path + "/transitions", json={**request, "actor_id": str(uuid4())}, headers=headers).status_code == 422
        assert client.get(f"/api/v1/decisions/{uuid4()}/state").status_code == 404
        assert client.post(path + "/transitions", json={**request, "policy_version": "wrong"}, headers=headers).status_code == 409
        for _ in range(2):
            response = client.post(path + "/transitions", json=request, headers=headers)
            assert response.status_code == 200
            assert response.json()["current_status"] == "approved"
            assert response.json()["candidate"]["status"] == "ready_for_approval"
            assert len(response.json()["events"]) == 1
        assert client.post(path + "/transitions", json={**request, "reason": "Changed"}, headers=headers).status_code == 409
        assert client.get(path + "/state").json()["current_status"] == "approved"
    assert history(database) == before


@pytest.mark.parametrize("mutation", ["status", "event_column", "event_payload", "event_time"])
def test_linked_reader_rejects_forged_postapproval_lifecycle(ready_linked, mutation):
    values, _, candidate = ready_linked
    database, _, _, _, publisher, context, _, _, _ = values
    event = _approval(candidate)
    with database.session() as session:
        PlatformRepository(session, artifact_store=publisher.artifact_store).add_decision_event(event)
    with database.session() as session:
        row = session.get(DecisionRow, candidate.decision_id)
        indexed = session.get(DecisionLifecycleEventRow, event.event_id)
        if mutation == "status":
            row.status = "ready_for_approval"
        elif mutation == "event_column":
            indexed.to_status = "rejected"
        elif mutation == "event_payload":
            indexed.payload = {**indexed.payload, "actor_type": "system", "actor_id": None}
        else:
            indexed.occurred_at = context._lease.started_at - timedelta(seconds=1)
    with database.session() as session, pytest.raises(LinkedExecutionError):
        read_linked_completion(session=session, artifact_store=publisher.artifact_store,
            owner_id=context.owner_id, execution_id=context.execution_id)


def test_linked_reader_and_approval_sanitize_blob_integrity_failure(ready_linked, monkeypatch):
    from tradingagents.platform.artifacts import ArtifactIntegrityError

    values, _, candidate = ready_linked
    database, _, _, _, publisher, context, _, _, _ = values

    def broken_blob(*args, **kwargs):
        raise ArtifactIntegrityError("synthetic private blob diagnostic MUST_NOT_LEAK")

    monkeypatch.setattr(publisher.artifact_store, "get_bytes", broken_blob)
    with database.session() as session, pytest.raises(LinkedExecutionError) as rejected:
        read_linked_completion(session=session, artifact_store=publisher.artifact_store,
            owner_id=context.owner_id, execution_id=context.execution_id)
    assert "MUST_NOT_LEAK" not in str(rejected.value)
    with database.session() as session, pytest.raises(ValueError):
        PlatformRepository(session, artifact_store=publisher.artifact_store).add_decision_event(_approval(candidate))
    with database.session() as session:
        assert PlatformRepository(session).list_decision_events(candidate.decision_id, candidate.owner_id) == ()


@pytest.mark.parametrize("path", ["review_ready_approve", "reject"])
def test_linked_human_review_and_rejection_preserve_immutable_candidate(ready_linked, path):
    from tradingagents.contracts import DecisionStatus
    from tradingagents.platform.decisions import DecisionLifecycle

    values, _, candidate = ready_linked
    database, _, _, _, publisher, context, _, _, _ = values
    before = history(database)
    start = _approval(candidate)
    targets = [DecisionStatus.REVIEW, DecisionStatus.READY_FOR_APPROVAL, DecisionStatus.APPROVED] if path == "review_ready_approve" else [DecisionStatus.REJECTED]
    previous = candidate.status
    for index, target in enumerate(targets):
        action = start.model_copy(update={"event_id": uuid4(), "from_status": previous,
            "to_status": target, "occurred_at": start.occurred_at + timedelta(minutes=index)})
        with database.session() as session:
            repository = PlatformRepository(session, artifact_store=publisher.artifact_store)
            repository.add_decision_event(action)
            assert read_linked_completion(session=session, artifact_store=publisher.artifact_store,
                owner_id=context.owner_id, execution_id=context.execution_id) is not None
            events = repository.list_decision_events(candidate.decision_id, candidate.owner_id)
            assert DecisionLifecycle().apply(candidate, events) is target
            assert repository.get_decision(candidate.decision_id, candidate.owner_id) == candidate
        previous = target
    with database.session() as session, pytest.raises(ValueError):
        PlatformRepository(session, artifact_store=publisher.artifact_store).add_decision_event(
            start.model_copy(update={"event_id": uuid4(), "occurred_at": start.occurred_at + timedelta(days=1)}))
    assert history(database) == before
