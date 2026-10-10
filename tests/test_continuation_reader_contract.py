"""Authenticated recovery reading; synthetic writer fixtures, not native proof."""

from datetime import timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from tests.test_continuation_consent import history, prepared as prepared
from tests.test_linked_execution import setup
from tests.test_linked_results import published as published, stopped
from tests.test_platform_api import _login, api_context as api_context
from tradingagents.platform.analysis.preparation_refusals import record_preparation_refusal
from tradingagents.platform.api import ApiSettings, continuation_routes, create_app
from tradingagents.platform.auth import OwnerAuth
from tradingagents.platform.persistence.models import (
    DecisionRow,
    ResearchExecutionArtifactRow,
    ResearchExecutionCompletionRow,
    ResearchPreparationRefusalRow,
)


def forbid_preparation(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Read-only recovery must not prepare an SDK or model")
    monkeypatch.setattr(continuation_routes, "prepare_terminal_continuation", forbidden)


def test_foreign_run_is_hidden_from_all_recovery_reads_before_sdk_work(api_context, monkeypatch):
    forbid_preparation(monkeypatch)
    client = api_context["client"]
    _login(client)
    root = f"/api/v1/runs/{api_context['other_run'].run_id}/continuations"
    for path in (root, root + f"/{uuid4()}", root + f"/{uuid4()}/events"):
        response = client.get(path)
        assert response.status_code == 404
        assert response.json() == {"detail": "run not found"}


@pytest.mark.parametrize("prepared", [False,
    pytest.param("postgres_failed", marks=pytest.mark.integration)], indirect=True)
@pytest.mark.parametrize("mutation", ["expired", "revoked", "disabled"])
def test_lost_owner_auth_blocks_every_recovery_reader_without_sdk_or_history_change(prepared, tmp_path, mutation, monkeypatch):
    forbid_preparation(monkeypatch)
    database, executions, params, clock = setup(prepared)
    reservation = executions.allocate(**params)
    if mutation == "expired":
        clock[0] += timedelta(days=1)
    else:
        with database.session() as session:
            auth = OwnerAuth(session)
            if mutation == "revoked":
                auth.revoke_session(params["session_token"], now=clock[0])
            else:
                auth.disable_owner(reservation.owner_id, now=clock[0])
    before = history(database)
    app = create_app(ApiSettings(database_url=database.engine.url.render_as_string(hide_password=False),
        artifact_root=tmp_path / "artifacts", allowed_origin="http://testserver", secure_cookies=False,
        clock=lambda: clock[0]))
    with TestClient(app) as client:
        client.cookies.set("ta_session", params["session_token"])
        client.cookies.set("ta_csrf", params["csrf_token"])
        root = f"/api/v1/runs/{reservation.source_run_id}/continuations"
        for path in (root, root + f"/{reservation.execution_id}", root + f"/{reservation.execution_id}/events"):
            response = client.get(path)
            assert response.status_code == 401
            assert response.json() == {"detail": "authentication required"}
    assert history(database) == before


@pytest.mark.parametrize("prepared", [False,
    pytest.param("postgres_failed", marks=pytest.mark.integration)], indirect=True)
def test_valid_refusal_is_visible_but_corrupt_refusal_never_becomes_readable_state(prepared, tmp_path, monkeypatch):
    forbid_preparation(monkeypatch)
    database, executions, params, clock = setup(prepared)
    reservation = executions.allocate(**params)
    assert record_preparation_refusal(database=database, execution_id=reservation.execution_id,
        worker_id="reader-fixture", clock=lambda: clock[0])
    app = create_app(ApiSettings(database_url=database.engine.url.render_as_string(hide_password=False),
        artifact_root=tmp_path / "artifacts", allowed_origin="http://testserver", secure_cookies=False,
        clock=lambda: clock[0]))
    with TestClient(app) as client:
        root = f"/api/v1/runs/{reservation.source_run_id}/continuations"
        before = history(database)
        assert client.get(root).status_code == 401
        client.cookies.set("ta_session", params["session_token"])
        client.cookies.set("ta_csrf", params["csrf_token"])
        for path in (root, root + f"/{reservation.execution_id}"):
            response = client.get(path)
            assert response.status_code == 200
            value = response.json()["items"][0] if path == root else response.json()
            assert value["status"] == "reserved" and value["preparation_requires_review"] is True
            assert value["report_artifact_id"] is value["decision_id"] is None
        assert history(database) == before
        # Corruption is restricted to this disposable synthetic fixture.
        with database.session() as session:
            session.get(ResearchPreparationRefusalRow, reservation.execution_id).payload_hash = "c" * 64
        for path in (root, root + f"/{reservation.execution_id}"):
            response = client.get(path)
            assert response.status_code == 409
            assert response.json() == {"detail": "continuation requires review"}
        assert history(database) == before


@pytest.mark.parametrize("prepared", [False,
    pytest.param("postgres_failed", marks=pytest.mark.integration)], indirect=True)
@pytest.mark.parametrize("mutation", ["report_hash", "decision_payload", "report_actor"])
def test_discovery_and_state_require_complete_integrity_before_exposing_report_ids(published, mutation, monkeypatch):
    forbid_preparation(monkeypatch)
    database, _, params, clock, publisher, context, loaded, supervised, result = published
    stopped(published)  # Existing fabricated unit writer stop, not native worker evidence.
    report_ids = publisher.publish_completed(supervised, result, loaded.request)
    app = create_app(ApiSettings(database_url=database.engine.url.render_as_string(hide_password=False),
        artifact_root=publisher.artifact_store.root, allowed_origin="http://testserver", secure_cookies=False,
        clock=lambda: clock[0]))
    with TestClient(app) as client:
        client.cookies.set("ta_session", params["session_token"])
        client.cookies.set("ta_csrf", params["csrf_token"])
        root = f"/api/v1/runs/{context.run_id}/continuations"
        before = history(database)
        for path in (root, root + f"/{context.execution_id}"):
            response = client.get(path)
            assert response.status_code == 200, response.text
            value = response.json()["items"][0] if path == root else response.json()
            assert value["status"] == "completed" and value["report_artifact_id"] == str(report_ids[0])
            assert value["decision_id"] is not None and value["attempt"] == 2
        with database.session() as session:
            receipt = session.get(ResearchExecutionCompletionRow, context.execution_id)
            if mutation == "report_hash":
                receipt.report_hash = "sha256:" + "c" * 64
            elif mutation == "decision_payload":
                row = session.get(DecisionRow, receipt.decision_id)
                row.payload = {**row.payload, "thesis": "SYNTHETIC CORRUPTION"}
            else:
                session.delete(session.get(ResearchExecutionArtifactRow, receipt.report_artifact_id))
        for path in (root, root + f"/{context.execution_id}"):
            response = client.get(path)
            assert response.status_code == 409
            assert response.json() == {"detail": "continuation requires review"}
        assert history(database) == before
