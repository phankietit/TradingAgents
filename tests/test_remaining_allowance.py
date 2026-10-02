"""Disposable DB allowance arithmetic; no consent, model or private history."""

from copy import deepcopy
from dataclasses import FrozenInstanceError
from uuid import uuid4

import pytest
from sqlalchemy import select

from tests.test_accounting_evidence import append, receipt
from tests.test_durable_jobs import _database
from tradingagents.contracts.runs import DecisionRunInputs, ResearchExecutionLimits
from tradingagents.platform.analysis.accounting import AccountingEvidenceError
from tradingagents.platform.analysis.allowance import load_remaining_allowance
from tradingagents.platform.persistence import PlatformRepository
from tradingagents.platform.persistence.models import RunEventRow


@pytest.mark.parametrize("kind", ["empty", "legacy", "unclosed", "bounded", "failed_reservations",
                                 "time_exhausted", "overrun", "unknown_usage", "multi_attempt",
                                 "exhausted_unclosed", "multi_exhausted"])
def test_original_allowance_debits_all_starts_and_preserves_unknown(tmp_path, kind):
    database, owner, original = _database(tmp_path)
    try:
        limits = ResearchExecutionLimits(wall_seconds=60, model_calls=3)
        snapshot_id = uuid4()
        run = original.model_copy(update={"run_id": uuid4(), "execution_limits": limits,
            "snapshot_ids": (snapshot_id,), "decision_inputs": DecisionRunInputs(
                snapshots_by_analyst={"market": (snapshot_id,)}, source_max_age_seconds={"market": 0})})
        with database.session() as session:
            PlatformRepository(session).save_run(run)
            if kind != "empty":
                payloads = receipt(finish=kind not in {"failed_reservations", "unknown_usage"},
                                   calls=3 if kind == "failed_reservations" else 1)
                elapsed = 61 if kind == "overrun" else 60 if kind in {"time_exhausted", "exhausted_unclosed"} else 10
                for payload in payloads:
                    payload["execution_limits"] = limits.model_dump(mode="json")
                    payload["elapsed_seconds"] = elapsed
                if kind == "legacy":
                    payloads = [{"usage": payloads[-1]["usage"]}]
                elif kind not in {"unclosed", "exhausted_unclosed"}:
                    payloads.append({**deepcopy(payloads[-1]), "execution_stopped": True})
                append(session, owner, run, 1, payloads)
                if kind in {"multi_attempt", "multi_exhausted"}:
                    append(session, owner, run, 2, payloads)
                if kind == "multi_exhausted":
                    append(session, owner, run, 3, payloads)
        with database.session() as session:
            before = [(row.run_id, row.sequence, deepcopy(row.payload)) for row in session.scalars(
                select(RunEventRow).order_by(RunEventRow.run_id, RunEventRow.sequence)).all()]
            observation = load_remaining_allowance(session=session, owner_id=owner, run_id=run.run_id)
            assert observation.accounting.original_wall_seconds == 60
            assert observation.accounting.original_model_calls == 3
            if kind in {"empty", "legacy"}:
                assert observation.assessment_status == "UNVERIFIED"
                assert observation.reason == "accounting_unavailable"
                assert observation.remaining_wall_seconds is None and observation.remaining_model_calls is None
            elif kind == "unclosed":
                assert observation.assessment_status == "UNVERIFIED"
                assert observation.reason == "elapsed_upper_bound_unavailable"
                assert observation.remaining_wall_seconds is None and observation.remaining_model_calls == 2
            elif kind in {"failed_reservations", "time_exhausted", "overrun", "exhausted_unclosed", "multi_exhausted"}:
                assert observation.assessment_status == "BLOCKED"
                assert observation.reason == "original_allowance_exhausted"
                if kind in {"failed_reservations", "multi_exhausted"}:
                    assert observation.remaining_model_calls == 0
                elif kind == "exhausted_unclosed":
                    assert observation.remaining_wall_seconds is None
                else:
                    assert observation.remaining_wall_seconds == 0
            else:
                assert observation.assessment_status == "PASS" and observation.reason == "bounded_arithmetic_only"
                assert observation.remaining_wall_seconds == (40 if kind == "multi_attempt" else 50)
                assert observation.remaining_model_calls == (1 if kind == "multi_attempt" else 2)
            if kind == "unknown_usage":
                assert observation.accounting.unreported_started_calls == 1
                assert observation.accounting.reported_total_tokens == 0  # Reported tokens, not zero incurred usage/cost.
            assert observation.accounting.exact_elapsed_known is False
            assert repr(observation) == object.__repr__(observation)
            with pytest.raises(FrozenInstanceError):
                observation.remaining_model_calls = 3
            with pytest.raises(AccountingEvidenceError):
                load_remaining_allowance(session=session, owner_id=uuid4(), run_id=run.run_id)
            after = [(row.run_id, row.sequence, row.payload) for row in session.scalars(
                select(RunEventRow).order_by(RunEventRow.run_id, RunEventRow.sequence)).all()]
            assert before == after
            assert PlatformRepository(session).get_run(original.run_id, owner) == original
    finally:
        database.dispose()
