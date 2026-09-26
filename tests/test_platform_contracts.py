"""Versioned platform contracts enforce product and safety boundaries."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from tradingagents.contracts import (
    CONTRACT_REGISTRY,
    AssetClass,
    DataQualityStatus,
    DecisionCandidate,
    DecisionRating,
    DecisionStatus,
    InstrumentContract,
    PolicyCheck,
    PolicyResult,
    PortfolioSnapshot,
    RunManifest,
    RunStatus,
    SnapshotManifest,
    Tradability,
)

NOW = datetime(2026, 9, 23, 8, 0, tzinfo=UTC)


def _instrument(**overrides):
    values = {
        "instrument_id": uuid4(),
        "symbol": "AAPL",
        "canonical_symbol": "AAPL",
        "display_name": "Apple Inc.",
        "asset_class": AssetClass.EQUITY,
        "tradability": Tradability.INVESTABLE,
        "venue": "NASDAQ",
        "quote_currency": "USD",
        "timezone": "America/New_York",
        "session_calendar": "XNYS",
        "benchmark_symbol": "SPY",
    }
    values.update(overrides)
    return InstrumentContract.model_validate(values)


@pytest.mark.unit
def test_contracts_are_versioned_strict_and_immutable():
    instrument = _instrument()
    assert instrument.schema_version == "1.0"
    with pytest.raises(ValidationError, match="extra_forbidden"):
        InstrumentContract.model_validate({**instrument.model_dump(), "unknown": True})
    with pytest.raises(ValidationError, match="frozen_instance"):
        instrument.symbol = "MSFT"


@pytest.mark.unit
def test_reference_future_cannot_be_marked_investable():
    with pytest.raises(ValidationError, match="reference_only"):
        _instrument(
            symbol="NQ=F",
            canonical_symbol="NQ=F",
            display_name="Nasdaq-100 E-mini reference",
            asset_class=AssetClass.REFERENCE_FUTURE,
            tradability=Tradability.INVESTABLE,
            venue="CME",
            session_calendar="CME_Equity",
        )


@pytest.mark.unit
def test_crypto_requires_utc():
    with pytest.raises(ValidationError, match="UTC"):
        _instrument(
            symbol="BTC-USD",
            canonical_symbol="BTC-USD",
            display_name="Bitcoin",
            asset_class=AssetClass.CRYPTO,
            timezone="America/New_York",
            venue="aggregate",
            session_calendar="24/7",
        )


def _policy_check(result=PolicyResult.PASS, blocking=True):
    return PolicyCheck(
        check_id="max_weight",
        policy_id=uuid4(),
        policy_version="1",
        result=result,
        blocking=blocking,
        reason="Within configured maximum weight",
        observed_value=0.05,
        limit_value=0.08,
    )


def _decision(**overrides):
    values = {
        "decision_id": uuid4(),
        "run_id": uuid4(),
        "owner_id": uuid4(),
        "instrument_id": uuid4(),
        "as_of": NOW,
        "status": DecisionStatus.READY_FOR_APPROVAL,
        "rating": DecisionRating.OVERWEIGHT,
        "confidence": 0.72,
        "thesis": "Earnings revisions and relative strength remain positive.",
        "risks": ("Valuation compression",),
        "invalidation_conditions": ("Relative strength breaks down",),
        "evidence": (),
        "data_quality": DataQualityStatus.OK,
        "current_weight": 0.03,
        "target_weight": 0.05,
        "max_allowed_weight": 0.08,
        "policy_checks": (_policy_check(),),
        "requires_human_approval": True,
    }
    values.update(overrides)
    return DecisionCandidate.model_validate(values)


@pytest.mark.unit
def test_legacy_review_with_narrative_rating_remains_readable():
    decision = _decision(status=DecisionStatus.REVIEW)
    assert decision.status is DecisionStatus.REVIEW


@pytest.mark.unit
def test_decision_always_requires_human_approval():
    with pytest.raises(ValidationError, match="literal_error"):
        _decision(requires_human_approval=False)


@pytest.mark.unit
def test_decision_rejects_target_above_deterministic_limit():
    with pytest.raises(ValidationError, match="max_allowed_weight"):
        _decision(target_weight=0.09, max_allowed_weight=0.08)


@pytest.mark.unit
def test_blocking_policy_failure_cannot_be_approval_ready():
    with pytest.raises(ValidationError, match="blocking policy"):
        _decision(policy_checks=(_policy_check(PolicyResult.FAIL),))


@pytest.mark.unit
def test_naive_as_of_datetime_is_rejected():
    with pytest.raises(ValidationError, match="timezone_aware"):
        _decision(as_of=datetime(2026, 9, 23, 8, 0))


@pytest.mark.unit
def test_contract_registry_exports_json_schemas():
    schemas = {name: model.model_json_schema() for name, model in CONTRACT_REGISTRY.items()}
    assert set(schemas) == set(CONTRACT_REGISTRY)
    assert all(schema.get("additionalProperties") is False for schema in schemas.values())
    assert schemas["DecisionCandidate"]["properties"]["schema_version"]["default"] == "1.0"


@pytest.mark.unit
def test_decision_round_trip_is_lossless():
    decision = _decision()
    restored = DecisionCandidate.model_validate_json(decision.model_dump_json())
    assert restored == decision


@pytest.mark.unit
def test_snapshot_rejects_future_leaking_source_window():
    with pytest.raises(ValidationError, match="must not exceed as_of"):
        SnapshotManifest(
            snapshot_id=uuid4(),
            instrument_id=uuid4(),
            dataset="ohlcv.daily",
            vendor="example",
            as_of=NOW,
            retrieved_at=NOW + timedelta(minutes=1),
            source_start=NOW - timedelta(days=30),
            source_end=NOW + timedelta(days=1),
            content_hash="sha256:" + "a" * 64,
            quality_status=DataQualityStatus.OK,
        )


@pytest.mark.unit
def test_terminal_run_requires_complete_lifecycle_evidence():
    with pytest.raises(ValidationError, match="completed_at"):
        RunManifest(
            run_id=uuid4(),
            owner_id=uuid4(),
            instrument_id=uuid4(),
            analysis_as_of=NOW,
            status=RunStatus.SUCCEEDED,
            created_at=NOW,
            started_at=NOW,
            selected_analysts=("market",),
            llm_provider="openai",
            quick_model="quick",
            deep_model="deep",
            config_hash="sha256:" + "b" * 64,
            prompt_version="1",
        )


@pytest.mark.unit
def test_portfolio_is_long_only_and_positions_are_unique():
    instrument_id = uuid4()
    position = {
        "instrument_id": instrument_id,
        "quantity": Decimal("1"),
        "market_price": Decimal("100"),
        "market_value": Decimal("100"),
        "weight": 0.5,
    }
    common = {
        "portfolio_id": uuid4(),
        "owner_id": uuid4(),
        "as_of": NOW,
        "base_currency": "USD",
        "cash": ({"currency": "USD", "amount": Decimal("100")},),
        "net_asset_value": Decimal("200"),
        "content_hash": "sha256:" + "c" * 64,
    }

    with pytest.raises(ValidationError, match="unique instrument_id"):
        PortfolioSnapshot.model_validate({**common, "positions": (position, position)})

    with pytest.raises(ValidationError, match="greater_than_equal"):
        PortfolioSnapshot.model_validate(
            {**common, "positions": ({**position, "quantity": Decimal("-1")},)}
        )
