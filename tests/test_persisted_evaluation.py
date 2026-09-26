from datetime import timedelta
from uuid import uuid4

import pytest

from tests.test_platform_persistence import _instrument
from tests.test_risk_engine import NOW
from tests.test_risk_provenance import setup_risk
from tradingagents.contracts import AssetClass, NormalizedTimeSeries, RunStatus
from tradingagents.contracts.runs import DecisionRunInputs
from tradingagents.platform.artifacts import ArtifactService
from tradingagents.platform.evaluation.calendar import evaluation_session_window
from tradingagents.platform.evaluation.replay import (
    EvaluationCellSelection,
    EvaluationReplayRequest,
    PersistedEvaluationService,
)
from tradingagents.platform.market_data import TimeSeriesSnapshotService
from tradingagents.platform.persistence import PlatformRepository


def setup_evaluation(tmp_path):
    database, store, seeded = setup_risk(tmp_path)
    evaluated_at = NOW + timedelta(days=7)
    with database.session() as session:
        repo = PlatformRepository(session, artifact_store=store)
        source = repo.get_snapshot(seeded.risk_snapshot_ids[0])
        original_run = repo.get_run(seeded.run_id, seeded.owner_id)
        policy = seeded.policy_checks[0]
        inputs = DecisionRunInputs(snapshots_by_analyst={"market": (source.snapshot_id,)},
            source_max_age_seconds={"market": 86400}, portfolio_snapshot_id=seeded.portfolio_snapshot_id,
            policy_id=policy.policy_id, policy_version=policy.policy_version, requested_target_weight=.3,
            risk_snapshot_ids=seeded.risk_snapshot_ids)
        run = original_run.model_copy(update={"run_id": uuid4(), "selected_analysts": ("market",),
            "snapshot_ids": inputs.snapshot_ids(), "decision_inputs": inputs})
        repo.save_run(run)
        evidence = seeded.evidence[0].model_copy(update={"snapshot_id": source.snapshot_id,
            "content_hash": source.content_hash, "source_name": source.vendor,
            "source_at": source.source_end, "observed_at": source.retrieved_at})
        decision = seeded.model_copy(update={"decision_id": uuid4(), "run_id": run.run_id, "evidence": (evidence,)})
        repo.add_decision(decision)
        run = run.model_copy(update={"status": RunStatus.RUNNING, "started_at": NOW})
        repo.save_run(run)
        repo.save_run(run.model_copy(update={"status": RunStatus.SUCCEEDED, "completed_at": NOW}))
        instrument = repo.get_instrument(decision.instrument_id)
        benchmark = _instrument().model_copy(update={"instrument_id": uuid4(), "symbol": "SPY",
            "canonical_symbol": "SPY", "asset_class": AssetClass.ETF})
        repo.add_instrument(benchmark)
        windows = evaluation_session_window(instrument=instrument, decision_at=NOW,
            holding_sessions=1, evaluated_at=evaluated_at)
        ids = []
        for item, prices in ((instrument, (100, 110)), (benchmark, (100, 102))):
            series = NormalizedTimeSeries(instrument_id=item.instrument_id, dataset="daily_prices",
                interval="1d", timezone=item.timezone, quote_currency="USD", annualization_periods=252,
                as_of=windows.session_closes[-1], bars=tuple({
                    "timestamp": timestamp, "open": price, "high": price, "low": price,
                    "close": price, "volume": 1000} for timestamp, price in zip(windows.session_closes, prices, strict=True)))
            manifest = TimeSeriesSnapshotService(repo, ArtifactService(store, repo)).persist(
                owner_id=decision.owner_id, series=series, vendor="fixture",
                retrieved_at=windows.session_closes[-1] + timedelta(minutes=1))
            ids.append(manifest.snapshot_id)
    request = EvaluationReplayRequest(owner_id=decision.owner_id, evaluated_at=evaluated_at,
        cells=(EvaluationCellSelection(decision_id=decision.decision_id,
            asset_snapshot_id=ids[0], benchmark_snapshot_id=ids[1], holding_sessions=1),))
    return database, store, request


def test_owner_receipt_reconstructs_returns_and_calendar_evidence(tmp_path):
    database, store, request = setup_evaluation(tmp_path)
    with database.session() as session:
        service = PersistedEvaluationService(ArtifactService(store, PlatformRepository(session)))
        artifact = service.create(request)
        assert service.create(request) == artifact
        receipt = service.verify(artifact.artifact_id, request.owner_id)
        assert receipt.evaluation.reproducible is True
        assert receipt.evaluation.portfolio_performance_claim is False
        assert receipt.evaluation.cells[0].raw_return == pytest.approx(.1)
        assert receipt.evaluation.cells[0].benchmark_return == pytest.approx(.02)
        assert len(receipt.calendars) == 1
        with pytest.raises(ValueError, match="unavailable"):
            service.verify(artifact.artifact_id, uuid4())
    database.dispose()


@pytest.mark.parametrize("case", ["owner", "source", "future", "duplicate"])
def test_replay_rejects_unavailable_or_ineligible_inputs(tmp_path, case):
    database, store, request = setup_evaluation(tmp_path)
    if case == "owner":
        request = request.model_copy(update={"owner_id": uuid4()})
    elif case == "source":
        request = request.model_copy(update={"cells": (request.cells[0].model_copy(update={"asset_snapshot_id": uuid4()}),)})
    elif case == "future":
        request = request.model_copy(update={"evaluated_at": NOW + timedelta(hours=1)})
    else:
        request = request.model_copy(update={"cells": request.cells * 2})
    with pytest.raises(ValueError), database.session() as session:
        PersistedEvaluationService(ArtifactService(store, PlatformRepository(session))).create(request)
    database.dispose()
