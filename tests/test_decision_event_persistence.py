"""Approval writes must preserve owner, source and lifecycle authority."""

from datetime import timedelta
from uuid import uuid4

import pytest

from tests.test_decision_lifecycle import NOW, _approval, _decision
from tests.test_platform_persistence import _instrument, _run
from tests.test_risk_engine import _policy
from tradingagents.contracts import DataQualityStatus, DecisionStatus, SnapshotManifest
from tradingagents.platform.decisions import DecisionLifecycle
from tradingagents.platform.persistence import Database, PlatformRepository, upgrade_database


def seed(tmp_path):
    url = f"sqlite:///{tmp_path / 'decisions.db'}"
    upgrade_database(url)
    database = Database(url)
    owner = uuid4()
    decision = _decision(owner)
    instrument = _instrument().model_copy(update={"instrument_id": decision.instrument_id})
    evidence = decision.evidence[0]
    run = _run(instrument.instrument_id, owner, run_id=decision.run_id).model_copy(update={
        "analysis_as_of": NOW, "snapshot_ids": (evidence.snapshot_id,),
    })
    source = SnapshotManifest(
        snapshot_id=evidence.snapshot_id, instrument_id=instrument.instrument_id,
        dataset="ohlcv.daily", vendor=evidence.source_name,
        as_of=NOW, retrieved_at=NOW, source_end=NOW,
        content_hash=evidence.content_hash, quality_status=DataQualityStatus.OK,
    )
    policy = _policy(owner).model_copy(update={"policy_id": decision.policy_checks[0].policy_id})
    with database.session() as session:
        repository = PlatformRepository(session)
        repository.add_instrument(instrument)
        repository.add_snapshot(source)
        repository.save_run(run)
        repository.add_policy(policy)
        repository.add_decision(decision)
    return database, decision


def test_approval_is_persisted_once_and_terminal_conflict_rolls_back(tmp_path):
    database, decision = seed(tmp_path)
    event = _approval(decision)
    with database.session() as session:
        repository = PlatformRepository(session)
        repository.add_decision_event(event)
        assert repository.add_decision_event(event) == event
    with database.session() as session:
        repository = PlatformRepository(session)
        history = repository.list_decision_events(decision.decision_id, decision.owner_id)
        assert len(history) == 1
        assert DecisionLifecycle().apply(decision, history) is DecisionStatus.APPROVED
        assert repository.list_decision_events(decision.decision_id, uuid4()) == ()
    conflict = event.model_copy(update={"event_id": uuid4(), "to_status": DecisionStatus.REJECTED,
                                        "occurred_at": event.occurred_at + timedelta(seconds=1)})
    with pytest.raises(ValueError), database.session() as session:
        PlatformRepository(session).add_decision_event(conflict)
    database.dispose()


def test_cross_owner_event_and_wrong_policy_are_not_written(tmp_path):
    database, decision = seed(tmp_path)
    other = uuid4()
    event = _approval(decision, owner_id=other, actor_id=other)
    with pytest.raises(ValueError, match="not found"), database.session() as session:
        PlatformRepository(session).add_decision_event(event)
    with pytest.raises(ValueError, match="does not match"), database.session() as session:
        PlatformRepository(session).add_decision_event(_approval(decision, policy_version="unreviewed"))
    with database.session() as session:
        assert PlatformRepository(session).list_decision_events(decision.decision_id, decision.owner_id) == ()
    database.dispose()
