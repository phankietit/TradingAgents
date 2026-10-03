"""Actual parent callbacks / private append-only persistence, no provider calls."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import replace
from datetime import timedelta
from threading import Barrier
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import SQLAlchemyError

from tests.test_continuation_consent import history, prepared as prepared
from tests.test_linked_execution import setup
from tradingagents.platform.analysis.accounting import (
    AccountingEvidenceError,
    load_accounting_evidence,
)
from tradingagents.platform.analysis.allowance import load_remaining_allowance
from tradingagents.platform.analysis.checkpoint_codec import SnapshotCheckpointCodec
from tradingagents.platform.analysis.checkpoint_store import (
    CheckpointStoreError,
    PrivateCheckpointStore,
)
from tradingagents.platform.analysis.linked_execution import LinkedExecutionError
from tradingagents.platform.analysis.linked_publication import LinkedPublicationContext
from tradingagents.platform.analysis.observer import ResearchBudgetExceeded, ResearchExecutionFailed
from tradingagents.platform.auth import OwnerAuth
from tradingagents.platform.persistence import downgrade_database, upgrade_database
from tradingagents.platform.persistence.models import (
    ResearchCheckpointExecutionRow,
    ResearchCheckpointRow,
    ResearchExecutionEntryRow,
    ResearchExecutionEventRow,
    RunEventRow,
)


def entered(prepared):
    database, store, params, clock = setup(prepared)
    reservation = store.allocate(**params)
    lease = store.claim(execution_id=reservation.execution_id, worker_id="linked-fixture")
    before = history(database)
    context = LinkedPublicationContext.prepare(store, lease, observer_clock=lambda: (
        clock[0] - lease.started_at).total_seconds())
    return database, store, params, clock, context, before


def raw_checkpoint(context, store, *, text="Completed linked pending output"):
    checkpoints = PrivateCheckpointStore(codec=store.consents.codec)
    with store.database.session() as session:
        value = checkpoints.load_latest(session=session, owner_id=context.owner_id, run_id=context.run_id)
    value.pending_writes.append((str(uuid4()), "market_report", text))
    return checkpoints, store.consents.codec.encode(value)


def save(context, checkpoints, raw):
    return checkpoints.commit(context=context, owner_id=context.owner_id, run_id=context.run_id, raw=raw)


def evidence(database, context):
    with database.session() as session:
        return load_accounting_evidence(session=session, owner_id=context.owner_id, run_id=context.run_id)


def assert_old_history_unchanged(database, before):
    after = history(database)
    for table, rows in before.items():
        assert all(row in after[table] for row in rows)
        if table in {"analysis_runs", "analysis_jobs"}:
            assert after[table] == rows


@pytest.mark.parametrize("prepared", [False,
    pytest.param("postgres_failed", marks=pytest.mark.integration)], indirect=True)
def test_parent_entry_usage_stop_checkpoint_provenance_and_original_history(prepared):
    database, store, _, clock, context, before = entered(prepared)
    initial = evidence(database, context)
    assert initial.attempts == (1, 2) and initial.started_calls == 1
    assert initial.elapsed_upper_bound is None  # New active entry is not known stopped.
    assert initial.reported_total_tokens == 15 and initial.exact_elapsed_known is False
    with database.session() as session:
        assert load_remaining_allowance(session=session, owner_id=context.owner_id,
            run_id=context.run_id).assessment_status == "UNVERIFIED"
    call = uuid4()
    context.observer.on_chat_model_start({}, [], run_id=call)
    reserved = evidence(database, context)
    assert reserved.started_calls == 2 and reserved.completed_calls == 1
    clock[0] += timedelta(seconds=3)
    context.observer.on_llm_end(SimpleNamespace(generations=[[SimpleNamespace(message=SimpleNamespace(
        usage_metadata={"input_tokens": 20, "output_tokens": 7, "total_tokens": 27}))]]), run_id=call)
    latest = evidence(database, context)
    assert latest.started_calls == latest.completed_calls == 2 and latest.reported_total_tokens == 42
    assert latest.elapsed_lower_bound == 13 and latest.elapsed_upper_bound is None
    checkpoints, raw = raw_checkpoint(context, store)
    first = save(context, checkpoints, raw)
    assert save(context, checkpoints, raw) == first
    with database.session() as session:
        row = session.get(ResearchCheckpointRow, first.record_id)
        actor = session.get(ResearchCheckpointExecutionRow, first.record_id)
        assert row.attempt == 2 and row.job_id == context.job_id and row.sequence == 2
        assert actor.execution_id == context.execution_id
        entry = session.get(ResearchExecutionEntryRow, context.execution_id)
        assert session.get(ResearchExecutionEventRow, entry.event_id).execution_id == context.execution_id
        assert len(session.scalars(select(ResearchCheckpointExecutionRow)).all()) == 1
        assert checkpoints.load_latest(session=session, owner_id=context.owner_id,
            run_id=context.run_id) == checkpoints.codec.decode(raw)
    clock[0] += timedelta(seconds=2)
    # This fixture invokes the trusted hook; it is not child-reaping evidence.
    context.observer._record_supervised_stop()
    stopped = evidence(database, context)
    assert stopped.elapsed_upper_bound == stopped.elapsed_lower_bound == 15
    assert stopped.reported_total_tokens == 42 and stopped.exact_elapsed_known is False
    with pytest.raises(ResearchExecutionFailed):
        context.observer._record_supervised_stop()
    assert_old_history_unchanged(database, before)


@pytest.mark.parametrize("prepared", [False,
    pytest.param("postgres_failed", marks=pytest.mark.integration)], indirect=True)
def test_checkpoint_two_writers_serialize_without_relabeling_original(prepared):
    database, store, _, _, context, before = entered(prepared)
    checkpoints, raw = raw_checkpoint(context, store)
    other = checkpoints.codec.decode(raw)
    other.pending_writes.append((str(uuid4()), "market_report", "Second completed task"))
    raw2 = checkpoints.codec.encode(other)
    barrier = Barrier(2)

    def call(data):
        barrier.wait(timeout=5)
        return save(context, checkpoints, data)

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(call, (raw, raw2)))
    assert sorted(result.sequence for result in results) == [2, 3]
    with database.session() as session:
        assert len(session.scalars(select(ResearchCheckpointExecutionRow)).all()) == 2
    assert_old_history_unchanged(database, before)


def test_claim_prepare_gap_is_charged_and_deadline_does_not_reset(prepared):
    database, store, params, clock = setup(prepared)
    row = store.allocate(**params)
    lease = store.claim(execution_id=row.execution_id, worker_id="fixture")
    clock[0] += timedelta(seconds=25)
    context = LinkedPublicationContext.prepare(store, lease, observer_clock=lambda: 100)
    assert evidence(database, context).elapsed_lower_bound == 35
    context.heartbeat()
    assert context._lease.deadline_at == lease.deadline_at and context._lease.started_at == lease.started_at


@pytest.mark.parametrize("fence", ["cancel", "expired", "disabled", "nonce", "owner", "run", "attempt", "observer_reset"])
def test_lost_authority_cannot_publish_checkpoint_or_usage(prepared, fence):
    database, store, params, clock, context, _ = entered(prepared)
    checkpoints, raw = raw_checkpoint(context, store)
    before = history(database)
    if fence == "cancel":
        store.request_cancel(**params)
    elif fence == "expired":
        clock[0] = context._lease.expires_at
    elif fence == "disabled":
        with database.session() as session:
            OwnerAuth(session).disable_owner(context.owner_id, now=clock[0])
    elif fence == "nonce":
        context._lease = replace(context._lease, token=uuid4())
    elif fence == "attempt":
        context._lease = replace(context._lease, reservation=replace(context._lease.reservation, attempt=2.0))
    elif fence == "owner":
        context.owner_id = uuid4()
    elif fence == "run":
        context.run_id = uuid4()
    else:
        context.observer._retained_started_calls = 0
    with pytest.raises((LinkedExecutionError, CheckpointStoreError)):
        save(context, checkpoints, raw)
    with pytest.raises(LinkedExecutionError):
        context.observer.on_chat_model_start({}, [], run_id=uuid4())
    assert history(database) == before


def test_expiry_during_checkpoint_transaction_rolls_back_no_ack(prepared, monkeypatch):
    database, store, _, clock, context, _ = entered(prepared)
    checkpoints, raw = raw_checkpoint(context, store)
    before = history(database)
    original = context.publication_session

    @contextmanager
    def late(**options):
        with original(**options) as session:
            yield session
            clock[0] = context._lease.expires_at

    monkeypatch.setattr(context, "publication_session", late)
    with pytest.raises(LinkedExecutionError):
        save(context, checkpoints, raw)
    assert history(database) == before
    with database.session() as session:
        assert session.scalar(select(ResearchCheckpointExecutionRow)) is None


def test_expiry_while_acquiring_source_locks_cannot_be_renewed(prepared, monkeypatch):
    _, store, _, clock, context, _ = entered(prepared)
    original = store._source

    def slow(*args, **options):
        result = original(*args, **options)
        clock[0] = context._lease.expires_at
        return result

    monkeypatch.setattr(store, "_source", slow)
    with pytest.raises(LinkedExecutionError):
        context.heartbeat()


def test_lost_entry_ack_retains_uncertainty_and_refuses_second_entry(prepared, monkeypatch):
    database, store, params, _ = setup(prepared)
    row = store.allocate(**params)
    lease = store.claim(execution_id=row.execution_id, worker_id="fixture")
    original = store._transaction

    @contextmanager
    def lost(**options):
        entered = False
        with original(**options) as (session, now):
            yield session, now
            entered = session.get(ResearchExecutionEntryRow, row.execution_id) is not None
        if entered:
            raise SQLAlchemyError("fixture lost ACK after committed entry")

    monkeypatch.setattr(store, "_transaction", lost)
    with pytest.raises(SQLAlchemyError):
        LinkedPublicationContext.prepare(store, lease, observer_clock=lambda: 0)
    before = history(database)
    monkeypatch.setattr(store, "_transaction", original)
    with pytest.raises(AccountingEvidenceError):
        LinkedPublicationContext.prepare(store, lease, observer_clock=lambda: 0)
    assert history(database) == before
    with database.session() as session:
        result = load_accounting_evidence(session=session, owner_id=row.owner_id, run_id=row.source_run_id)
        assert result.attempts == (1, 2) and result.elapsed_upper_bound is None
        assert len(session.scalars(select(ResearchExecutionEntryRow)).all()) == 1


@pytest.mark.parametrize("mutation", ["missing_link", "attempt", "marker", "marker_link"])
def test_corrupt_latest_actor_provenance_never_falls_back(prepared, mutation):
    database, store, _, _, context, _ = entered(prepared)
    checkpoints, raw = raw_checkpoint(context, store)
    saved = save(context, checkpoints, raw)
    with database.session() as session:
        if mutation == "missing_link":
            session.delete(session.get(ResearchCheckpointExecutionRow, saved.record_id))
        elif mutation == "attempt":
            session.get(ResearchCheckpointRow, saved.record_id).attempt = 1
        else:
            entry = session.get(ResearchExecutionEntryRow, context.execution_id)
            if mutation == "marker":
                session.get(RunEventRow, entry.event_id).payload = {"attempt": True}
            else:
                session.delete(session.get(ResearchExecutionEventRow, entry.event_id))
    with database.session() as session, pytest.raises(CheckpointStoreError):
        checkpoints.load_latest(session=session, owner_id=context.owner_id, run_id=context.run_id)


def test_idempotent_old_checkpoint_is_not_relabelled_as_new_execution(prepared):
    database, store, _, _, context, _ = entered(prepared)
    checkpoints = PrivateCheckpointStore(codec=store.consents.codec)
    with database.session() as session:
        old = session.scalar(select(ResearchCheckpointRow))
        raw, identity = old.payload, old.record_id
    assert save(context, checkpoints, raw).record_id == identity
    with database.session() as session:
        assert session.get(ResearchCheckpointExecutionRow, identity) is None
        assert session.get(ResearchCheckpointRow, identity).attempt == 1


def test_aggregate_original_call_cap_not_reset_for_linked_attempt(prepared):
    database, _, _, _, context, _ = entered(prepared)
    # 1 prior reservation +127 new reservations exhaust original 128 cap.
    for _ in range(127):
        call = uuid4()
        context.observer.on_chat_model_start({}, [], run_id=call)
        context.observer.on_llm_error(RuntimeError("synthetic provider error"), run_id=call)
    assert evidence(database, context).started_calls == 128
    before = history(database)
    with pytest.raises(ResearchBudgetExceeded):
        context.observer.on_chat_model_start({}, [], run_id=uuid4())
    assert history(database) == before


def test_payload_cannot_fabricate_stop_or_reservation(prepared):
    database, _, _, _, context, _ = entered(prepared)
    before = history(database)
    payload = context.observer._usage_payload()
    with pytest.raises(LinkedExecutionError):
        context._emit("model.usage", {**payload, "execution_stopped": True})
    payload["usage"]["started_model_calls"] = 128
    with pytest.raises(LinkedExecutionError):
        context._emit("model.usage", payload)
    assert history(database) == before


@pytest.mark.parametrize("elapsed", [True, float("inf"), float("nan"), -1, 1])
def test_elapsed_receipt_cannot_invent_future_or_nonfinite_time(prepared, elapsed):
    database, _, _, _, context, _ = entered(prepared)
    before = history(database)
    with pytest.raises(LinkedExecutionError):
        context._emit("model.usage", {**context.observer._usage_payload(), "elapsed_seconds": elapsed})
    assert history(database) == before


def test_transaction_guard_rejects_aggregate_over_cap_even_matching_observer_payload(prepared):
    database, _, _, _, context, _ = entered(prepared)
    context.observer.started_calls = 128
    before = history(database)
    with pytest.raises(LinkedExecutionError):
        context._emit("model.usage", context.observer._usage_payload())
    assert history(database) == before


@pytest.mark.parametrize("change", ["fingerprint", "nodes"])
def test_linked_checkpoint_codec_must_match_original_reviewed_contract(prepared, change):
    database, store, _, _, context, _ = entered(prepared)
    _, raw = raw_checkpoint(context, store)
    value = store.consents.codec.decode(raw)
    codec = SnapshotCheckpointCodec(fingerprint="b" * 64 if change == "fingerprint" else store.consents.codec.fingerprint,
        nodes={"Market Analyst", "News Analyst"} if change == "nodes" else store.consents.codec.nodes)
    checkpoints = PrivateCheckpointStore(codec=codec)
    before = history(database)
    with pytest.raises(LinkedExecutionError):
        save(context, checkpoints, codec.encode(value))
    assert history(database) == before


@pytest.mark.parametrize("committed", [False, True])
def test_checkpoint_commit_uncertainty_never_relabels_or_double_appends(prepared, monkeypatch, committed):
    database, store, _, _, context, _ = entered(prepared)
    checkpoints, raw = raw_checkpoint(context, store)
    original = context.publication_session

    @contextmanager
    def uncertain(**options):
        with original(**options) as session:
            yield session
            if not committed:
                raise SQLAlchemyError("PRIVATE_NEVER_ECHO")
        if committed:
            raise SQLAlchemyError("PRIVATE_NEVER_ECHO")

    monkeypatch.setattr(context, "publication_session", uncertain)
    with pytest.raises((CheckpointStoreError, LinkedExecutionError)) as raised:
        save(context, checkpoints, raw)
    assert "PRIVATE_NEVER_ECHO" not in str(raised.value)
    monkeypatch.setattr(context, "publication_session", original)
    with database.session() as session:
        assert len(session.scalars(select(ResearchCheckpointExecutionRow)).all()) == int(committed)
    recovered = save(context, checkpoints, raw)
    assert save(context, checkpoints, raw) == recovered
    with database.session() as session:
        assert len(session.scalars(select(ResearchCheckpointRow)).all()) == 2
        assert len(session.scalars(select(ResearchCheckpointExecutionRow)).all()) == 1


@pytest.mark.parametrize("fence", ["cancel", "expired"])
def test_failed_late_stop_preserves_unknown_elapsed_not_refund(prepared, fence):
    database, store, params, clock, context, _ = entered(prepared)
    if fence == "cancel":
        store.request_cancel(**params)
    else:
        clock[0] = context._lease.expires_at
    with pytest.raises(LinkedExecutionError):
        context.observer._record_supervised_stop()
    assert evidence(database, context).elapsed_upper_bound is None


def test_additive_empty_provenance_migration_preserves_original_evidence(prepared):
    database, _, _, _ = prepared
    before = history(database)
    url = database.engine.url.render_as_string(hide_password=False)
    downgrade_database(url, "0013_research_executions")
    assert "research_execution_entries" not in inspect(database.engine).get_table_names()
    upgrade_database(url)
    assert "research_execution_entries" in inspect(database.engine).get_table_names()
    assert history(database) == before
