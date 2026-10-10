"""Fast API refusal/redaction evidence; native acceptance is tested separately."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from tests.test_platform_api import ORIGIN, _login, api_context  # noqa: F401
from tradingagents.platform.api import continuation_routes
from tradingagents.platform.api.schemas import ContinuationConsentRequest
from tradingagents.platform.persistence import PlatformRepository


@pytest.mark.parametrize("value", [False, 1, "true", None])
@pytest.mark.parametrize("field", ["confirm_continue", "acknowledge_original_allowance",
    "acknowledge_unknown_provider_cost", "acknowledge_unvalidated_prior_research"])
def test_confirmation_requires_literal_true(field, value):
    body = {"observation_hash": "a" * 64,
            "idempotency_key": "65e6de5e-c7d2-4ed6-ac6e-67d66c8e91a6",
            "confirm_continue": True, "acknowledge_original_allowance": True,
            "acknowledge_unknown_provider_cost": True,
            "acknowledge_unvalidated_prior_research": True}
    with pytest.raises(ValidationError):
        ContinuationConsentRequest.model_validate({**body, field: value})


def test_foreign_run_refuses_before_probe_and_probe_errors_are_redacted(api_context, monkeypatch):  # noqa: F811
    client = api_context["client"]
    _login(client)
    headers = {"Origin": ORIGIN, "X-CSRF-Token": client.cookies["ta_csrf"]}
    calls = []

    def refused(**kwargs):
        calls.append(kwargs["run_id"])
        raise ValueError("private-provider-value-not-for-response")

    monkeypatch.setattr(continuation_routes, "prepare_terminal_continuation", refused)
    run = api_context["other_run"]
    path = f"/api/v1/runs/{run.run_id}/continuation/prepare"
    assert client.post(path, headers=headers).status_code == 404
    assert calls == []
    # Synthetic owner record only; never an existing private application DB.
    run = run.model_copy(update={"run_id": uuid4(), "owner_id": api_context["principal"].owner_id})
    with client.app.state.database.session() as session:
        PlatformRepository(session).save_run(run)
    path = f"/api/v1/runs/{run.run_id}/continuation/prepare"
    response = client.post(path, headers=headers)
    assert response.status_code == 409
    assert response.json() == {"detail": "continuation requires review"}
    assert calls == [run.run_id]
