"""Reloadable, owner-scoped processing state without payload or lease disclosure."""

from tests.test_platform_api import (
    NOW,
    _csrf_headers,
    _login,
    _run_payload,
    api_context as api_context,
)
from tradingagents.platform.jobs import DurableJobQueue


def test_cancel_retry_wait_updates_active_run_and_reload_projection(api_context):
    from datetime import timedelta
    from uuid import UUID

    from tradingagents.contracts import RunStatus
    from tradingagents.platform.persistence import PlatformRepository

    client = api_context['client']
    _login(client)
    accepted = client.post('/api/v1/runs',
        headers=_csrf_headers(client, **{'Idempotency-Key': 'retry-cancel'}),
        json=_run_payload(api_context['instrument'].instrument_id))
    assert accepted.status_code == 202
    run_id = accepted.json()['run']['run_id']
    owner_id = UUID(accepted.json()['run']['owner_id'])
    with client.app.state.database.session() as session:
        queue = DurableJobQueue(session)
        job = queue.claim('test-retry-worker', lease_for=timedelta(minutes=1), now=NOW)
        assert str(job.run_id) == run_id
        repo = PlatformRepository(session)
        run = repo.get_run(UUID(run_id), owner_id)
        repo.save_run(run.model_copy(update={'status': RunStatus.RUNNING, 'started_at': NOW}))
        queue.fail(job.job_id, 'test-retry-worker', error_code='TEST_TRANSPORT',
                   retry_after=timedelta(minutes=1), now=NOW)
    cancelled = client.post(f'/api/v1/runs/{run_id}/cancel', headers=_csrf_headers(client))
    assert cancelled.json()['status'] == 'cancelled'
    assert client.get(f'/api/v1/runs/{run_id}').json()['status'] == 'cancelled'
    assert client.get(f'/api/v1/runs/{run_id}/job').json()['status'] == 'cancelled'


def test_run_job_discovery_is_owner_scoped_and_minimal(api_context):
    client = api_context["client"]
    other = api_context["other_run"]
    other_path = f"/api/v1/runs/{other.run_id}/job"
    with client.app.state.database.session() as session:
        DurableJobQueue(session).enqueue(owner_id=other.owner_id, run_id=other.run_id,
            idempotency_key="other-owner-job", payload={"private": "do-not-disclose"}, now=NOW)
    assert client.get(other_path).status_code == 401
    _login(client)
    assert client.get(other_path).status_code == 404
    accepted = client.post('/api/v1/runs',
        headers=_csrf_headers(client, **{'Idempotency-Key': 'reloadable-job'}),
        json=_run_payload(api_context['instrument'].instrument_id))
    assert accepted.status_code == 202
    run_id = accepted.json()['run']['run_id']
    response = client.get(f'/api/v1/runs/{run_id}/job')
    assert response.status_code == 200
    assert response.json() == {key: value for key, value in accepted.json()['job'].items()
        if key in {'job_id', 'run_id', 'status', 'attempt', 'max_attempts', 'available_at', 'updated_at', 'completed_at'}}
    assert response.json()['attempt'] == 0
    assert 'no-store' in response.headers['cache-control']
    assert not {'owner_id', 'payload', 'lease_owner', 'error_message', 'idempotency_key'} & response.json().keys()
