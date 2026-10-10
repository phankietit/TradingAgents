"""Durable preclaim refusal, migration and owner control; no SDK/model calls."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect, select

from tests.test_continuation_consent import history, prepared as prepared
from tests.test_linked_execution import setup
from tests.test_linked_publication import entered
from tradingagents.platform.analysis.linked_execution import LinkedExecutionError
from tradingagents.platform.analysis.preparation_refusals import next_reserved_execution
from tradingagents.platform.api import ApiSettings, create_app
from tradingagents.platform.artifacts import LocalArtifactStore
from tradingagents.platform.jobs import linked_worker
from tradingagents.platform.persistence import Database, downgrade_database, upgrade_database
from tradingagents.platform.persistence.models import (
    ResearchExecutionEntryRow,
    ResearchExecutionEventRow,
    ResearchPreparationRefusalRow,
)


@pytest.mark.parametrize("prepared", [False, "postgres_failed"], indirect=True)
def test_poison_reservation_is_durable_without_claim_or_original_mutation(prepared, tmp_path, monkeypatch):
    database, executions, params, clock = setup(prepared)
    reservation = executions.allocate(**params)
    before = history(database)
    calls = []

    def refused(**kwargs):
        calls.append(kwargs["execution_id"])
        raise ValueError("synthetic private diagnostic")

    monkeypatch.setattr(linked_worker, "execute_reserved_continuation", refused)
    values = {"database": database, "artifact_store": LocalArtifactStore(tmp_path / "artifacts"),
              "base_config": {}, "worker_id": "control-worker", "clock": lambda: clock[0]}
    assert linked_worker.poll_reserved_continuation(**values) == reservation.execution_id
    assert calls == [reservation.execution_id]
    assert next_reserved_execution(database) is None
    reopened = Database(database.engine.url.render_as_string(hide_password=False))
    try:
        assert next_reserved_execution(reopened) is None
        assert linked_worker.poll_reserved_continuation(**{**values, "database": reopened}) is None
    finally:
        reopened.dispose()
    assert calls == [reservation.execution_id]
    with pytest.raises(LinkedExecutionError):
        executions.claim(execution_id=reservation.execution_id, worker_id="another-worker")
    assert history(database) == before
    with database.session() as session:
        assert len(session.scalars(select(ResearchPreparationRefusalRow)).all()) == 1


@pytest.mark.parametrize("prepared", [False, "postgres_failed"], indirect=True)
def test_owner_state_and_idempotent_cancel_need_no_sdk(prepared, tmp_path, monkeypatch):
    database, executions, params, clock = setup(prepared)
    reservation = executions.allocate(**params)
    before = history(database)
    app = create_app(ApiSettings(database_url=database.engine.url.render_as_string(hide_password=False),
        artifact_root=tmp_path / "artifacts", allowed_origin="http://testserver", secure_cookies=False,
        clock=lambda: clock[0]))
    with TestClient(app) as client:
        path = f"/api/v1/runs/{reservation.source_run_id}/continuations/{reservation.execution_id}"
        assert client.get(path).status_code == 401
        client.cookies.set("ta_session", params["session_token"])
        client.cookies.set("ta_csrf", params["csrf_token"])
        response = client.get(path)
        assert response.status_code == 200, response.text
        assert response.json()["status"] == "reserved"
        assert response.json()["preparation_requires_review"] is False
        assert response.json()["report_artifact_id"] is None
        discovery = f"/api/v1/runs/{reservation.source_run_id}/continuations"
        found = client.get(discovery)
        assert found.status_code == 200
        assert found.json()["has_more"] is False
        assert [item["execution_id"] for item in found.json()["items"]] == [str(reservation.execution_id)]
        assert found.json()["items"][0]["attempt"] == reservation.attempt
        assert client.get(discovery + f"?before_attempt={reservation.attempt}").json()["items"] == []
        assert client.get(discovery + "?limit=51").status_code == 422
        assert client.get(discovery.replace(str(reservation.source_run_id), str(uuid4()))).status_code == 404
        assert client.get(path.replace(str(reservation.execution_id), str(uuid4()))).status_code == 404
        assert client.post(path + "/cancel", headers={"Origin": "http://testserver"}).status_code == 403
        headers = {"Origin": "http://testserver", "X-CSRF-Token": params["csrf_token"]}
        for _ in range(2):
            assert client.post(path + "/cancel", headers=headers).json()["status"] == "cancelled"
    assert history(database) == before
    assert next_reserved_execution(database) is None
    with pytest.raises(LinkedExecutionError):
        executions.claim(execution_id=reservation.execution_id, worker_id="cancelled-worker")


def test_empty_additive_migration_preserves_original_history(prepared):
    database = prepared[0]
    before = history(database)
    url = database.engine.url.render_as_string(hide_password=False)
    downgrade_database(url, "0017_linked_stops")
    assert "research_preparation_refusals" not in inspect(database.engine).get_table_names()
    assert history(database) == before
    upgrade_database(url)
    assert "research_preparation_refusals" in inspect(database.engine).get_table_names()
    assert history(database) == before


def test_linked_progress_is_owner_scoped_bounded_and_does_not_replay_original_events(prepared, tmp_path, monkeypatch):
    from tradingagents.platform.api import continuation_routes

    def forbidden(*args, **kwargs):
        pytest.fail("Read-only progress must not prepare an SDK or model")

    monkeypatch.setattr(continuation_routes, "prepare_terminal_continuation", forbidden)
    database, _, params, clock, context, _ = entered(prepared)
    stage_run = uuid4()
    context.observer.on_chain_start({}, {}, run_id=stage_run, name="Market Analyst")
    context.observer.on_chain_end({"market_report": "Unvalidated fixture"}, run_id=stage_run)
    before = history(database)
    app = create_app(ApiSettings(database_url=database.engine.url.render_as_string(hide_password=False),
        artifact_root=tmp_path / "artifacts", allowed_origin="http://testserver", secure_cookies=False,
        clock=lambda: clock[0]))
    with TestClient(app) as client:
        path = f"/api/v1/runs/{context.run_id}/continuations/{context.execution_id}/events"
        assert client.get(path).status_code == 401
        client.cookies.set("ta_session", params["session_token"])
        client.cookies.set("ta_csrf", params["csrf_token"])
        assert client.get(path.replace(str(context.execution_id), str(uuid4()))).status_code == 404
        assert client.get(path + "?after_sequence=-1").status_code == 422
        assert client.get(path + "?limit=101").status_code == 422
        first = client.get(path + "?limit=1")
        assert first.status_code == 200, first.text
        assert first.json()["has_more"] is True
        assert first.json()["approval_eligible"] is False
        after = first.json()["events"][0]["sequence"]
        rest = client.get(path + f"?after_sequence={after}").json()
        events = [*first.json()["events"], *rest["events"]]
        assert rest["has_more"] is False
        assert all(event["attempt"] == 2 and "payload" not in event for event in events)
        assert {event["event_type"] for event in events} >= {"research.execution_started", "stage.started", "stage.completed"}
        assert [event["sequence"] for event in events] == sorted({event["sequence"] for event in events})
        assert history(database) == before
        # Disposable fixture corruption: missing actual parent entry provenance
        # must refuse, not render unbound progress or relay database diagnostics.
        with database.session() as session:
            entry = session.get(ResearchExecutionEntryRow, context.execution_id)
            session.delete(session.get(ResearchExecutionEventRow, entry.event_id))
        response = client.get(path)
        assert response.status_code == 409
        assert response.json() == {"detail": "continuation requires review"}
