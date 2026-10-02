"""Durable pre-call counters, without activating recovery or paid models."""

from datetime import timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest

from tests.test_durable_jobs import _database, _enqueue
from tests.test_risk_engine import NOW
from tradingagents.contracts import RunEventType
from tradingagents.platform.analysis.observer import (
    ResearchBudgetExceeded,
    ResearchExecutionFailed,
    ResearchObserver,
)
from tradingagents.platform.events import RunEventStore
from tradingagents.platform.jobs import DurableJobQueue
from tradingagents.platform.jobs.worker import JobExecutionContext


def test_unfinished_reservation_reopens_as_unknown_usage(tmp_path):
    database, owner, run = _database(tmp_path)
    try:
        _enqueue(database, owner, run)
        with database.session() as session:
            job = DurableJobQueue(session).claim("fixture", lease_for=timedelta(minutes=5), now=NOW)
        context = JobExecutionContext(database, job.job_id, "fixture", timedelta(minutes=5), lambda: NOW)
        clock = [100]

        def emit(kind, payload):
            with context.publication_session() as session:
                RunEventStore(session).append(owner_id=owner, run_id=run.run_id,
                    event_type=RunEventType(kind), occurred_at=NOW, payload={**payload, "attempt": job.attempt})

        observer = ResearchObserver(check_cancelled=context.raise_if_cancelled, emit=emit, clock=lambda: clock[0])
        clock[0] = 112
        observer.on_chat_model_start({}, [], run_id=uuid4())
        # No completion: a separate DB session must still see the reservation.
        with database.session() as session:
            event, = RunEventStore(session).list_after(owner, run.run_id)
            assert event.payload["attempt"] == job.attempt
            assert event.payload["elapsed_seconds"] == 12
            assert event.payload["execution_limits"] == {"wall_seconds": 1800, "model_calls": 128}
            assert event.payload["usage"]["started_model_calls"] == 1
            assert event.payload["usage"]["model_calls"] == 0
            assert event.payload["usage"]["status"] == "incomplete"
            assert event.payload["usage"]["cost"] is None
    finally:
        database.dispose()


def test_new_unfinished_call_does_not_reuse_previous_reported_status():
    events = []
    observer = ResearchObserver(check_cancelled=lambda: None, emit=lambda *args: events.append(args))
    run_id = uuid4()
    observer.on_chat_model_start({}, [], run_id=run_id)
    observer.on_llm_end(SimpleNamespace(generations=[[SimpleNamespace(message=SimpleNamespace(
        usage_metadata={"input_tokens": 10, "output_tokens": 5, "total_tokens": 15}))]]), run_id=run_id)
    assert observer.receipt()["usage"]["status"] == "reported"
    observer.on_chat_model_start({}, [], run_id=uuid4())
    assert observer.receipt()["usage"]["status"] == "incomplete"
    assert events[-1][1]["usage"]["started_model_calls"] == 2
    assert events[-1][1]["usage"]["total_tokens"] == 15


def test_failed_admission_emission_does_not_return_permission_to_invoke():
    entered = []

    def refuse(*args):
        raise RuntimeError("synthetic persistence unavailable")

    observer = ResearchObserver(check_cancelled=lambda: None, emit=refuse)
    with pytest.raises(RuntimeError, match="synthetic persistence unavailable"):
        observer.on_chat_model_start({}, [], run_id=uuid4())
        entered.append("provider")
    assert not entered
    assert observer.started_calls == 1 and observer.receipt()["usage"]["status"] == "incomplete"


def test_commit_after_original_deadline_does_not_grant_provider_admission():
    clock = [0]
    events, entered = [], []

    def emit(kind, payload):
        events.append((kind, payload))
        clock[0] = 2

    observer = ResearchObserver(check_cancelled=lambda: None, emit=emit, clock=lambda: clock[0], max_seconds=1)
    with pytest.raises(ResearchBudgetExceeded):
        observer.on_chat_model_start({}, [], run_id=uuid4())
        entered.append("provider")
    assert not entered
    assert len(events) == 1 and events[0][1]["usage"]["status"] == "incomplete"
    assert observer.started == 0 and observer.started_calls == 1


@pytest.mark.parametrize("persist", [True, False])
def test_supervised_stop_keeps_unknown_usage_and_prevents_later_callbacks(persist):
    events, clock = [], [100]

    def emit(kind, payload):
        if payload.get("execution_stopped") and not persist:
            raise RuntimeError("synthetic fence refusal")
        events.append((kind, payload))

    observer = ResearchObserver(check_cancelled=lambda: None, emit=emit, clock=lambda: clock[0])
    model_id = uuid4()
    observer.on_chat_model_start({}, [], run_id=model_id)
    clock[0] = 112
    if persist:
        observer._record_supervised_stop()
        assert events[-1][1]["execution_stopped"] is True
        assert events[-1][1]["elapsed_seconds"] == 12
    else:
        with pytest.raises(RuntimeError, match="synthetic fence refusal"):
            observer._record_supervised_stop()
        assert len(events) == 1 and "execution_stopped" not in events[0][1]
    assert observer.receipt()["usage"]["status"] == "incomplete"
    assert observer.receipt()["usage"]["cost"] is None
    assert observer.started == 100 and observer.started_calls == 1
    for action in (
        lambda: observer.on_chat_model_start({}, [], run_id=uuid4()),
        lambda: observer.on_llm_end(SimpleNamespace(generations=[]), run_id=model_id),
        lambda: observer.on_llm_error(RuntimeError(), run_id=model_id),
        observer._record_supervised_stop,
    ):
        with pytest.raises(ResearchExecutionFailed, match="already stopped"):
            action()
