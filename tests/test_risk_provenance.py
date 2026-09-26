"""Risk replay uses real immutable storage, owner queries and policy evaluation."""

from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from tests.test_decision_event_persistence import seed
from tests.test_decision_lifecycle import _approval
from tests.test_evaluation_outcomes import _snapshot
from tests.test_platform_persistence import _instrument, _run
from tests.test_risk_engine import NOW, _policy
from tradingagents.contracts import RunStatus
from tradingagents.platform.artifacts import ArtifactService, LocalArtifactStore
from tradingagents.platform.market_data.timeseries import TimeSeriesSnapshotService
from tradingagents.platform.persistence import PlatformRepository
from tradingagents.platform.risk import RiskEngine, RiskProposal
from tradingagents.platform.risk.provenance import replay_correlations


def setup_risk(tmp_path, *, database_url=None):
    database, original = seed(tmp_path, database_url=database_url)
    store = LocalArtifactStore(tmp_path / "risk-blobs")
    with database.session() as session:
        repo = PlatformRepository(session, artifact_store=store)
        held = _instrument().model_copy(update={"instrument_id": uuid4(), "symbol": "MSFT",
                                               "canonical_symbol": "MSFT"})
        repo.add_instrument(held)
        portfolio = repo.get_portfolio_snapshot(original.portfolio_snapshot_id, original.owner_id)
        first = portfolio.positions[0].model_copy(update={"quantity": Decimal(2),
            "market_value": Decimal(200), "weight": .2})
        second = first.model_copy(update={"instrument_id": held.instrument_id})
        portfolio = portfolio.model_copy(update={"portfolio_id": uuid4(), "positions": (first, second)})
        repo.add_portfolio_snapshot(portfolio)
        policy = _policy(original.owner_id)
        policy = policy.model_copy(update={"parameters": {**policy.parameters,
            "correlation_periods": 2, "correlation_max_age_seconds": 86400}})
        repo.add_policy(policy)
        service = TimeSeriesSnapshotService(repo, ArtifactService(store, repo))
        ids = []
        for instrument_id, prices in ((original.instrument_id, (100, 102, 108)),
                                       (held.instrument_id, (100, 106, 107))):
            _, series = _snapshot(instrument_id, prices)
            series = series.model_copy(update={"as_of": NOW, "bars": tuple(
                bar.model_copy(update={"timestamp": bar.timestamp - timedelta(days=3)})
                for bar in series.bars)})
            snapshot = service.persist(owner_id=original.owner_id, series=series,
                                       vendor="fixture", retrieved_at=NOW)
            ids.append(snapshot.snapshot_id)
        run = _run(original.instrument_id, original.owner_id).model_copy(update={
            "analysis_as_of": NOW, "snapshot_ids": (*ids, original.evidence[0].snapshot_id)})
        repo.save_run(run)
        candidate = original.model_copy(update={"decision_id": uuid4(), "run_id": run.run_id,
            "portfolio_snapshot_id": portfolio.portfolio_id, "risk_snapshot_ids": tuple(ids),
            "current_weight": .2, "target_weight": .3})
        correlations = replay_correlations(repo, candidate, portfolio, policy)
        assert correlations[held.instrument_id] == pytest.approx(-1)
        assessment = RiskEngine().evaluate(portfolio=portfolio, policy=policy, proposal=RiskProposal(
            instrument_id=original.instrument_id, asset_class=held.asset_class,
            tradability=held.tradability, target_weight=.3, data_quality=original.data_quality,
            position_asset_classes={first.instrument_id: held.asset_class, held.instrument_id: held.asset_class},
            correlations=correlations))
        candidate = candidate.model_copy(update={"policy_checks": assessment.checks,
                                                "max_allowed_weight": assessment.max_allowed_weight})
    return database, store, candidate


def test_multi_asset_risk_is_replayed_before_readiness_and_approval(tmp_path):
    database, store, candidate = setup_risk(tmp_path)
    with database.session() as session:
        repo = PlatformRepository(session, artifact_store=store)
        repo.add_decision(candidate)
        run = repo.get_run(candidate.run_id, candidate.owner_id)
        run = run.model_copy(update={"status": RunStatus.RUNNING, "started_at": NOW})
        repo.save_run(run)
        repo.save_run(run.model_copy(update={"status": RunStatus.SUCCEEDED, "completed_at": NOW}))
        repo.add_decision_event(_approval(candidate))
    database.dispose()


@pytest.mark.parametrize("mutation", [
    "missing", "duplicate", "unbound", "no_store", "foreign_owner", "forged_check",
])
def test_risk_source_bypass_is_rejected(tmp_path, mutation):
    database, store, candidate = setup_risk(tmp_path)
    if mutation == "missing":
        candidate = candidate.model_copy(update={"risk_snapshot_ids": candidate.risk_snapshot_ids[:1]})
    elif mutation == "duplicate":
        candidate = candidate.model_copy(update={"risk_snapshot_ids": candidate.risk_snapshot_ids * 2})
    elif mutation == "unbound":
        candidate = candidate.model_copy(update={"risk_snapshot_ids": (uuid4(),)})
    elif mutation == "foreign_owner":
        candidate = candidate.model_copy(update={"owner_id": uuid4()})
    elif mutation == "forged_check":
        candidate = candidate.model_copy(update={"policy_checks": tuple(
            item.model_copy(update={"observed_value": 0.0}) if item.check_id == "max_correlation" else item
            for item in candidate.policy_checks)})
    with pytest.raises(ValueError), database.session() as session:
        PlatformRepository(session, artifact_store=None if mutation == "no_store" else store).add_decision(candidate)
    database.dispose()


@pytest.mark.parametrize("mutation,match", [
    ("short_history", "insufficient"), ("stale", "stale"),
    ("missing_policy_window", "explicit policy"), ("corrupt", "hash mismatch"),
])
def test_replay_rejects_unusable_source_data(tmp_path, monkeypatch, mutation, match):
    database, store, candidate = setup_risk(tmp_path)
    with database.session() as session:
        repo = PlatformRepository(session, artifact_store=store)
        portfolio = repo.get_portfolio_snapshot(candidate.portfolio_snapshot_id, candidate.owner_id)
        check = candidate.policy_checks[0]
        policy = repo.get_policy(check.policy_id, check.policy_version, candidate.owner_id)
        if mutation == "short_history":
            policy = policy.model_copy(update={"parameters": {**policy.parameters, "correlation_periods": 5}})
        elif mutation == "stale":
            candidate = candidate.model_copy(update={"as_of": NOW + timedelta(days=2)})
        elif mutation == "missing_policy_window":
            policy = policy.model_copy(update={"parameters": {**policy.parameters, "correlation_periods": None}})
        else:
            monkeypatch.setattr(store, "get_bytes", lambda blob: b"corrupted")
        with pytest.raises(ValueError, match=match):
            replay_correlations(repo, candidate, portfolio, policy)
    database.dispose()
