"""Separate stop facts cannot authorize publication or refund accounting."""

from contextlib import contextmanager
from copy import deepcopy
from dataclasses import replace
from datetime import timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.attributes import flag_modified

from tests.test_accounting_evidence import append, receipt
from tests.test_continuation_consent import history, prepared as prepared
from tests.test_linked_publication import entered
from tests.test_native_recorder_spawn import (
    test_exact_engine_native_spawn_recorder_with_parent_persistence as run_native,
)
from tradingagents.platform.analysis.accounting import (
    AccountingEvidenceError,
    load_accounting_evidence,
    recheck_accounting_evidence,
)
from tradingagents.platform.analysis.allowance import load_remaining_allowance
from tradingagents.platform.analysis.linked_stops import LinkedStopError, LinkedStopStore
from tradingagents.platform.analysis.observer import ResearchExecutionFailed
from tradingagents.platform.persistence import (
    PlatformRepository,
    downgrade_database,
    upgrade_database,
)
from tradingagents.platform.persistence.models import (
    DecisionRow,
    ResearchExecutionCompletionRow,
    ResearchExecutionStopRow,
)


def capture_native(tmp_path, monkeypatch, *, mode="linked_stopped", fault=None):
    captured = []
    original = LinkedStopStore.record_supervised

    def remember(store, engine):
        captured.append((store, engine))
        if fault == "renewal":
            engine.linked_context._renewal_failed = True
            return original(store, engine)
        if fault == "guards":
            context = engine.linked_context
            original_lease = context._lease
            original_binding = engine._linked_native_binding
            original_scope = engine._linked_native_scope
            database = store.executions.database
            for mutation in ("nonce", "attempt", "observer", "process", "reader"):
                if mutation == "nonce":
                    context._lease = replace(original_lease, token=uuid4())
                elif mutation == "attempt":
                    context._lease = replace(original_lease, reservation=replace(original_lease.reservation, attempt=2.0))
                elif mutation == "observer":
                    engine._linked_native_binding = (context, object(), original_binding[2])
                elif mutation == "process":
                    engine._linked_native_scope = (SimpleNamespace(pid=1, exitcode=0), *original_scope[1:])
                else:
                    engine._linked_native_scope = (original_scope[0], SimpleNamespace(is_alive=lambda: True), *original_scope[2:])
                with pytest.raises(LinkedStopError, match="^linked local stop requires review$"):
                    original(store, engine)
                with database.session() as session:
                    assert session.get(ResearchExecutionStopRow, context.execution_id) is None
                context._lease = original_lease
                engine._linked_native_binding, engine._linked_native_scope = original_binding, original_scope
            return original(store, engine)
        if fault is None:
            return original(store, engine)
        session_factory = store.executions.database.session

        @contextmanager
        def failed(*args, **kwargs):
            with session_factory(*args, **kwargs) as session:
                yield session
                if fault == "rollback":
                    raise SQLAlchemyError("synthetic stop commit refused")
            raise SQLAlchemyError("synthetic committed stop ACK lost")

        with monkeypatch.context() as patch:
            patch.setattr(store.executions.database, "session", failed)
            return original(store, engine)

    monkeypatch.setattr(LinkedStopStore, "record_supervised", remember)
    # Actual joined production child/graph/owner context; no standalone result.
    if fault == "renewal" and mode == "linked_stopped":
        # This fixture normally publishes after clean exit. Injected renewal
        # uncertainty must refuse that result, while retaining actual stop proof.
        with pytest.raises(ResearchExecutionFailed, match="^linked result publication requires review$"):
            run_native(tmp_path, monkeypatch, "English", False, mode, stop_receipt_expected=True)
    else:
        run_native(tmp_path, monkeypatch, "English", False, mode, stop_receipt_expected=fault != "rollback")
    assert len(captured) == 1
    return captured[0]


@pytest.mark.parametrize("mode", ["linked_stopped", "linked_cancelled", "linked_expired"])
@pytest.mark.parametrize("fault", ["rollback", "lost_ack"])
def test_actual_native_stop_commit_and_ack_uncertainty(tmp_path, monkeypatch, mode, fault):
    store, engine = capture_native(tmp_path, monkeypatch, mode=mode, fault=fault)
    context = engine.linked_context
    before = history(store.executions.database)
    value = store.read(owner_id=context.owner_id, execution_id=context.execution_id)
    assert (value is not None) is (fault == "lost_ack")
    assert history(store.executions.database) == before  # Read-only ACK resolution.
    if value is not None:
        assert value.continuation_authorized is False and value.provider_cost_known is False
        assert str(context.owner_id) not in repr(value) and str(context._lease.token) not in repr(value)


def test_actual_parent_scope_and_private_identity_are_required(tmp_path, monkeypatch):
    store, engine = capture_native(tmp_path, monkeypatch, mode="linked_expired", fault="guards")
    context = engine.linked_context
    stop = store.read(owner_id=context.owner_id, execution_id=context.execution_id)
    assert stop is not None and stop.continuation_authorized is False


@pytest.mark.parametrize("mode", ["linked_stopped", "linked_cancelled", "linked_expired"])
def test_renewal_uncertainty_retains_actual_stop_without_publication(tmp_path, monkeypatch, mode):
    store, engine = capture_native(tmp_path, monkeypatch, mode=mode, fault="renewal")
    context = engine.linked_context
    stop = store.read(owner_id=context.owner_id, execution_id=context.execution_id)
    assert stop is not None
    assert stop.continuation_authorized is False and stop.provider_cost_known is False
    before = history(store.executions.database)
    with pytest.raises(ValueError):
        context.raise_if_cancelled()
    with pytest.raises(ValueError), context.publication_session():
        pytest.fail("renewal uncertainty must not authorize publication")
    assert history(store.executions.database) == before
    with store.executions.database.session() as session:
        assert session.get(ResearchExecutionCompletionRow, context.execution_id) is None
        assert not session.scalars(select(DecisionRow).where(DecisionRow.run_id == context.run_id)).all()
        assert PlatformRepository(session).get_run(context.run_id, context.owner_id) == engine.recording_inputs.read().run


def test_native_receipt_reader_rejects_tamper_and_foreign_owner(tmp_path, monkeypatch):
    store, engine = capture_native(tmp_path, monkeypatch)
    context, database = engine.linked_context, store.executions.database
    expected = store.read(owner_id=context.owner_id, execution_id=context.execution_id)
    with pytest.raises(LinkedStopError):
        store.read(owner_id=uuid4(), execution_id=context.execution_id)
    with database.session() as session:
        row = session.get(ResearchExecutionStopRow, context.execution_id)
        original = {key: deepcopy(getattr(row, key)) for key in
            ("payload", "payload_hash", "owner_id", "source_run_id", "stopped_at")}
    changes = [("payload_hash", "0" * 64), ("owner_id", uuid4()), ("source_run_id", uuid4()),
        ("stopped_at", original["stopped_at"] + timedelta(seconds=1))]
    for field, value in [("continuation_authorized", 0), ("provider_cost_known", True),
            ("child_reaped", False), ("reader_closed", False), ("local_elapsed_seconds", True),
            ("local_elapsed_seconds", -1), ("local_elapsed_seconds", 10**400),
            ("child_exitcode", True), ("attempt", 2.0),
            ("unexpected", "synthetic private diagnostic"), ("checkpoint_hash", "0" * 64)]:
        payload = deepcopy(original["payload"])
        payload[field] = value
        changes.append(("payload", payload))
    for index, (field, value) in enumerate(changes):
        with database.session() as session:
            row = session.get(ResearchExecutionStopRow, context.execution_id)
            setattr(row, field, value)
            if field == "payload":
                # SQLAlchemy otherwise sees False==0 / 2==2.0 as unchanged.
                # Force the actual corrupt JSON bytes into this disposable DB.
                flag_modified(row, "payload")
        try:
            store.read(owner_id=context.owner_id, execution_id=context.execution_id)
        except LinkedStopError as error:
            assert str(error) == "linked local stop requires review"
        else:
            pytest.fail(f"Stop mutation {index} ({field}) was not refused")
        with database.session() as session:
            row = session.get(ResearchExecutionStopRow, context.execution_id)
            for key, original_value in original.items():
                setattr(row, key, deepcopy(original_value))
            flag_modified(row, "payload")
        assert store.read(owner_id=context.owner_id, execution_id=context.execution_id) == expected


def test_native_stop_remains_readable_after_later_accounting_without_grant(tmp_path, monkeypatch):
    store, engine = capture_native(tmp_path, monkeypatch, mode="linked_cancelled")
    context, database = engine.linked_context, store.executions.database
    expected = store.read(owner_id=context.owner_id, execution_id=context.execution_id)
    with database.session() as session:
        prefix = load_accounting_evidence(session=session, owner_id=context.owner_id, run_id=context.run_id)
        run = PlatformRepository(session).get_run(context.run_id, context.owner_id)
        # Schema/accounting-only later-attempt fixture; NOT actual third dispatch.
        append(session, context.owner_id, run, 3, receipt(finish=False))
    assert store.read(owner_id=context.owner_id, execution_id=context.execution_id) == expected
    with database.session() as session:
        latest = load_accounting_evidence(session=session, owner_id=context.owner_id, run_id=context.run_id)
        assert latest.attempts == (1, 2, 3) and latest.started_calls == prefix.started_calls + 1
        assert latest.elapsed_upper_bound is None
        with pytest.raises(AccountingEvidenceError):
            recheck_accounting_evidence(session=session, owner_id=context.owner_id, run_id=context.run_id, expected=prefix)
        allowance = load_remaining_allowance(session=session, owner_id=context.owner_id, run_id=context.run_id)
        assert allowance.accounting == latest and allowance.assessment_status == "UNVERIFIED"
    assert expected.continuation_authorized is False and expected.provider_cost_known is False


def test_browser_style_payload_is_not_supervision_proof(prepared):
    database, executions, _, _, context, _ = entered(prepared)
    before = history(database)
    with pytest.raises(LinkedStopError, match="^linked local stop requires review$"):
        LinkedStopStore(executions).record_supervised(SimpleNamespace(linked_context=context,
            child_reaped=True, reader_closed=True, elapsed_seconds=0))
    assert history(database) == before
    with database.session() as session:
        assert not session.scalars(select(ResearchExecutionStopRow)).all()


def test_missing_dispatch_and_foreign_owner_cannot_read_a_stop(prepared):
    _, executions, _, _, context, _ = entered(prepared)
    store = LinkedStopStore(executions)
    for owner_id in (context.owner_id, uuid4()):
        with pytest.raises(LinkedStopError):
            store.read(owner_id=owner_id, execution_id=context.execution_id)


def test_additive_empty_stop_schema_reversal_preserves_original_history(prepared):
    database = prepared[0]
    before = history(database)
    url = database.engine.url.render_as_string(hide_password=False)
    assert "research_execution_stops" in inspect(database.engine).get_table_names()
    downgrade_database(url, "0016_linked_results")
    assert "research_execution_stops" not in inspect(database.engine).get_table_names()
    assert history(database) == before
    upgrade_database(url)
    assert "research_execution_stops" in inspect(database.engine).get_table_names()
    assert history(database) == before
