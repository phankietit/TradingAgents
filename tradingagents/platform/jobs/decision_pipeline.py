"""Bind graph narrative to evidence and deterministic owner risk inputs."""

from types import SimpleNamespace
from uuid import uuid5

from tradingagents.contracts import DataQualityStatus, DecisionCandidate
from tradingagents.platform.analysis import DecisionCandidateFactory
from tradingagents.platform.analysis.evidence_service import EvidenceGraphService
from tradingagents.platform.risk import RiskEngine, RiskProposal
from tradingagents.platform.risk.provenance import replay_correlations
from tradingagents.portfolio import PortfolioContext, Position


def load_run_portfolio(repository, run):
    inputs = run.decision_inputs
    if inputs is None or inputs.portfolio_snapshot_id is None:
        return None
    portfolio = repository.get_portfolio_snapshot(inputs.portfolio_snapshot_id, run.owner_id)
    if portfolio is None or portfolio.as_of != run.analysis_as_of:
        raise ValueError("owner portfolio unavailable at run timestamp")
    positions = []
    for position in portfolio.positions:
        instrument = repository.get_instrument(position.instrument_id)
        if instrument is None:
            raise ValueError("portfolio instrument unavailable")
        positions.append(Position(ticker=instrument.canonical_symbol, quantity=float(position.quantity),
            average_price=float(position.average_price) if position.average_price is not None else None))
    return PortfolioContext(currency=portfolio.base_currency,
        cash=float(sum(balance.amount for balance in portfolio.cash if balance.currency == portfolio.base_currency)),
        positions=positions)


def build_run_decision(artifacts, run, result):
    repository = artifacts.repository
    inputs = run.decision_inputs
    quality = DataQualityStatus.UNAVAILABLE
    references = ()
    evidence_artifact = None
    risk = {}
    raw = result.decision_payload.model_dump(mode="json") if result.decision_payload else {}
    if inputs is not None and result.decision_payload is not None:
        narrative = result.decision_payload
        required = {narrative.thesis, *narrative.risks, *narrative.invalidation_conditions}
        allowed = {key for ids in inputs.snapshots_by_analyst.values() for key in ids}
        cited = {key for ids in result.material_claims.values() for key in ids}
        if (set(result.material_claims) == required and cited <= allowed
                and all(ids and len(ids) == len(set(ids)) for ids in result.material_claims.values())):
            service = EvidenceGraphService(artifacts)
            evidence_artifact = service.create(owner_id=run.owner_id, run_id=run.run_id,
                                               material_claims=result.material_claims)
            references = service.read(evidence_artifact.artifact_id, run.owner_id).evidence
            quality = DataQualityStatus.OK
        else:
            quality = DataQualityStatus.INVALID
    if inputs is not None and inputs.portfolio_snapshot_id is not None:
        portfolio = repository.get_portfolio_snapshot(inputs.portfolio_snapshot_id, run.owner_id)
        policy = repository.get_policy(inputs.policy_id, inputs.policy_version, run.owner_id)
        instrument = repository.get_instrument(run.instrument_id)
        if portfolio is None or portfolio.as_of != run.analysis_as_of or policy is None:
            raise ValueError("owner risk inputs unavailable at run timestamp")
        classes = {}
        for position in portfolio.positions:
            held = repository.get_instrument(position.instrument_id)
            if held is not None:
                classes[held.instrument_id] = held.asset_class
        binding = SimpleNamespace(instrument_id=run.instrument_id, owner_id=run.owner_id,
            run_id=run.run_id, as_of=run.analysis_as_of, target_weight=inputs.requested_target_weight,
            risk_snapshot_ids=inputs.risk_snapshot_ids)
        try:
            correlations = replay_correlations(repository, binding, portfolio, policy)
        except ValueError:
            correlations = {}  # Missing coverage is a blocking REVIEW check.
        assessment = RiskEngine().evaluate(portfolio=portfolio, policy=policy, proposal=RiskProposal(
            instrument_id=run.instrument_id, asset_class=instrument.asset_class,
            tradability=instrument.tradability, target_weight=inputs.requested_target_weight,
            data_quality=quality, position_asset_classes=classes, correlations=correlations,
        ))
        risk = {"current_weight": next((p.weight for p in portfolio.positions
                                        if p.instrument_id == run.instrument_id), 0.0),
                "target_weight": inputs.requested_target_weight if assessment.passed else None,
                "max_allowed_weight": assessment.max_allowed_weight,
                "policy_checks": assessment.checks}
    candidate = DecisionCandidateFactory().build(
        decision_id=uuid5(run.run_id, "decision-v1"), raw_output=raw, run_id=run.run_id,
        owner_id=run.owner_id, instrument_id=run.instrument_id, as_of=run.analysis_as_of,
        evidence=references, data_quality=quality, **risk,
    )
    if inputs is not None:
        candidate = DecisionCandidate.model_validate({**candidate.model_dump(),
            "portfolio_snapshot_id": inputs.portfolio_snapshot_id,
            "risk_snapshot_ids": inputs.risk_snapshot_ids})
    return candidate, evidence_artifact
