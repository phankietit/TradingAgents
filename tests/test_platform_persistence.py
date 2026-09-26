"""Migration, transaction, immutability, and owner-isolation evidence."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, inspect, text

from tradingagents.contracts import (
    AssetClass,
    CashBalance,
    DataQualityStatus,
    DecisionCandidate,
    DecisionRating,
    DecisionStatus,
    InstrumentContract,
    PolicyContract,
    PortfolioSnapshot,
    RunManifest,
    RunStatus,
    SnapshotManifest,
    Tradability,
)
from tradingagents.platform.persistence import (
    Database,
    ImmutableRecordConflict,
    InvalidStateTransition,
    PlatformRepository,
    downgrade_database,
    upgrade_database,
)
from tradingagents.platform.persistence.models import InstrumentRow

NOW = datetime(2026, 9, 23, 8, 0, tzinfo=UTC)


def _url(tmp_path) -> str:
    return f"sqlite:///{tmp_path / 'platform.db'}"


def _instrument():
    return InstrumentContract(
        instrument_id=uuid4(),
        symbol="AAPL",
        canonical_symbol="AAPL",
        display_name="Apple Inc.",
        asset_class=AssetClass.EQUITY,
        tradability=Tradability.INVESTABLE,
        venue="NASDAQ",
        quote_currency="USD",
        timezone="America/New_York",
        session_calendar="XNYS",
        benchmark_symbol="SPY",
    )


def _run(instrument_id, owner_id, *, status=RunStatus.QUEUED, run_id=None):
    started = NOW + timedelta(seconds=1) if status is not RunStatus.QUEUED else None
    terminal = status in {RunStatus.SUCCEEDED, RunStatus.FAILED, RunStatus.CANCELLED}
    return RunManifest(
        run_id=run_id or uuid4(),
        owner_id=owner_id,
        instrument_id=instrument_id,
        analysis_as_of=NOW,
        status=status,
        created_at=NOW,
        started_at=started,
        completed_at=NOW + timedelta(seconds=2) if terminal else None,
        selected_analysts=("market",),
        llm_provider="openai",
        quick_model="quick",
        deep_model="deep",
        config_hash="sha256:" + "a" * 64,
        prompt_version="1",
        error_code="TEST_FAILURE" if status is RunStatus.FAILED else None,
    )


@pytest.mark.unit
def test_migration_upgrades_and_downgrades_all_tables(tmp_path):
    url = _url(tmp_path)
    upgrade_database(url)
    database = Database(url)
    tables = set(inspect(database.engine).get_table_names())
    assert {
        "alembic_version",
        "analysis_jobs",
        "analysis_runs",
        "artifacts",
        "decisions",
        "instrument_aliases",
        "instruments",
        "owner_accounts",
        "owner_sessions",
        "policies",
        "portfolio_snapshots",
        "run_events",
        "snapshots",
    } <= tables

    downgrade_database(url)
    remaining = set(inspect(database.engine).get_table_names())
    assert remaining <= {"alembic_version"}
    database.dispose()


@pytest.mark.unit
def test_instrument_alias_migration_backfills_existing_canonical_symbols(tmp_path):
    url = _url(tmp_path)
    upgrade_database(url, "0006_run_events")
    instrument = _instrument()
    database = Database(url)
    with database.session() as session:
        session.add(
            InstrumentRow(
                instrument_id=instrument.instrument_id,
                schema_version=instrument.schema_version,
                symbol=instrument.symbol,
                canonical_symbol=instrument.canonical_symbol,
                asset_class=instrument.asset_class.value,
                tradability=instrument.tradability.value,
                payload=instrument.model_dump(mode="json"),
                created_at=NOW,
            )
        )
    database.dispose()

    upgrade_database(url)
    database = Database(url)
    with database.session() as session:
        repository = PlatformRepository(session)
        assert repository.resolve_instrument(" aapl ") == instrument
        assert repository.list_instrument_aliases(instrument.instrument_id)[0].namespace == "canonical"
    database.dispose()


@pytest.mark.unit
def test_csrf_migration_revokes_preexisting_sessions(tmp_path):
    url = _url(tmp_path)
    upgrade_database(url, "0004_owner_authentication")
    engine = create_engine(url)
    owner_id = str(uuid4())
    session_id = str(uuid4())
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO owner_accounts "
                "(owner_id, singleton_key, email, password_hash, status, created_at, updated_at) "
                "VALUES (:owner_id, 'primary-owner', 'owner@example.com', 'legacy', 'active', "
                ":created_at, :updated_at)"
            ),
            {"owner_id": owner_id, "created_at": NOW, "updated_at": NOW},
        )
        connection.execute(
            text(
                "INSERT INTO owner_sessions "
                "(session_id, owner_id, token_hash, issued_at, expires_at, last_seen_at, revoked_at) "
                "VALUES (:session_id, :owner_id, :token_hash, :issued_at, :expires_at, "
                ":last_seen_at, NULL)"
            ),
            {
                "session_id": session_id,
                "owner_id": owner_id,
                "token_hash": "a" * 64,
                "issued_at": NOW,
                "expires_at": NOW + timedelta(hours=1),
                "last_seen_at": NOW,
            },
        )

    upgrade_database(url)
    with engine.connect() as connection:
        row = connection.execute(
            text(
                "SELECT csrf_token_hash, revoked_at FROM owner_sessions "
                "WHERE session_id = :session_id"
            ),
            {"session_id": session_id},
        ).one()
    assert row.csrf_token_hash == "0" * 64
    assert row.revoked_at is not None
    engine.dispose()


@pytest.mark.unit
def test_immutable_records_are_idempotent_but_not_replaceable(tmp_path):
    url = _url(tmp_path)
    upgrade_database(url)
    database = Database(url)
    instrument = _instrument()
    with database.session() as session:
        repository = PlatformRepository(session)
        repository.add_instrument(instrument)
        repository.add_instrument(instrument)

    changed = instrument.model_copy(update={"display_name": "Different Company"})
    with pytest.raises(ImmutableRecordConflict), database.session() as session:
        PlatformRepository(session).add_instrument(changed)

    with database.session() as session:
        assert PlatformRepository(session).get_instrument(instrument.instrument_id) == instrument
    database.dispose()


@pytest.mark.unit
def test_owner_scoped_run_lookup_and_valid_transition(tmp_path):
    url = _url(tmp_path)
    upgrade_database(url)
    database = Database(url)
    instrument = _instrument()
    owner_id = uuid4()
    queued = _run(instrument.instrument_id, owner_id)
    running = _run(
        instrument.instrument_id,
        owner_id,
        status=RunStatus.RUNNING,
        run_id=queued.run_id,
    )

    with database.session() as session:
        repository = PlatformRepository(session)
        repository.add_instrument(instrument)
        repository.save_run(queued)
        repository.save_run(running)

    with database.session() as session:
        repository = PlatformRepository(session)
        assert repository.get_run(queued.run_id, owner_id) == running
        assert repository.get_run(queued.run_id, uuid4()) is None
    database.dispose()


@pytest.mark.unit
def test_terminal_run_cannot_transition_and_transaction_rolls_back(tmp_path):
    url = _url(tmp_path)
    upgrade_database(url)
    database = Database(url)
    instrument = _instrument()
    owner_id = uuid4()
    succeeded = _run(instrument.instrument_id, owner_id, status=RunStatus.SUCCEEDED)
    with database.session() as session:
        repository = PlatformRepository(session)
        repository.add_instrument(instrument)
        repository.save_run(succeeded)

    running_again = _run(
        instrument.instrument_id,
        owner_id,
        status=RunStatus.RUNNING,
        run_id=succeeded.run_id,
    )
    with pytest.raises(InvalidStateTransition), database.session() as session:
        PlatformRepository(session).save_run(running_again)

    with database.session() as session:
        assert PlatformRepository(session).get_run(succeeded.run_id, owner_id) == succeeded
    database.dispose()


@pytest.mark.unit
def test_saved_run_state_cannot_be_rewritten_without_transition(tmp_path):
    url = _url(tmp_path)
    upgrade_database(url)
    database = Database(url)
    instrument = _instrument()
    queued = _run(instrument.instrument_id, uuid4())
    with database.session() as session:
        repository = PlatformRepository(session)
        repository.add_instrument(instrument)
        repository.save_run(queued)

    rewritten = queued.model_copy(update={"quick_model": "different-model"})
    with pytest.raises(ImmutableRecordConflict), database.session() as session:
        PlatformRepository(session).save_run(rewritten)

    with database.session() as session:
        assert PlatformRepository(session).get_run(queued.run_id, queued.owner_id) == queued
    database.dispose()


@pytest.mark.unit
def test_snapshot_round_trip_preserves_provenance(tmp_path):
    url = _url(tmp_path)
    upgrade_database(url)
    database = Database(url)
    instrument = _instrument()
    snapshot = SnapshotManifest(
        snapshot_id=uuid4(),
        instrument_id=instrument.instrument_id,
        dataset="ohlcv.daily",
        vendor="example",
        as_of=NOW,
        retrieved_at=NOW + timedelta(minutes=1),
        source_start=NOW - timedelta(days=30),
        source_end=NOW,
        content_hash="sha256:" + "b" * 64,
        quality_status=DataQualityStatus.OK,
    )
    with database.session() as session:
        repository = PlatformRepository(session)
        repository.add_instrument(instrument)
        repository.add_snapshot(snapshot)

    with database.session() as session:
        assert PlatformRepository(session).get_snapshot(snapshot.snapshot_id) == snapshot
    database.dispose()


@pytest.mark.unit
def test_private_contracts_require_matching_owner(tmp_path):
    url = _url(tmp_path)
    upgrade_database(url)
    database = Database(url)
    instrument = _instrument()
    owner_id = uuid4()
    other_owner_id = uuid4()
    run = _run(instrument.instrument_id, owner_id, status=RunStatus.SUCCEEDED)
    decision = DecisionCandidate(
        decision_id=uuid4(),
        run_id=run.run_id,
        owner_id=owner_id,
        instrument_id=instrument.instrument_id,
        as_of=NOW,
        status=DecisionStatus.REVIEW,
        rating=DecisionRating.HOLD,
        confidence=0.6,
        thesis="Valuation and quality are balanced.",
        risks=("Multiple compression",),
        invalidation_conditions=("Material earnings miss",),
        evidence=(),
        data_quality=DataQualityStatus.OK,
        policy_checks=(),
    )
    portfolio = PortfolioSnapshot(
        portfolio_id=uuid4(),
        owner_id=owner_id,
        as_of=NOW,
        base_currency="USD",
        cash=(CashBalance(currency="USD", amount="10000"),),
        positions=(),
        net_asset_value="10000",
        content_hash="sha256:" + "c" * 64,
    )
    policy = PolicyContract(
        policy_id=uuid4(),
        owner_id=owner_id,
        name="US large-cap baseline",
        policy_version="1.0.0",
        asset_class=AssetClass.EQUITY,
        effective_at=NOW,
        parameters={"max_weight": 0.1},
    )

    with database.session() as session:
        repository = PlatformRepository(session)
        repository.add_instrument(instrument)
        repository.save_run(run)
        repository.add_decision(decision)
        repository.add_portfolio_snapshot(portfolio)
        repository.add_policy(policy)

    with database.session() as session:
        repository = PlatformRepository(session)
        assert repository.get_decision(decision.decision_id, owner_id) == decision
        assert repository.get_decision(decision.decision_id, other_owner_id) is None
        assert repository.get_portfolio_snapshot(portfolio.portfolio_id, owner_id) == portfolio
        assert repository.get_portfolio_snapshot(portfolio.portfolio_id, other_owner_id) is None
        assert repository.get_policy(policy.policy_id, policy.policy_version, owner_id) == policy
        assert (
            repository.get_policy(policy.policy_id, policy.policy_version, other_owner_id) is None
        )
    database.dispose()


@pytest.mark.integration
def test_postgresql_target_uses_jsonb_and_round_trips_contracts():
    url = os.environ.get("TEST_POSTGRES_URL")
    if not url:
        pytest.skip("TEST_POSTGRES_URL is required for the PostgreSQL integration gate")

    database = Database(url)
    try:
        upgrade_database(url)
        payload_column = next(
            column
            for column in inspect(database.engine).get_columns("instruments")
            if column["name"] == "payload"
        )
        assert payload_column["type"].__class__.__name__ == "JSONB"

        instrument = _instrument()
        with database.session() as session:
            PlatformRepository(session).add_instrument(instrument)
        with database.session() as session:
            assert (
                PlatformRepository(session).get_instrument(instrument.instrument_id) == instrument
            )
    finally:
        downgrade_database(url)
        database.dispose()
