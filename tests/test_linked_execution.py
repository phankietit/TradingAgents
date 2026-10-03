"""Separate authenticated allocation/lease mechanics, never model dispatch."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import replace
from datetime import timedelta
from threading import Barrier
from time import monotonic
from uuid import uuid4

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import SQLAlchemyError

from tests.test_continuation_consent import history, prepared as prepared
from tradingagents.contracts import RunEventType
from tradingagents.platform.analysis.accounting import load_accounting_evidence
from tradingagents.platform.analysis.continuation import ContinuationConsentStore
from tradingagents.platform.analysis.linked_execution import (
    LinkedExecutionError,
    LinkedExecutionStore,
)
from tradingagents.platform.auth import OwnerAuth
from tradingagents.platform.events import RunEventStore
from tradingagents.platform.persistence import Database, downgrade_database, upgrade_database
from tradingagents.platform.persistence.models import ResearchExecutionRow


def setup(prepared):
    database, consents, values, clock = prepared
    consent = consents.record(**values)
    store = LinkedExecutionStore(consents)
    params = {"execution_id": consent.execution_id, "session_token": values["session_token"],
              "csrf_token": values["csrf_token"]}
    return database, store, params, clock


@pytest.mark.parametrize("prepared", [False,
    pytest.param("postgres_failed", marks=pytest.mark.integration)], indirect=True)
def test_separate_lease_preserves_history_and_original_deadline(prepared):
    database, store, params, clock = setup(prepared)
    before = history(database)
    first = store.allocate(**params)
    assert store.allocate(**params) == first and first.status == "reserved" and first.attempt == 2
    lease = store.claim(execution_id=first.execution_id, worker_id="fixture-worker-2")
    assert lease.reservation.source_job_id == first.source_job_id
    assert lease.deadline_at == clock[0] + timedelta(seconds=1790)
    clock[0] += timedelta(seconds=20)
    renewed = store.heartbeat(lease)
    assert renewed.token == lease.token and renewed.deadline_at == lease.deadline_at
    assert renewed.started_at == lease.started_at and renewed.expires_at == clock[0] + timedelta(seconds=300)
    assert str(lease.token) not in repr(lease) and str(first.owner_id) not in repr(lease) + repr(first)
    reopened = Database(database.engine.url.render_as_string(hide_password=False))
    try:
        other = LinkedExecutionStore(ContinuationConsentStore(reopened, codec=store.consents.codec, clock=store.consents.clock))
        assert other.heartbeat(renewed) == renewed
    finally:
        reopened.dispose()
    with database.session() as session:
        row = session.get(ResearchExecutionRow, first.execution_id)
        assert row.lease_token_hash != str(lease.token) and len(row.lease_token_hash) == 64
        evidence = load_accounting_evidence(session=session, owner_id=first.owner_id, run_id=first.source_run_id)
        assert evidence.attempts == (1,) and evidence.started_calls == 1 and evidence.reported_total_tokens == 15
    assert history(database) == before
    # A lease has not emitted execution_started or granted publication/model entry.


@pytest.mark.parametrize("prepared", [False,
    pytest.param("postgres_failed", marks=pytest.mark.integration)], indirect=True)
@pytest.mark.parametrize("allocation", [True, False])
def test_concurrent_allocation_idempotent_but_claim_has_one_winner(prepared, allocation):
    database, store, params, _ = setup(prepared)
    if not allocation:
        store.allocate(**params)
    before = history(database)
    barrier = Barrier(2)

    def call(index):
        barrier.wait(timeout=5)
        try:
            return store.allocate(**params) if allocation else store.claim(
                execution_id=params["execution_id"], worker_id=f"fixture-{index}")
        except LinkedExecutionError:
            return None

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(call, range(2)))
    assert len([result for result in results if result is not None]) == (2 if allocation else 1)
    with database.session() as session:
        assert len(session.scalars(select(ResearchExecutionRow)).all()) == 1
    assert history(database) == before


@pytest.mark.parametrize("leased", [False, True])
def test_owner_cancel_never_claims_an_active_worker_was_stopped(prepared, leased):
    database, store, params, _ = setup(prepared)
    row = store.allocate(**params)
    if leased:
        lease = store.claim(execution_id=row.execution_id, worker_id="fixture")
    before = history(database)
    stopped = store.request_cancel(**params)
    assert stopped.status == ("cancel_requested" if leased else "cancelled")
    assert store.request_cancel(**params) == stopped
    with pytest.raises(LinkedExecutionError):
        store.claim(execution_id=row.execution_id, worker_id="fixture")
    if leased:
        with pytest.raises(LinkedExecutionError):
            store.heartbeat(lease)
    assert history(database) == before


def test_expiration_retains_uncertainty_and_never_requeues(prepared):
    database, store, params, clock = setup(prepared)
    reserved = store.allocate(**params)
    lease = store.claim(execution_id=reserved.execution_id, worker_id="fixture", lease_seconds=1)
    before = history(database)
    with pytest.raises(LinkedExecutionError):
        store.mark_expired_for_review(execution_id=reserved.execution_id)
    clock[0] += timedelta(seconds=1)
    with pytest.raises(LinkedExecutionError):
        store.heartbeat(lease)
    reviewed = store.mark_expired_for_review(execution_id=reserved.execution_id)
    assert reviewed.status == "review_required"
    assert store.mark_expired_for_review(execution_id=reserved.execution_id) == reviewed
    assert store.allocate(**params).status == "review_required"
    with pytest.raises(LinkedExecutionError):
        store.claim(execution_id=reserved.execution_id, worker_id="new-fixture")
    assert history(database) == before


@pytest.mark.parametrize("allocated", [False, True])
def test_stale_high_water_refuses_allocation_or_claim(prepared, allocated):
    database, store, params, clock = setup(prepared)
    if allocated:
        store.allocate(**params)
    source = prepared[2]["expected_observation"]
    with database.session() as session:
        RunEventStore(session).append(owner_id=source.owner_id, run_id=source.run_id,
            event_type=RunEventType.STAGE_STARTED, occurred_at=clock[0], payload={"stage": "Market Analyst"})
    before = history(database)
    with pytest.raises(LinkedExecutionError, match="^linked execution requires review$"):
        if allocated:
            store.claim(execution_id=params["execution_id"], worker_id="fixture")
        else:
            store.allocate(**params)
    assert history(database) == before


@pytest.mark.parametrize("mutation", ["token", "csrf", "owner", "expired", "revoked", "disabled"])
def test_current_owner_auth_required_to_consume_or_cancel(prepared, mutation):
    database, store, params, clock = setup(prepared)
    store.allocate(**params)
    observed = prepared[2]["expected_observation"]
    if mutation == "token":
        params["session_token"] = "PRIVATE_NEVER_ECHO"
    elif mutation == "csrf":
        params["csrf_token"] = "PRIVATE_NEVER_ECHO"
    elif mutation == "owner":
        params["execution_id"] = uuid4()
    elif mutation == "expired":
        clock[0] += timedelta(days=1)
    else:
        with database.session() as session:
            auth = OwnerAuth(session)
            if mutation == "revoked":
                auth.revoke_session(params["session_token"], now=clock[0])
            else:
                auth.disable_owner(observed.owner_id, now=clock[0])
    before = history(database)
    for operation in (store.allocate, store.request_cancel):
        with pytest.raises(LinkedExecutionError) as raised:
            operation(**params)
        assert str(raised.value) == "linked execution requires review" and raised.value.__cause__ is None
    assert history(database) == before


@pytest.mark.parametrize("mutation", ["token", "worker", "identity", "float_attempt", "bool_attempt", "deadline"])
def test_foreign_or_reset_lease_is_not_renewed(prepared, mutation):
    database, store, params, _ = setup(prepared)
    row = store.allocate(**params)
    lease = store.claim(execution_id=row.execution_id, worker_id="fixture")
    if mutation == "token":
        lease = replace(lease, token=uuid4())
    elif mutation == "worker":
        lease = replace(lease, worker_id="other")
    elif mutation == "deadline":
        lease = replace(lease, deadline_at=lease.deadline_at + timedelta(seconds=1))
    else:
        changes = {"identity": {"owner_id": uuid4()}, "float_attempt": {"attempt": 2.0}, "bool_attempt": {"attempt": True}}
        lease = replace(lease, reservation=replace(lease.reservation, **changes[mutation]))
    before = history(database)
    with pytest.raises(LinkedExecutionError):
        store.heartbeat(lease)
    assert history(database) == before


def test_disabled_owner_cannot_renew_but_expiry_can_be_marked_for_review(prepared):
    database, store, params, clock = setup(prepared)
    row = store.allocate(**params)
    lease = store.claim(execution_id=row.execution_id, worker_id="fixture", lease_seconds=1)
    with database.session() as session:
        OwnerAuth(session).disable_owner(row.owner_id, now=clock[0])
    with pytest.raises(LinkedExecutionError):
        store.heartbeat(lease)
    clock[0] += timedelta(seconds=1)
    assert store.mark_expired_for_review(execution_id=row.execution_id).status == "review_required"


def test_lease_deadline_cannot_be_extended_to_a_fresh_original_allowance(prepared):
    _, store, params, clock = setup(prepared)
    row = store.allocate(**params)
    lease = store.claim(execution_id=row.execution_id, worker_id="fixture")
    for _ in range(6):
        clock[0] += timedelta(seconds=290)
        lease = store.heartbeat(lease)
    assert lease.expires_at == lease.deadline_at
    clock[0] = lease.deadline_at
    with pytest.raises(LinkedExecutionError):
        store.heartbeat(lease)


def test_rollback_produces_no_allocation_ack(prepared, monkeypatch):
    database, store, params, _ = setup(prepared)
    original = database.session

    @contextmanager
    def fail_commit(**options):
        with original(**options) as session:
            yield session
            raise SQLAlchemyError("PRIVATE_NEVER_ECHO")

    before = history(database)
    monkeypatch.setattr(database, "session", fail_commit)
    with pytest.raises(LinkedExecutionError):
        store.allocate(**params)
    monkeypatch.setattr(database, "session", original)
    with database.session() as session:
        assert session.scalar(select(ResearchExecutionRow)) is None
    assert history(database) == before


@pytest.mark.parametrize("committed", [False, True])
def test_failed_or_lost_claim_ack_never_allows_an_automatic_second_claim(prepared, monkeypatch, committed):
    database, store, params, clock = setup(prepared)
    reserved = store.allocate(**params)
    original = database.session

    @contextmanager
    def uncertain_commit(**options):
        with original(**options) as session:
            yield session
            if not committed:
                raise SQLAlchemyError("PRIVATE_NEVER_ECHO")
        if committed:
            raise SQLAlchemyError("PRIVATE_NEVER_ECHO")

    before = history(database)
    monkeypatch.setattr(database, "session", uncertain_commit)
    with pytest.raises(LinkedExecutionError):
        store.claim(execution_id=reserved.execution_id, worker_id="fixture", lease_seconds=1)
    monkeypatch.setattr(database, "session", original)
    with database.session() as session:
        row = session.get(ResearchExecutionRow, reserved.execution_id)
        assert row.status == ("leased" if committed else "reserved")
    if committed:
        with pytest.raises(LinkedExecutionError):
            store.claim(execution_id=reserved.execution_id, worker_id="replacement")
        clock[0] += timedelta(seconds=1)
        assert store.mark_expired_for_review(execution_id=reserved.execution_id).status == "review_required"
    else:
        assert store.claim(execution_id=reserved.execution_id, worker_id="explicit-replacement").reservation.status == "leased"
    assert history(database) == before


@pytest.mark.parametrize("value", [0, 301, True, 1.0, None])
def test_invalid_lease_window_does_not_allocate_a_worker(prepared, value):
    database, store, params, _ = setup(prepared)
    row = store.allocate(**params)
    with pytest.raises(LinkedExecutionError):
        store.claim(execution_id=row.execution_id, worker_id="fixture", lease_seconds=value)
    with database.session() as session:
        assert session.get(ResearchExecutionRow, row.execution_id).status == "reserved"


@pytest.mark.parametrize("field", ["owner_id", "observation_hash", "source_run_id", "deadline_at"])
def test_corrupt_link_or_reset_deadline_refuses_renewal(prepared, field):
    database, store, params, _ = setup(prepared)
    row = store.allocate(**params)
    lease = store.claim(execution_id=row.execution_id, worker_id="fixture")
    with database.session() as session:
        record = session.get(ResearchExecutionRow, row.execution_id)
        value = (lease.deadline_at + timedelta(seconds=1) if field == "deadline_at"
            else "b" * 64 if field == "observation_hash" else uuid4())
        setattr(record, field, value)
    before = history(database)
    with pytest.raises(LinkedExecutionError):
        store.heartbeat(lease)
    assert history(database) == before


def test_matching_corrupt_deadline_in_database_and_handle_still_rejects(prepared):
    database, store, params, _ = setup(prepared)
    row = store.allocate(**params)
    lease = store.claim(execution_id=row.execution_id, worker_id="fixture")
    deadline = lease.deadline_at + timedelta(seconds=1)
    with database.session() as session:
        session.get(ResearchExecutionRow, row.execution_id).deadline_at = deadline
    with pytest.raises(LinkedExecutionError):
        store.heartbeat(replace(lease, deadline_at=deadline))


def test_clock_rollback_cannot_renew_or_restart_attempt(prepared):
    database, store, params, clock = setup(prepared)
    row = store.allocate(**params)
    lease = store.claim(execution_id=row.execution_id, worker_id="fixture")
    clock[0] -= timedelta(seconds=1)
    before = history(database)
    with pytest.raises(LinkedExecutionError):
        store.heartbeat(lease)
    assert history(database) == before


def test_busy_writer_refuses_with_bounded_wait(prepared):
    database, store, params, _ = setup(prepared)
    store.consents.lock_timeout_seconds = .05
    with database.engine.connect() as writer:
        writer.exec_driver_sql("BEGIN IMMEDIATE")
        started = monotonic()
        with pytest.raises(LinkedExecutionError):
            store.allocate(**params)
        assert monotonic() - started < 1
        writer.rollback()


def test_additive_migration_keeps_original_and_consent_history(prepared):
    database, _, _, _ = setup(prepared)
    before = history(database)
    url = str(database.engine.url)
    downgrade_database(url, "0012_research_continuations")
    assert "research_executions" not in inspect(database.engine).get_table_names()
    assert history(database) == before
    upgrade_database(url)
    assert "research_executions" in inspect(database.engine).get_table_names()
    assert history(database) == before
