"""Explicit synthetic local web QA server; never opens an existing owner database.

Run: python -m scripts.web_fixture --synthetic-local-only
Login: fixture@example.com / synthetic-local-web-password
No worker is started and no vendor/model is called. Not an investment dataset.
"""

import argparse
import math
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

import uvicorn

from tradingagents._compat import UTC
from tradingagents.contracts import (
    DecisionCandidate,
    LedgerTransaction,
    PolicyContract,
    PriceInterval,
    RunManifest,
)
from tradingagents.platform.api import ApiSettings, create_app
from tradingagents.platform.artifacts import ArtifactService, LocalArtifactStore
from tradingagents.platform.auth import OwnerAuth
from tradingagents.platform.instruments import InstrumentMaster
from tradingagents.platform.market_data import TimeSeriesSnapshotService, normalize_time_series
from tradingagents.platform.persistence import Database, PlatformRepository, upgrade_database
from tradingagents.platform.portfolio.service import PortfolioLedgerService


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthetic-local-only", action="store_true", required=True)
    parser.parse_args()
    cache = Path(__file__).resolve().parents[1] / ".cache"
    cache.mkdir(exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="web-fixture-", dir=cache))
    url = f"sqlite:///{directory / 'fixture.db'}"
    upgrade_database(url)
    now = datetime.now(UTC).replace(microsecond=0)
    database = Database(url)
    with database.session() as session:
        owner = OwnerAuth(session).bootstrap_owner("fixture@example.com", "synthetic-local-web-password", now=now)
        repository = PlatformRepository(session)
        master = InstrumentMaster(repository)
        master.bootstrap()
        instrument = next(item for item in master.list() if item.canonical_symbol == "AAPL")
        bars = []
        for index in range(60):
            close = round(180 + index * .25 + math.sin(index / 4) * 4, 2)
            bars.append({"timestamp": now - timedelta(days=60-index), "open": close - .3,
                         "high": close + 1, "low": close - 1, "close": close,
                         "volume": 1_000_000 + index * 1000})
        series = normalize_time_series(instrument=instrument, dataset="ohlcv.daily",
            interval=PriceInterval.ONE_DAY, as_of=now, annualization_periods=252, bars=bars)
        artifacts = ArtifactService(LocalArtifactStore(directory / "artifacts"), repository)
        source = TimeSeriesSnapshotService(repository, artifacts).persist(
            owner_id=owner.owner_id, series=series, vendor="SYNTHETIC LOCAL QA — NOT MARKET DATA", retrieved_at=now)
        ledger_id = uuid4()
        repository.add_ledger_transaction(LedgerTransaction(transaction_id=uuid4(), ledger_id=ledger_id,
            owner_id=owner.owner_id, occurred_at=now - timedelta(days=62), transaction_type="cash_deposit",
            currency="USD", cash_amount="10000", external_reference="SYNTHETIC-QA-DEPOSIT"))
        repository.add_ledger_transaction(LedgerTransaction(transaction_id=uuid4(), ledger_id=ledger_id,
            owner_id=owner.owner_id, occurred_at=now - timedelta(days=61), transaction_type="buy",
            currency="USD", instrument_id=instrument.instrument_id, quantity="10", unit_price="180",
            external_reference="SYNTHETIC-QA-HISTORICAL-ENTRY-NOT-AN-ORDER"))
        PortfolioLedgerService(artifacts).replay(ledger_id=ledger_id, owner_id=owner.owner_id,
            base_currency="USD", price_snapshot_ids={instrument.instrument_id: source.snapshot_id},
            as_of=now, max_price_age=timedelta(days=2))
        repository.add_policy(PolicyContract(policy_id=uuid4(), owner_id=owner.owner_id,
            name="SYNTHETIC QA POLICY — NOT OWNER LIMITS", policy_version="fixture-1", asset_class="equity",
            effective_at=now, parameters={"max_position_weight": .3, "max_asset_class_weight": .7,
                "max_gross_exposure": .8, "max_turnover": .2, "max_correlation": .8, "min_cash_weight": .2,
                "correlation_periods": 20, "correlation_max_age_seconds": 172800}))
        # Deliberately REVIEW with no risk approval. This is seeded QA content,
        # not a worker/model result and cannot be approved.
        run = RunManifest(run_id=uuid4(), owner_id=owner.owner_id, instrument_id=instrument.instrument_id,
            analysis_as_of=now, status="queued", created_at=now, selected_analysts=("market",),
            llm_provider="synthetic-no-provider", quick_model="fixture", deep_model="fixture",
            config_hash="sha256:" + "0" * 64, prompt_version="fixture", snapshot_ids=(source.snapshot_id,))
        repository.save_run(run)
        repository.add_decision(DecisionCandidate(decision_id=uuid4(), run_id=run.run_id,
            owner_id=owner.owner_id, instrument_id=instrument.instrument_id, as_of=now,
            status="review", rating="Review", confidence=0,
            thesis="SYNTHETIC LOCAL QA — seeded review candidate, not model output or investment advice.",
            risks=("Synthetic fixture has no live-provider verification.",),
            invalidation_conditions=("Do not use this fixture to make an investment decision.",),
            evidence=(), data_quality="UNAVAILABLE", policy_checks=()))
    database.dispose()
    print("Synthetic-only API on 127.0.0.1:8000; no worker or provider calls.")
    uvicorn.run(create_app(ApiSettings(database_url=url, artifact_root=directory / "artifacts",
        allowed_origin="http://127.0.0.1:5173", secure_cookies=False)),
        host="127.0.0.1", port=8000, access_log=False)


if __name__ == "__main__":
    main()
