from datetime import timedelta
from uuid import uuid4

import pytest

from tests.test_platform_api import NOW, _login, api_context as api_context
from tests.test_stock_screener import _input, _policy
from tradingagents.contracts import ArtifactKind
from tradingagents.platform.artifacts import ArtifactService
from tradingagents.platform.persistence import PlatformRepository
from tradingagents.platform.screening import DeterministicStockScreener


def seed(context, *, other_owner=False, future=False):
    client = context["client"]
    with client.app.state.database.session() as session:
        service = DeterministicStockScreener(ArtifactService(client.app.state.artifact_store, PlatformRepository(session)))
        snapshot = service.screen(inputs=(_input("AAPL", instrument=context["instrument"]),),
            policy=_policy(), as_of=NOW,
            generated_at=NOW + timedelta(days=1) if future else NOW)
        owner_id = uuid4() if other_owner else context["principal"].owner_id
        # Different policy makes a distinct immutable snapshot for another owner.
        if other_owner:
            snapshot = service.screen(inputs=(_input("AAPL", instrument=context["instrument"]),),
                policy=_policy(policy_id="other-owner-policy"), as_of=NOW, generated_at=NOW)
        service.persist(owner_id=owner_id, snapshot=snapshot)
        return snapshot


def test_screening_discovery_is_owner_scoped_bounded_and_omits_private_paths(api_context):
    client = api_context["client"]
    own = seed(api_context)
    other = seed(api_context, other_owner=True)
    future = seed(api_context, future=True)
    assert client.get("/api/v1/screenings").status_code == 401
    assert client.get(f"/api/v1/screenings/{own.screening_snapshot_id}").status_code == 401
    _login(client)
    response = client.get("/api/v1/screenings")
    assert [row["artifact_id"] for row in response.json()] == [str(own.screening_snapshot_id)]
    assert "storage_key" not in response.text and "owner_id" not in response.text
    assert response.headers["cache-control"] == "no-store"
    assert client.get("/api/v1/screenings", params={"offset": 1}).json() == []
    for params in ({"limit": 0}, {"limit": 201}, {"offset": -1}):
        assert client.get("/api/v1/screenings", params=params).status_code == 422
    assert client.get(f"/api/v1/screenings/{own.screening_snapshot_id}").json() == own.model_dump(mode="json")
    assert client.get(f"/api/v1/screenings/{other.screening_snapshot_id}").status_code == 404
    assert client.get(f"/api/v1/screenings/{future.screening_snapshot_id}").status_code == 409
    assert client.get(f"/api/v1/screenings/{uuid4()}").status_code == 404
    assert client.get(f"/api/v1/screenings/{api_context['artifact'].artifact_id}").status_code == 409


@pytest.mark.parametrize("failure", ["corrupt", "invalid_schema"])
def test_screening_rejects_invalid_content_without_exposing_payload(api_context, failure):
    client = api_context["client"]
    snapshot = seed(api_context)
    artifact_id = snapshot.screening_snapshot_id
    with client.app.state.database.session() as session:
        repo = PlatformRepository(session)
        if failure == "corrupt":
            manifest = repo.get_artifact(artifact_id, api_context["principal"].owner_id)
            (client.app.state.artifact_store.root / manifest.storage_key).write_bytes(b"private-invalid-payload")
        else:
            manifest = ArtifactService(client.app.state.artifact_store, repo).create(
                owner_id=api_context["principal"].owner_id, kind=ArtifactKind.SCREENING_SNAPSHOT,
                media_type="application/json", content=b'{"private-invalid-payload": true}', created_at=NOW)
            artifact_id = manifest.artifact_id
    _login(client)
    response = client.get(f"/api/v1/screenings/{artifact_id}")
    assert response.status_code == 409
    assert response.json() == {"detail": "screening validation failed"}
    assert "private-invalid-payload" not in response.text
