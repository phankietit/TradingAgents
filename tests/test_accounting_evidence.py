"""Owner-scoped durable cumulative evidence, not continuation authority."""

from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import select

from tests.test_durable_jobs import _database
from tests.test_risk_engine import NOW
from tradingagents.contracts import RunEventType
from tradingagents.platform.analysis.accounting import (
    AccountingEvidenceError,
    load_accounting_evidence,
    recheck_accounting_evidence,
)
from tradingagents.platform.analysis.observer import ResearchObserver
from tradingagents.platform.events import RunEventStore
from tradingagents.platform.persistence import PlatformRepository
from tradingagents.platform.persistence.models import RunEventRow


def receipt(*, finish=True, calls=1):
    events = []
    observer = ResearchObserver(check_cancelled=lambda: None, emit=lambda *args: events.append(args), clock=lambda: 0)
    for _ in range(calls):
        key = uuid4()
        observer.on_chat_model_start({}, [], run_id=key)
        if finish:
            observer.on_llm_end(SimpleNamespace(generations=[[SimpleNamespace(message=SimpleNamespace(
                usage_metadata={"input_tokens": 10, "output_tokens": 5, "total_tokens": 15}))]]), run_id=key)
    return [deepcopy(payload) for _, payload in events]


def append(session, owner, run, attempt, payloads):
    store = RunEventStore(session)
    store.append(owner_id=owner, run_id=run.run_id, event_type=RunEventType.RESEARCH_EXECUTION_STARTED,
                 occurred_at=NOW, payload={"attempt": attempt})
    for payload in payloads:
        store.append(owner_id=owner, run_id=run.run_id, event_type=RunEventType.MODEL_USAGE,
                     occurred_at=NOW, payload={**payload, "attempt": attempt})


def test_reopened_attempts_use_latest_cumulative_not_sum_every_receipt(tmp_path):
    database, owner, run = _database(tmp_path)
    try:
        with database.session() as session:
            append(session, owner, run, 1, receipt(calls=2))
            append(session, owner, run, 2, receipt(finish=False))
        with database.session() as session:
            result = load_accounting_evidence(session=session, owner_id=owner, run_id=run.run_id)
            assert result.evidence_status == "PASS" and result.attempts == (1, 2)
            assert result.owner_id == owner and result.run_id == run.run_id
            assert result.config_hash == run.config_hash
            assert result.original_wall_seconds == 1800 and result.original_model_calls == 128
            assert result.started_calls == 3 and result.completed_calls == 2
            assert result.unreported_started_calls == 1
            assert result.reported_input_tokens == 20 and result.reported_total_tokens == 30
            assert result.high_water_sequence == 7 and result.exact_elapsed_known is False
            assert result.elapsed_lower_bound == 0
            # Default object repr contains an arbitrary hex address, which may
            # contain digits matching token counts. Verify field suppression,
            # not accidental substrings of that unrelated address.
            assert repr(result) == object.__repr__(result)
            assert str(owner) not in repr(result) and str(run.run_id) not in repr(result)
            assert run.config_hash not in repr(result)
            assert len(session.scalars(select(RunEventRow)).all()) == 7
    finally:
        database.dispose()


@pytest.mark.parametrize("bound", [True, 0, -1, 1.0, "1", 100001, 999])
def test_receipt_prefix_rejects_invalid_or_unrecorded_bound(tmp_path, bound):
    database, owner, run = _database(tmp_path)
    try:
        with database.session() as session:
            append(session, owner, run, 1, receipt())
        with database.session() as session, pytest.raises(AccountingEvidenceError):
            load_accounting_evidence(session=session, owner_id=owner, run_id=run.run_id, through_sequence=bound)
    finally:
        database.dispose()


def test_old_receipt_prefix_does_not_replace_latest_consent_accounting(tmp_path):
    database, owner, run = _database(tmp_path)
    try:
        with database.session() as session:
            append(session, owner, run, 1, receipt())
            old = load_accounting_evidence(session=session, owner_id=owner, run_id=run.run_id)
            append(session, owner, run, 2, receipt(finish=False))
        with database.session() as session:
            prefix = load_accounting_evidence(session=session, owner_id=owner, run_id=run.run_id,
                through_sequence=old.high_water_sequence)
            assert prefix == old
            latest = load_accounting_evidence(session=session, owner_id=owner, run_id=run.run_id)
            assert latest.attempts == (1, 2) and latest.started_calls == 2
            with pytest.raises(AccountingEvidenceError):
                recheck_accounting_evidence(session=session, owner_id=owner, run_id=run.run_id, expected=prefix)
    finally:
        database.dispose()


@pytest.mark.parametrize("kind", ["empty", "marker", "legacy"])
def test_missing_or_legacy_evidence_is_not_zero_cost(tmp_path, kind):
    database, owner, run = _database(tmp_path)
    try:
        if kind != "empty":
            with database.session() as session:
                payloads = [] if kind == "marker" else [{"usage": receipt()[-1]["usage"]}]
                append(session, owner, run, 1, payloads)
        with database.session() as session:
            result = load_accounting_evidence(session=session, owner_id=owner, run_id=run.run_id)
            assert result.evidence_status == "UNVERIFIED"
            assert result.owner_id == owner and result.run_id == run.run_id
            assert result.started_calls is None and result.reported_total_tokens is None
            assert result.elapsed_lower_bound is None and result.exact_elapsed_known is False
    finally:
        database.dispose()


@pytest.mark.parametrize("kind", ["unchanged", "new_event", "owner", "run", "counter", "limits", "type"])
def test_accounting_recheck_binds_identity_and_full_observation(tmp_path, kind):
    database, owner, run = _database(tmp_path)
    try:
        with database.session() as session:
            append(session, owner, run, 1, receipt())
            other = run.model_copy(update={"run_id": uuid4()})
            PlatformRepository(session).save_run(other)
            append(session, owner, other, 1, receipt())
        with database.session() as session:
            evidence = load_accounting_evidence(session=session, owner_id=owner, run_id=run.run_id)
        if kind == "new_event":
            with database.session() as session:
                RunEventStore(session).append(owner_id=owner, run_id=run.run_id,
                    event_type=RunEventType.STAGE_STARTED, occurred_at=NOW, payload={"stage": "Market Analyst"})
        elif kind == "counter":
            evidence = replace(evidence, reported_total_tokens=0)
        elif kind == "limits":
            evidence = replace(evidence, original_wall_seconds=3600)
        elif kind == "type":
            evidence = SimpleNamespace(**evidence.__dict__)
        with database.session() as session:
            kwargs = {"session": session, "owner_id": uuid4() if kind == "owner" else owner,
                      "run_id": other.run_id if kind == "run" else run.run_id, "expected": evidence}
            if kind == "unchanged":
                assert recheck_accounting_evidence(**kwargs) is None  # Not an authorization token.
                with pytest.raises(FrozenInstanceError):
                    evidence.original_wall_seconds = 3600
            else:
                with pytest.raises(AccountingEvidenceError, match="^accounting evidence requires review$"):
                    recheck_accounting_evidence(**kwargs)
    finally:
        database.dispose()


@pytest.mark.parametrize("mutation", ["owner", "limits", "bool", "regress", "tokens", "cost",
    "extra", "scope", "elapsed", "status", "missing_marker", "gap", "bound"])
def test_malformed_identity_or_accounting_fails_fixed(tmp_path, monkeypatch, mutation):
    database, owner, run = _database(tmp_path)
    try:
        payloads = receipt()
        if mutation == "limits":
            payloads[-1]["execution_limits"]["model_calls"] = 127
        elif mutation == "bool":
            payloads[-1]["usage"]["started_model_calls"] = True
        elif mutation == "regress":
            payloads.append(deepcopy(payloads[0]))
        elif mutation == "tokens":
            payloads[-1]["usage"]["total_tokens"] = 999
        elif mutation == "cost":
            payloads[-1]["usage"]["cost"] = 0
        elif mutation == "extra":
            payloads[-1]["credentials"] = "PRIVATE_NEVER_ECHO"
        elif mutation == "scope":
            payloads[-1]["usage"]["model_call_scope"] = "provider_requests"
        elif mutation == "elapsed":
            payloads[-1]["elapsed_seconds"] = -1
        elif mutation == "status":
            payloads[0]["usage"]["status"] = "reported"
        elif mutation == "bound":
            monkeypatch.setattr("tradingagents.platform.analysis.accounting.MAX_ACCOUNTING_EVENTS", 1)
        with database.session() as session:
            append(session, owner, run, 1, payloads)
            if mutation in {"gap", "missing_marker"}:
                row = session.scalar(select(RunEventRow).where(RunEventRow.sequence == 1))
                if mutation == "gap":
                    session.delete(row)  # Disposable fixture only.
                else:
                    row.event_type = RunEventType.RUN_STARTED.value
        with database.session() as session:
            with pytest.raises(AccountingEvidenceError) as raised:
                load_accounting_evidence(session=session, owner_id=uuid4() if mutation == "owner" else owner,
                                         run_id=run.run_id)
            assert str(raised.value) == "accounting evidence requires review"
            assert raised.value.__cause__ is None
    finally:
        database.dispose()


def test_full_prefix_pagination_and_no_double_count(tmp_path):
    database, owner, run = _database(tmp_path)
    try:
        with database.session() as session:
            append(session, owner, run, 1, receipt())
            store = RunEventStore(session)
            for _ in range(501):
                store.append(owner_id=owner, run_id=run.run_id, event_type=RunEventType.STAGE_STARTED,
                             occurred_at=NOW, payload={"stage": "Market Analyst"})
        with database.session() as session:
            result = load_accounting_evidence(session=session, owner_id=owner, run_id=run.run_id)
            assert result.high_water_sequence == 504 and result.reported_total_tokens == 15
    finally:
        database.dispose()


@pytest.mark.parametrize("kind", ["tokens_without_usage", "tokens_without_new_usage", "elapsed_overflow"])
def test_impossible_accounting_totals_reject_without_mutation(tmp_path, kind):
    database, owner, run = _database(tmp_path)
    try:
        payloads = receipt()
        if kind == "tokens_without_usage":
            payloads = payloads[:1]
            payloads[0]["usage"].update(input_tokens=10, output_tokens=5, total_tokens=15)
        elif kind == "tokens_without_new_usage":
            extra = deepcopy(payloads[-1])
            extra["usage"].update(input_tokens=20, output_tokens=10, total_tokens=30)
            payloads.append(extra)
        else:
            for payload in payloads:
                payload["elapsed_seconds"] = 1e308
        with database.session() as session:
            append(session, owner, run, 1, payloads)
            if kind == "elapsed_overflow":
                append(session, owner, run, 2, payloads)
        with database.session() as session:
            before = [(row.sequence, deepcopy(row.payload)) for row in session.scalars(
                select(RunEventRow).order_by(RunEventRow.sequence)).all()]
            with pytest.raises(AccountingEvidenceError, match="^accounting evidence requires review$"):
                load_accounting_evidence(session=session, owner_id=owner, run_id=run.run_id)
            after = [(row.sequence, row.payload) for row in session.scalars(
                select(RunEventRow).order_by(RunEventRow.sequence)).all()]
            assert before == after
    finally:
        database.dispose()


@pytest.mark.parametrize("kind", ["all_stopped", "partial", "after_stop", "duplicate_stop", "false_stop"])
def test_local_elapsed_bound_requires_every_attempt_stop(tmp_path, kind):
    database, owner, run = _database(tmp_path)
    try:
        first = receipt()
        stop = {**deepcopy(first[-1]), "elapsed_seconds": 12, "execution_stopped": True}
        first.append(stop)
        if kind == "after_stop":
            first.append({**deepcopy(first[-1]), "execution_stopped": True, "elapsed_seconds": 13})
            first[-1].pop("execution_stopped")
        elif kind == "duplicate_stop":
            first.append(deepcopy(stop))
        elif kind == "false_stop":
            first[-1]["execution_stopped"] = False
        second = receipt(finish=False)
        if kind == "all_stopped":
            second.append({**deepcopy(second[-1]), "elapsed_seconds": 13, "execution_stopped": True})
        with database.session() as session:
            append(session, owner, run, 1, first)
            append(session, owner, run, 2, second)
        with database.session() as session:
            if kind in {"after_stop", "duplicate_stop", "false_stop"}:
                with pytest.raises(AccountingEvidenceError):
                    load_accounting_evidence(session=session, owner_id=owner, run_id=run.run_id)
            else:
                evidence = load_accounting_evidence(session=session, owner_id=owner, run_id=run.run_id)
                assert evidence.evidence_status == "PASS" and evidence.exact_elapsed_known is False
                assert evidence.elapsed_upper_bound == (25 if kind == "all_stopped" else None)
                assert evidence.reported_total_tokens == 15 and evidence.unreported_started_calls == 1
    finally:
        database.dispose()
