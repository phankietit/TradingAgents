"""Restore preflight must not turn a saved tuple into a fresh budget grant."""

from copy import copy, deepcopy
from dataclasses import FrozenInstanceError
from uuid import uuid4

import pytest
from sqlalchemy import select

from tests.test_accounting_evidence import append, receipt
from tests.test_recording_context import envelope, restore_bytes, supervisor
from tests.test_recovery_fingerprint import inputs
from tradingagents.platform.analysis.accounting import load_accounting_evidence
from tradingagents.platform.analysis.allowance import (
    build_retained_observer,
    validate_retained_observer,
)
from tradingagents.platform.analysis.observer import ResearchBudgetExceeded, ResearchObserver
from tradingagents.platform.jobs.worker import JobCancellationRequested
from tradingagents.platform.persistence import Database, PlatformRepository, upgrade_database
from tradingagents.platform.persistence.models import RunEventRow


def prepared(tmp_path, *, check_cancelled=None):
    args = inputs()
    url = f"sqlite:///{tmp_path / 'binding.db'}"
    upgrade_database(url)
    database = Database(url)
    payloads = receipt()
    for payload in payloads:
        payload["elapsed_seconds"] = 10
    payloads.append({**deepcopy(payloads[-1]), "execution_stopped": True})
    clock, emitted = [100.0], []
    with database.session() as session:
        repository = PlatformRepository(session)
        repository.add_instrument(args["request"].instrument)
        repository.save_run(args["run"])
        append(session, args["owner_id"], args["run"], 1, payloads)
    with database.session() as session:
        evidence = load_accounting_evidence(session=session, owner_id=args["owner_id"], run_id=args["run"].run_id)
        observer = build_retained_observer(session=session, owner_id=args["owner_id"], run_id=args["run"].run_id,
            expected_accounting=evidence, check_cancelled=check_cancelled or (lambda: None),
            emit=lambda *event: emitted.append(event),
            clock=lambda: clock[0])
        rows = [(row.event_id, deepcopy(row.payload)) for row in session.scalars(select(RunEventRow)).all()]
    return args, database, observer, clock, emitted, rows


@pytest.mark.parametrize("mutation", [
    "fresh", "copied", "debit_calls", "debit_time", "caps", "bool_cap", "float_cap", "clock",
    "started", "emit", "cancelled", "save_stage", "binding", "used", "stopped",
    "owner", "run", "config", "run_limits",
])
def test_restore_rejects_unbound_reset_or_changed_attempt_before_spawn(tmp_path, monkeypatch, mutation):
    args, database, observer, clock, emitted, rows = prepared(tmp_path)
    try:
        if mutation == "fresh":
            observer = ResearchObserver(check_cancelled=lambda: None, emit=lambda *_: None)
        elif mutation == "copied":
            observer = copy(observer)
        elif mutation == "debit_calls":
            observer._retained_started_calls = 0
        elif mutation == "debit_time":
            observer._retained_elapsed_seconds = None
        elif mutation == "caps":
            observer.max_seconds = 3600
        elif mutation == "bool_cap":
            observer.max_calls = True
        elif mutation == "float_cap":
            observer.max_calls = 128.0
        elif mutation == "clock":
            observer.clock = lambda: clock[0]
        elif mutation == "started":
            observer.started += 1
        elif mutation in {"emit", "cancelled", "save_stage"}:
            setattr(observer, "check_cancelled" if mutation == "cancelled" else mutation, lambda *_: None)
        elif mutation == "binding":
            observer._retained_binding = object()
        elif mutation == "used":
            observer.on_chat_model_start({}, [], run_id=uuid4())
        elif mutation == "stopped":
            observer._record_supervised_stop()
        elif mutation in {"owner", "run", "config", "run_limits"}:
            field, value = {"owner": ("owner_id", uuid4()), "run": ("run_id", uuid4()),
                "config": ("config_hash", "sha256:" + "b" * 64),
                "run_limits": ("execution_limits", args["run"].execution_limits.model_copy(update={"model_calls": 127}))}[mutation]
            args["run"] = args["run"].model_copy(update={field: value})
            args["owner_id"] = args["run"].owner_id
        engine = supervisor(args, envelope(args), restore_checkpoint=restore_bytes(args))
        request = args["request"].model_copy(update={"execution_observer": observer})
        captured = list(emitted)
        started_calls = observer.started_calls

        def forbidden(*_args, **_kwargs):
            raise AssertionError("invalid observer spawned a child")

        monkeypatch.setattr("tradingagents.platform.analysis.supervision.get_context", forbidden)
        with pytest.raises(ValueError, match="^invalid checkpoint bridge configuration$") as raised:
            engine.analyze(request)
        assert raised.value.__cause__ is None
        assert observer.started_calls == started_calls and emitted == captured
        with database.session() as session:
            assert [(row.event_id, row.payload) for row in session.scalars(select(RunEventRow)).all()] == rows
    finally:
        database.dispose()


def test_valid_binding_is_private_frozen_and_keeps_original_clock(tmp_path):
    args, database, observer, clock, emitted, _ = prepared(tmp_path)
    try:
        assert validate_retained_observer(observer=observer, run=args["run"]) is None
        assert str(args["owner_id"]) not in repr(observer._retained_binding)
        assert str(args["run"].run_id) not in repr(observer._retained_binding)
        with pytest.raises(FrozenInstanceError):
            observer._retained_binding.started = 101
        clock[0] = 120
        assert validate_retained_observer(observer=observer, run=args["run"]) is None
        assert observer.remaining_seconds() == 1770
        assert observer.max_seconds == 1800 and observer.max_calls == 128
        assert observer._retained_started_calls == 1
        assert emitted == []
    finally:
        database.dispose()


def test_valid_restore_still_checks_original_deadline_before_spawn(tmp_path, monkeypatch):
    args, database, observer, clock, emitted, _ = prepared(tmp_path)
    try:
        engine = supervisor(args, envelope(args), restore_checkpoint=restore_bytes(args))
        clock[0] = 1890  # 1790 remaining seconds at original construction, not 1800.

        def forbidden(*_args, **_kwargs):
            raise AssertionError("expired observer spawned a child")

        monkeypatch.setattr("tradingagents.platform.analysis.supervision.get_context", forbidden)
        with pytest.raises(ResearchBudgetExceeded, match="wall-time budget exhausted"):
            engine.analyze(args["request"].model_copy(update={"execution_observer": observer}))
        assert observer.started_calls == 0 and emitted == []
    finally:
        database.dispose()


@pytest.mark.parametrize("expired", [False, True])
def test_valid_restore_preserves_cancellation_priority(tmp_path, monkeypatch, expired):
    cancelled = [False]

    def check_cancelled():
        if cancelled[0]:
            raise JobCancellationRequested("cancelled")

    args, database, observer, clock, emitted, _ = prepared(tmp_path, check_cancelled=check_cancelled)
    try:
        engine = supervisor(args, envelope(args), restore_checkpoint=restore_bytes(args))
        cancelled[0] = True
        if expired:
            clock[0] = 1890

        def forbidden(*_args, **_kwargs):
            raise AssertionError("cancelled restore spawned a child")

        monkeypatch.setattr("tradingagents.platform.analysis.supervision.get_context", forbidden)
        with pytest.raises(JobCancellationRequested):
            engine.analyze(args["request"].model_copy(update={"execution_observer": observer}))
        assert observer.started_calls == 0 and emitted == []
    finally:
        database.dispose()
