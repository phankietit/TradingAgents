"""Eligible decision inputs backed by the real deterministic risk evaluator."""

from uuid import uuid4

from tests.test_risk_engine import NOW, _policy, _portfolio
from tradingagents.contracts import AssetClass, DataQualityStatus, EvidenceReference, Tradability
from tradingagents.platform.risk import RiskEngine, RiskProposal


def ready_inputs(owner_id=None):
    owner = owner_id or uuid4()
    held, instrument = uuid4(), uuid4()
    policy = _policy(owner)
    assessment = RiskEngine().evaluate(
        portfolio=_portfolio(owner, held), policy=policy,
        proposal=RiskProposal(
            instrument_id=instrument, asset_class=AssetClass.EQUITY,
            tradability=Tradability.INVESTABLE, target_weight=0.1,
            data_quality=DataQualityStatus.OK,
            position_asset_classes={held: AssetClass.EQUITY}, correlations={held: 0.2},
        ),
    )
    return {
        "owner_id": owner, "instrument_id": instrument,
        "current_weight": 0.0, "target_weight": 0.1,
        "max_allowed_weight": assessment.max_allowed_weight,
        "policy_checks": assessment.checks,
        "evidence": (EvidenceReference(
            evidence_id=uuid4(), snapshot_id=uuid4(), claim="Thesis", source_name="fixture",
            observed_at=NOW, source_at=NOW, content_hash="sha256:" + "a" * 64,
        ),),
    }
