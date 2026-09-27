"""Disposable PostgreSQL gates; TEST_POSTGRES_URL must be a test-only database."""

import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import inspect

from tests.test_decision_event_persistence import seed
from tests.test_decision_lifecycle import _approval
from tests.test_persisted_evaluation import setup_evaluation
from tests.test_platform_persistence import NOW, _instrument
from tests.test_portfolio_valuation_service import setup_valuation
from tradingagents.contracts import DecisionStatus
from tradingagents.platform.artifacts import ArtifactService
from tradingagents.platform.auth import OwnerAuth
from tradingagents.platform.evaluation.replay import PersistedEvaluationService
from tradingagents.platform.persistence import (
    Database,
    PlatformRepository,
    downgrade_database,
    upgrade_database,
)
from tradingagents.platform.persistence.models import Base, DecisionRow
from tradingagents.platform.portfolio.evidence import load_valuation_evidence
from tradingagents.platform.portfolio.service import PortfolioLedgerService

pytestmark = pytest.mark.integration


@pytest.fixture
def postgres_url():
    url = os.environ.get("TEST_POSTGRES_URL")
    if not url:
        pytest.skip("TEST_POSTGRES_URL is required for the PostgreSQL integration gate")
    upgrade_database(url)
    try:
        yield url
    finally:
        downgrade_database(url)


def test_migration_schema_parity_and_rollback(postgres_url):
    database = Database(postgres_url)
    try:
        with database.engine.connect() as connection:
            assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []
        downgrade_database(postgres_url)
        assert set(inspect(database.engine).get_table_names()) <= {"alembic_version"}
        upgrade_database(postgres_url)
    finally:
        database.dispose()


def test_concurrent_watchlist_put_and_owner_isolation(postgres_url):
    database = Database(postgres_url)
    instrument = _instrument()
    with database.session() as session:
        owner = OwnerAuth(session).bootstrap_owner("watchlist@example.com", "synthetic-qa-password")
        PlatformRepository(session).add_instrument(instrument)
    barrier = Barrier(2)

    def save(_):
        barrier.wait(timeout=10)
        with database.session() as session:
            OwnerAuth(session).lock_owner(owner.owner_id)
            PlatformRepository(session).add_watchlist_entry(owner.owner_id, instrument.instrument_id, now=NOW)

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(save, range(2)))
        with database.session() as session:
            repository = PlatformRepository(session)
            assert repository.list_watchlist(owner.owner_id) == (instrument,)
            assert repository.list_watchlist(uuid4()) == ()
            repository.remove_watchlist_entry(uuid4(), instrument.instrument_id)
            assert repository.list_watchlist(owner.owner_id) == (instrument,)
            repository.remove_watchlist_entry(owner.owner_id, instrument.instrument_id)
        with database.session() as session:
            assert PlatformRepository(session).list_watchlist(owner.owner_id) == ()
    finally:
        database.dispose()


@pytest.mark.parametrize("same_event", [True, False])
def test_concurrent_owner_approval_is_idempotent_or_conflicts(tmp_path, postgres_url, same_event):
    database, decision = seed(tmp_path, database_url=postgres_url)
    first = _approval(decision)
    second = first if same_event else first.model_copy(update={
        "event_id": uuid4(), "to_status": DecisionStatus.REJECTED,
    })
    barrier = Barrier(2)

    def write(event):
        barrier.wait(timeout=10)
        try:
            with database.session() as session:
                PlatformRepository(session).add_decision_event(event)
            return "committed"
        except ValueError:
            return "conflict"

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(write, (first, second)))
        assert results.count("committed") == (2 if same_event else 1)
        with database.session() as session:
            repo = PlatformRepository(session)
            history = repo.list_decision_events(decision.decision_id, decision.owner_id)
            assert len(history) == 1
            assert session.get(DecisionRow, decision.decision_id).status == history[0].to_status.value
            assert repo.list_decision_events(decision.decision_id, uuid4()) == ()
    finally:
        database.dispose()


def test_owner_ledger_snapshot_replay_on_postgresql(tmp_path, postgres_url):
    database, store, args = setup_valuation(tmp_path, database_url=postgres_url)
    try:
        with database.session() as session:
            service = PortfolioLedgerService(ArtifactService(store, PlatformRepository(session)))
            result = service.replay(**args)
        with database.session() as session:
            repo = PlatformRepository(session)
            assert PortfolioLedgerService(ArtifactService(store, repo)).replay(**args) == result
            assert repo.get_portfolio_snapshot(result.portfolio_id, uuid4()) is None
            evidence = load_valuation_evidence(ArtifactService(store, repo), result, args["owner_id"])
            assert evidence.portfolio_content_hash == result.content_hash
            assert evidence.sources[0].quote.price == result.positions[0].market_price
            assert evidence.sources[0].quote.snapshot_id == next(iter(args["price_snapshot_ids"].values()))
            assert load_valuation_evidence(ArtifactService(store, repo), result, uuid4()) is None
    finally:
        database.dispose()


def test_owner_risk_and_evaluation_replay_on_postgresql(tmp_path, postgres_url):
    database, store, request = setup_evaluation(tmp_path, database_url=postgres_url)
    try:
        with database.session() as session:
            repo = PlatformRepository(session, artifact_store=store)
            decision = repo.get_decision(request.cells[0].decision_id, request.owner_id)
            repo.add_decision_event(_approval(decision))
            service = PersistedEvaluationService(ArtifactService(store, repo))
            artifact = service.create(request)
        with database.session() as session:
            service = PersistedEvaluationService(ArtifactService(store, PlatformRepository(session)))
            assert service.verify(artifact.artifact_id, request.owner_id).evaluation.reproducible
            assert service.create(request) == artifact
            with pytest.raises(ValueError):
                service.verify(artifact.artifact_id, uuid4())
    finally:
        database.dispose()
