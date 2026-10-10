"""Retained budget fixtures only: no consent, checkpoint restore or paid call."""

from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace
from uuid import uuid4

import pytest

from tests.test_accounting_evidence import append, receipt
from tests.test_durable_jobs import _database
from tests.test_research_supervision import SpawnFixtureEngine, assert_child_stopped, request_with
from tests.test_risk_engine import NOW
from tradingagents.contracts import RunEventType
from tradingagents.contracts.runs import DecisionRunInputs, ResearchExecutionLimits
from tradingagents.platform.analysis.accounting import (
    AccountingEvidenceError,
    load_accounting_evidence,
)
from tradingagents.platform.analysis.allowance import (
    build_retained_observer,
    load_remaining_allowance,
)
from tradingagents.platform.analysis.observer import ResearchBudgetExceeded
from tradingagents.platform.analysis.supervision import SupervisedAnalysisEngine
from tradingagents.platform.events import RunEventStore
from tradingagents.platform.persistence import PlatformRepository


def setup(tmp_path, *, calls=1, closed=True):
    database, owner, original = _database(tmp_path)
    limits, source = ResearchExecutionLimits(wall_seconds=60, model_calls=3), uuid4()
    run = original.model_copy(update={"run_id": uuid4(), "execution_limits": limits,
        "snapshot_ids": (source,), "decision_inputs": DecisionRunInputs(
            snapshots_by_analyst={"market": (source,)}, source_max_age_seconds={"market": 0})})
    payloads = receipt(calls=calls)
    for payload in payloads:
        payload["execution_limits"] = limits.model_dump(mode="json")
        payload["elapsed_seconds"] = 10
    if closed:
        payloads.append({**deepcopy(payloads[-1]), "execution_stopped": True})
    with database.session() as session:
        PlatformRepository(session).save_run(run)
        append(session, owner, run, 1, payloads)
    with database.session() as session:
        evidence = load_accounting_evidence(session=session, owner_id=owner, run_id=run.run_id)
    return database, owner, run, evidence


def emit_for(database, owner, run):
    with database.session() as session:
        RunEventStore(session).append(owner_id=owner, run_id=run.run_id,
            event_type=RunEventType.RESEARCH_EXECUTION_STARTED, occurred_at=NOW, payload={"attempt": 2})

    def emit(kind, payload):
        with database.session() as session:
            RunEventStore(session).append(owner_id=owner, run_id=run.run_id,
                event_type=RunEventType(kind), occurred_at=NOW, payload={**payload, "attempt": 2})

    return emit


def test_retained_budget_enforces_original_caps_without_double_counting(tmp_path):
    database, owner, run, evidence = setup(tmp_path)
    try:
        clock = [100]
        # Construction happens before the synthetic second execution marker.
        forward = [None]
        with database.session() as session:
            observer = build_retained_observer(session=session, owner_id=owner, run_id=run.run_id,
                expected_accounting=evidence, check_cancelled=lambda: None,
                emit=lambda *args: forward[0](*args), clock=lambda: clock[0])
        forward[0] = emit_for(database, owner, run)
        assert observer.remaining_seconds() == 50
        assert observer.max_seconds == 60 and observer.max_calls == 3 and observer.started == 100
        clock[0] = 110
        for _ in range(2):
            key = uuid4()
            observer.on_chat_model_start({}, [], run_id=key)
            observer.on_llm_end(SimpleNamespace(generations=[[SimpleNamespace(message=SimpleNamespace(
                usage_metadata={"input_tokens": 10, "output_tokens": 5, "total_tokens": 15}))]]), run_id=key)
        with pytest.raises(ResearchBudgetExceeded, match="model-call budget exhausted"):
            observer.on_chat_model_start({}, [], run_id=uuid4())
        assert observer.started_calls == 2 and observer.remaining_seconds() == 40
        observer._record_supervised_stop()  # Unit-only synthetic stop, not process proof.
        with database.session() as session:
            total = load_accounting_evidence(session=session, owner_id=owner, run_id=run.run_id)
            assert total.started_calls == 3 and total.reported_total_tokens == 45
            assert total.elapsed_upper_bound == 20  # 10 prior + 10 current, not 10 + 20.
            assert load_remaining_allowance(session=session, owner_id=owner, run_id=run.run_id).assessment_status == "BLOCKED"
    finally:
        database.dispose()


def test_retained_wall_deadline_is_not_a_fresh_clock_budget(tmp_path):
    database, owner, run, evidence = setup(tmp_path)
    try:
        clock = [100]
        with database.session() as session:
            observer = build_retained_observer(session=session, owner_id=owner, run_id=run.run_id,
                expected_accounting=evidence, check_cancelled=lambda: None, emit=lambda *_: None,
                clock=lambda: clock[0])
        clock[0] = 149.5
        assert observer.remaining_seconds() == 0.5
        clock[0] = 150
        with pytest.raises(ResearchBudgetExceeded, match="wall-time budget exhausted"):
            observer.on_chat_model_start({}, [], run_id=uuid4())
        assert observer.started_calls == 0
    finally:
        database.dispose()


@pytest.mark.parametrize("kind", ["unknown", "exhausted", "stale", "owner", "altered", "type", "run"])
def test_retained_observer_refuses_unusable_or_changed_evidence(tmp_path, kind):
    database, owner, run, evidence = setup(tmp_path, calls=3 if kind == "exhausted" else 1,
                                         closed=kind != "unknown")
    try:
        if kind == "stale":
            emit_for(database, owner, run)
        if kind == "altered":
            evidence = replace(evidence, original_model_calls=128)
        if kind == "type":
            evidence = SimpleNamespace(**evidence.__dict__)
        error = ResearchBudgetExceeded if kind == "exhausted" else AccountingEvidenceError
        with database.session() as session, pytest.raises(error):
            build_retained_observer(session=session, owner_id=uuid4() if kind == "owner" else owner,
                run_id=uuid4() if kind == "run" else run.run_id, expected_accounting=evidence,
                check_cancelled=lambda: None, emit=lambda *_: None)
    finally:
        database.dispose()


def test_actual_spawn_uses_retained_parent_call_cap(tmp_path):
    database, owner, run, evidence = setup(tmp_path / "db", calls=2)
    try:
        forward, marker = [None], tmp_path / "child"
        with database.session() as session:
            observer = build_retained_observer(session=session, owner_id=owner, run_id=run.run_id,
                expected_accounting=evidence, check_cancelled=lambda: None,
                emit=lambda *args: forward[0](*args), clock=lambda: 100)
        forward[0] = emit_for(database, owner, run)
        result = SupervisedAnalysisEngine(base_config={"marker": str(marker)},
            engine_factory=SpawnFixtureEngine).analyze(request_with(observer))
        assert result.narrative_signal == "REVIEW" and observer.started_calls == 1
        assert_child_stopped(marker)
        with database.session() as session:
            total = load_accounting_evidence(session=session, owner_id=owner, run_id=run.run_id)
            assert total.started_calls == 3 and total.reported_total_tokens == 35
            assert total.elapsed_upper_bound == 10  # Frozen fixture clock, not real latency.
            assert load_remaining_allowance(session=session, owner_id=owner, run_id=run.run_id).remaining_model_calls == 0
    finally:
        database.dispose()


def test_retained_deadline_after_emit_does_not_admit_provider(tmp_path):
    database, owner, run, evidence = setup(tmp_path)
    try:
        clock, events, entered = [100], [], []

        def emit(kind, payload):
            events.append((kind, payload))
            clock[0] = 151

        with database.session() as session:
            observer = build_retained_observer(session=session, owner_id=owner, run_id=run.run_id,
                expected_accounting=evidence, check_cancelled=lambda: None, emit=emit, clock=lambda: clock[0])
        clock[0] = 149.5
        with pytest.raises(ResearchBudgetExceeded):
            observer.on_chat_model_start({}, [], run_id=uuid4())
            entered.append("provider")
        assert not entered and observer.started_calls == 1
        assert events[0][1]["elapsed_seconds"] == 49.5  # Current attempt, not prior-inclusive 59.5.
        assert events[0][1]["usage"]["status"] == "incomplete"
    finally:
        database.dispose()
