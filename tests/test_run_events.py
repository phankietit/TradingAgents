"""Append-only run event ordering, owner isolation, and PostgreSQL concurrency evidence."""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from tradingagents.contracts import (
    AssetClass,
    InstrumentContract,
    RunEventType,
    RunManifest,
    RunStatus,
    Tradability,
)
from tradingagents.platform.events import RunEventConflict, RunEventNotFound, RunEventStore
from tradingagents.platform.persistence import (
    Database,
    PlatformRepository,
    downgrade_database,
    upgrade_database,
)

NOW = datetime(2026, 9, 23, 13, 0, tzinfo=UTC)


def _seed(database: Database) -> tuple[UUID, RunManifest]:
    owner_id = uuid4()
    instrument = InstrumentContract(
        instrument_id=uuid4(),
        symbol="AAPL",
        canonical_symbol=f"AAPL-{uuid4()}",
        display_name="Apple Inc.",
        asset_class=AssetClass.EQUITY,
        tradability=Tradability.INVESTABLE,
        venue="NASDAQ",
        quote_currency="USD",
        timezone="America/New_York",
        session_calendar="XNYS",
        benchmark_symbol="SPY",
    )
    run = RunManifest(
        run_id=uuid4(),
        owner_id=owner_id,
        instrument_id=instrument.instrument_id,
        analysis_as_of=NOW,
        status=RunStatus.QUEUED,
        created_at=NOW,
        selected_analysts=("market",),
        llm_provider="openai",
        quick_model="quick",
        deep_model="deep",
        config_hash="sha256:" + "d" * 64,
        prompt_version="1",
    )
    with database.session() as session:
        repository = PlatformRepository(session)
        repository.add_instrument(instrument)
        repository.save_run(run)
    return owner_id, run


@pytest.mark.unit
def test_events_are_append_only_ordered_and_resumable(tmp_path):
    url = f"sqlite:///{tmp_path / 'events.db'}"
    upgrade_database(url)
    database = Database(url)
    owner_id, run = _seed(database)
    with database.session() as session:
        store = RunEventStore(session)
        queued = store.append(
            owner_id=owner_id,
            run_id=run.run_id,
            event_type=RunEventType.RUN_QUEUED,
            occurred_at=NOW,
            payload={"job_id": str(uuid4())},
        )
        started = store.append(
            owner_id=owner_id,
            run_id=run.run_id,
            event_type=RunEventType.RUN_STARTED,
            occurred_at=NOW,
        )
    assert (queued.sequence, started.sequence) == (1, 2)

    with database.session() as session:
        store = RunEventStore(session)
        assert store.list_after(owner_id, run.run_id) == (queued, started)
        assert store.list_after(owner_id, run.run_id, after_sequence=1) == (started,)
        with pytest.raises(RunEventNotFound):
            store.list_after(uuid4(), run.run_id)
        with pytest.raises(RunEventNotFound):
            store.append(
                owner_id=uuid4(),
                run_id=run.run_id,
                event_type=RunEventType.RUN_FAILED,
            )
        assert (
            store.append(
                owner_id=owner_id,
                run_id=run.run_id,
                event_type=queued.event_type,
                payload=queued.payload,
                event_id=queued.event_id,
            )
            == queued
        )
        with pytest.raises(RunEventConflict):
            store.append(
                owner_id=owner_id,
                run_id=run.run_id,
                event_type=RunEventType.RUN_FAILED,
                event_id=queued.event_id,
            )
    database.dispose()


@pytest.mark.integration
def test_postgresql_concurrent_appends_receive_distinct_sequences():
    url = os.environ.get("TEST_POSTGRES_URL")
    if not url:
        pytest.skip("TEST_POSTGRES_URL is required for the PostgreSQL integration gate")

    database = Database(url)
    try:
        upgrade_database(url)
        owner_id, run = _seed(database)

        def append(index: int):
            with database.session() as session:
                return RunEventStore(session).append(
                    owner_id=owner_id,
                    run_id=run.run_id,
                    event_type=RunEventType.STAGE_STARTED,
                    occurred_at=NOW,
                    payload={"stage": f"stage-{index}"},
                )

        with ThreadPoolExecutor(max_workers=4) as executor:
            events = list(executor.map(append, range(8)))
        assert sorted(event.sequence for event in events) == list(range(1, 9))
        with database.session() as session:
            persisted = RunEventStore(session).list_after(owner_id, run.run_id)
        assert [event.sequence for event in persisted] == list(range(1, 9))
    finally:
        downgrade_database(url)
        database.dispose()
