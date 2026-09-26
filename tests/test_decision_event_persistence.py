"""Approval writes must preserve owner, source and lifecycle authority."""

from datetime import timedelta
from uuid import uuid4

import pytest

from tests.test_decision_lifecycle import NOW, _approval, _decision
from tests.test_platform_persistence import _instrument, _run
from tests.test_risk_engine import _policy, _portfolio
from tradingagents.contracts import DataQualityStatus, DecisionStatus, SnapshotManifest
from tradingagents.platform.decisions import DecisionLifecycle
from tradingagents.platform.persistence import Database, PlatformRepository, upgrade_database
from tradingagents.platform.risk import RiskEngine, RiskProposal


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
    portfolio = _portfolio(owner, instrument.instrument_id)
    assessment = RiskEngine().evaluate(
        portfolio=portfolio, policy=policy, proposal=RiskProposal(
            instrument_id=instrument.instrument_id, asset_class=instrument.asset_class,
            tradability=instrument.tradability, target_weight=.45,
            data_quality=DataQualityStatus.OK,
            position_asset_classes={instrument.instrument_id: instrument.asset_class},
        ),
    )
    decision = decision.model_copy(update={
        "portfolio_snapshot_id": portfolio.portfolio_id, "current_weight": .4,
        "target_weight": .45, "max_allowed_weight": assessment.max_allowed_weight,
        "policy_checks": assessment.checks,
    })
    with database.session() as session:
        repository = PlatformRepository(session)
        repository.add_instrument(instrument)
        repository.add_snapshot(source)
        repository.save_run(run)
        repository.add_policy(policy)
        repository.add_portfolio_snapshot(portfolio)
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


@pytest.mark.parametrize("mutation", [
    {"portfolio_snapshot_id": None},
    {"portfolio_snapshot_id": uuid4()},
    {"current_weight": .1},
    {"target_weight": .49},
    {"max_allowed_weight": .49},
])
def test_ready_write_rejects_unbound_or_forged_risk_inputs(tmp_path, mutation):
    database, decision = seed(tmp_path)
    forged = decision.model_copy(update={"decision_id": uuid4(), **mutation})
    with pytest.raises(ValueError), database.session() as session:
        PlatformRepository(session).add_decision(forged)
    with database.session() as session:
        assert PlatformRepository(session).get_decision(forged.decision_id, decision.owner_id) is None
    database.dispose()


def test_ready_write_rejects_forged_pass_observations(tmp_path):
    database, decision = seed(tmp_path)
    checks = tuple(check.model_copy(update={"observed_value": 0.0})
                   if check.check_id == "max_turnover" else check for check in decision.policy_checks)
    forged = decision.model_copy(update={"decision_id": uuid4(), "policy_checks": checks})
    with pytest.raises(ValueError, match="persisted inputs"), database.session() as session:
        PlatformRepository(session).add_decision(forged)
    database.dispose()
