"""Authenticated consent reservations only; no model, paid job or private DB."""

import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import replace
from datetime import timedelta
from threading import Barrier
from time import monotonic
from uuid import uuid4

import pytest
from sqlalchemy import inspect, select, update
from sqlalchemy.exc import SQLAlchemyError

from tests.test_accounting_evidence import append, receipt
from tests.test_recovery_fingerprint import inputs
from tests.test_snapshot_checkpoint_codec import checkpoint
from tradingagents.contracts import RunEventType
from tradingagents.platform.analysis.checkpoint_codec import SnapshotCheckpointCodec
from tradingagents.platform.analysis.checkpoint_store import PrivateCheckpointStore
from tradingagents.platform.analysis.continuation import (
    ContinuationConsentError,
    ContinuationConsentStore,
)
from tradingagents.platform.auth import OwnerAuth
from tradingagents.platform.events import RunEventStore
from tradingagents.platform.jobs import DurableJobQueue, JobWorker
from tradingagents.platform.jobs.worker import JobExecutionContext
from tradingagents.platform.persistence import (
    Database,
    PlatformRepository,
    downgrade_database,
    upgrade_database,
)
from tradingagents.platform.persistence.models import (
    JobRow,
    ResearchCheckpointRow,
    ResearchContinuationRow,
    RunEventRow,
    RunRow,
)

PASSWORD = "synthetic consent fixture password"


def history(database):
    with database.session() as session:
        return {model.__tablename__: [
            {column.name: deepcopy(getattr(row, column.name)) for column in model.__table__.columns}
            for row in session.scalars(select(model)).all()]
            for model in (RunRow, JobRow, RunEventRow, ResearchCheckpointRow)}


@pytest.fixture
def prepared(tmp_path, request):
    mode = getattr(request, "param", False)
    postgres = mode in ("postgres_failed", "postgres_cancelled")
    url = os.getenv("TEST_POSTGRES_URL") if postgres else f"sqlite:///{tmp_path / 'consent.db'}"
    if not url:
        pytest.skip("TEST_POSTGRES_URL is required for the PostgreSQL integration gate")
    fixture = _prepared(url, cancelled=mode is True or mode == "postgres_cancelled")
    try:
        yield from fixture
    finally:
        fixture.close()
        if postgres:
            # Explicit disposable integration database only, never private state.
            downgrade_database(url)


def _prepared(url, *, cancelled):
    args = inputs()
    run, owner = args["run"], args["owner_id"]
    now = run.created_at
    upgrade_database(url)
    database = Database(url)
    worker = JobWorker(database, worker_id="fixture-worker", handlers={}, clock=lambda: now)
    payload = {"instrument_id": str(run.instrument_id), "analysis_as_of": run.analysis_as_of.isoformat(),
        "selected_analysts": list(run.selected_analysts), "config_hash": run.config_hash,
        "decision_inputs": run.decision_inputs.model_dump(mode="json"), "report_language": run.report_language,
        "execution_limits": run.execution_limits.model_dump(mode="json")}
    with database.session() as session:
        auth = OwnerAuth(session)
        auth.bootstrap_owner("consent-fixture@example.test", PASSWORD, owner_id=owner, now=now)
        issued = auth.login("consent-fixture@example.test", PASSWORD, now=now)
        repository = PlatformRepository(session)
        repository.add_instrument(args["request"].instrument)
        repository.save_run(run)
        queue = DurableJobQueue(session)
        queue.enqueue(owner_id=owner, run_id=run.run_id, idempotency_key=str(uuid4()), payload=payload, now=now)
        job = queue.claim("fixture-worker", lease_for=timedelta(minutes=5), now=now)
        worker._record_job_state(session, job, now)
    context = JobExecutionContext(database, job.job_id, "fixture-worker", timedelta(minutes=5), lambda: now)
    codec = SnapshotCheckpointCodec(fingerprint="a" * 64, nodes={"Market Analyst"})
    cp = checkpoint()
    cp.config["configurable"]["thread_id"] = str(run.run_id)
    cp.metadata["thread_id"] = str(run.run_id)
    # The codec fixture date must agree with this original synthetic run.
    cp.checkpoint["ts"] = now.isoformat()
    PrivateCheckpointStore(codec=codec).commit(context=context, owner_id=owner, run_id=run.run_id, raw=codec.encode(cp))
    payloads = receipt()
    for value in payloads:
        value["elapsed_seconds"] = 10
    payloads.append({**deepcopy(payloads[-1]), "execution_stopped": True})
    with context.publication_session() as session:
        append(session, owner, run, job.attempt, payloads)
    with database.session() as session:
        queue = DurableJobQueue(session)
        if cancelled:
            queue.request_cancel(job.job_id, owner_id=owner, now=now + timedelta(seconds=10))
            job = queue.complete(job.job_id, "fixture-worker", now=now + timedelta(seconds=10))
        else:
            job = queue.fail(job.job_id, "fixture-worker", retryable=False,
                error_code="RESEARCH_EXECUTION_FAILED", now=now + timedelta(seconds=10))
        worker._record_job_state(session, job, now + timedelta(seconds=10))
    clock = [now + timedelta(minutes=1)]
    store = ContinuationConsentStore(database, codec=codec, clock=lambda: clock[0])
    with database.session() as session:
        observed = store.observe(session=session, owner_id=owner, run_id=run.run_id)
    values = {"session_token": issued.token, "csrf_token": issued.csrf_token,
        "expected_observation": observed, "idempotency_key": uuid4(), "confirm_continue": True}
    try:
        yield database, store, values, clock
    finally:
        database.dispose()


@pytest.mark.parametrize("prepared", [False, True,
    pytest.param("postgres_failed", marks=pytest.mark.integration),
    pytest.param("postgres_cancelled", marks=pytest.mark.integration)], indirect=True)
def test_durable_idempotent_private_link_preserves_all_original_history(prepared):
    database, store, values, _ = prepared
    before = history(database)
    first = store.record(**values)
    assert store.record(**values) == first
    reopened = Database(database.engine.url.render_as_string(hide_password=False))
    try:
        same = ContinuationConsentStore(reopened, codec=store.codec, clock=store.clock).record(**values)
        assert same == first
        with reopened.session() as session:
            rows = session.scalars(select(ResearchContinuationRow)).all()
            assert len(rows) == 1
            row = rows[0]
            observed = values["expected_observation"]
            assert row.execution_id == first.execution_id and row.source_run_id == observed.run_id
            assert row.source_job_id == observed.source_job_id and row.checkpoint_record_id == observed.checkpoint_record_id
            assert row.source_event_sequence == observed.accounting.high_water_sequence
            bound = row.payload["observation"]["accounting"]
            assert bound["started_calls"] == 1 and bound["reported_total_tokens"] == 15
            assert bound["elapsed_upper_bound"] == 10
            assert bound["original_wall_seconds"] == 1800 and bound["original_model_calls"] == 128
            assert row.payload["dispatch_enabled"] is False
            text = json.dumps(row.payload)
            assert values["session_token"] not in text and values["csrf_token"] not in text
            assert PASSWORD not in text and "consent-fixture@example.test" not in text
            assert str(observed.owner_id) not in repr(first) + repr(observed)
        assert history(database) == before
    finally:
        reopened.dispose()


@pytest.mark.parametrize("mutation", [
    "token", "csrf", "expired", "revoked", "disabled", "owner", "run", "counter", "bool_counter", "type",
    "confirmation", "bool_like", "key_type", "event", "unknown_stop", "job_payload", "checkpoint_hash",
    "checkpoint_fingerprint", "checkpoint_owner", "checkpoint_attempt", "checkpoint_future", "in_flight",
    "elapsed_exhausted", "calls_exhausted", "checkpoint_missing",
])
def test_auth_staleness_identity_uncertainty_and_input_refuse_without_history_mutation(prepared, mutation):
    database, store, supplied, clock = prepared
    values = dict(supplied)
    observed = values["expected_observation"]
    if mutation == "token":
        values["session_token"] = "ta_session_PRIVATE_NEVER_ECHO"
    elif mutation == "csrf":
        values["csrf_token"] = "PRIVATE_NEVER_ECHO" * 3
    elif mutation == "expired":
        clock[0] += timedelta(days=1)
    elif mutation in {"revoked", "disabled"}:
        with database.session() as session:
            auth = OwnerAuth(session)
            if mutation == "revoked":
                auth.revoke_session(values["session_token"], now=clock[0])
            else:
                auth.disable_owner(observed.owner_id, now=clock[0])
    elif mutation in {"owner", "run", "counter", "bool_counter"}:
        changes = {"owner": {"owner_id": uuid4()}, "run": {"run_id": uuid4()},
            "counter": {"accounting": replace(observed.accounting, started_calls=0)},
            "bool_counter": {"accounting": replace(observed.accounting, started_calls=True)}}[mutation]
        values["expected_observation"] = replace(observed, **changes)
    elif mutation == "type":
        values["expected_observation"] = object()
    elif mutation == "confirmation":
        values["confirm_continue"] = False
    elif mutation == "bool_like":
        values["confirm_continue"] = 1
    elif mutation == "key_type":
        values["idempotency_key"] = str(values["idempotency_key"])
    elif mutation == "event":
        with database.session() as session:
            RunEventStore(session).append(owner_id=observed.owner_id, run_id=observed.run_id,
                event_type=RunEventType.STAGE_STARTED, occurred_at=clock[0], payload={"stage": "Market Analyst"})
    else:
        # Deliberate corruption in a disposable fixture, not a permitted writer.
        with database.session() as session:
            if mutation in {"unknown_stop", "elapsed_exhausted", "calls_exhausted"}:
                row = session.scalar(select(RunEventRow).where(RunEventRow.event_type == "model.usage")
                    .order_by(RunEventRow.sequence.desc()))
                value = deepcopy(row.payload)
                if mutation == "unknown_stop":
                    value.pop("execution_stopped")
                elif mutation == "elapsed_exhausted":
                    value["elapsed_seconds"] = 1800
                else:
                    value["usage"].update(started_model_calls=128, status="incomplete")
                row.payload = value
            elif mutation == "job_payload":
                row = session.get(JobRow, observed.source_job_id)
                row.payload = {**row.payload, "config_hash": "sha256:" + "b" * 64}
            elif mutation == "in_flight":
                row = session.get(JobRow, observed.source_job_id)
                row.status, row.completed_at = "running", None
                row.lease_owner, row.lease_expires_at = "fixture-worker", clock[0] + timedelta(minutes=5)
            else:
                row = session.get(ResearchCheckpointRow, observed.checkpoint_record_id)
                if mutation == "checkpoint_missing":
                    session.delete(row)
                elif mutation == "checkpoint_hash":
                    row.payload = b"PRIVATE_NEVER_ECHO"
                elif mutation == "checkpoint_fingerprint":
                    row.fingerprint = "b" * 64
                elif mutation == "checkpoint_owner":
                    row.owner_id = uuid4()
                elif mutation == "checkpoint_attempt":
                    row.attempt += 1
                elif mutation == "checkpoint_future":
                    row.created_at = clock[0] + timedelta(days=1)
    before = history(database)
    with pytest.raises(ContinuationConsentError) as raised:
        store.record(**values)
    assert str(raised.value) == "continuation consent requires review" and raised.value.__cause__ is None
    assert history(database) == before
    with database.session() as session:
        assert session.scalar(select(ResearchContinuationRow)) is None


@pytest.mark.parametrize("same_key", [False, True])
@pytest.mark.parametrize("prepared", [False,
    pytest.param("postgres_failed", marks=pytest.mark.integration)], indirect=True)
def test_concurrent_requests_reserve_one_link_not_two_executions(prepared, same_key):
    database, store, values, _ = prepared
    barrier = Barrier(2)

    def submit(index):
        args = dict(values)
        if not same_key and index:
            args["idempotency_key"] = uuid4()
        barrier.wait(timeout=5)
        try:
            return store.record(**args)
        except ContinuationConsentError:
            return None

    before = history(database)
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(submit, range(2)))
    succeeded = [result for result in results if result is not None]
    assert len(succeeded) == (2 if same_key else 1)
    assert len({result.execution_id for result in succeeded}) == 1
    with database.session() as session:
        assert len(session.scalars(select(ResearchContinuationRow)).all()) == 1
    assert history(database) == before


def test_commit_failure_rolls_back_without_ack_or_original_mutation(prepared, monkeypatch):
    database, store, values, _ = prepared
    before = history(database)
    original = database.session

    @contextmanager
    def fail_commit(**options):
        with original(**options) as session:
            yield session
            raise SQLAlchemyError("PRIVATE_NEVER_ECHO")

    monkeypatch.setattr(database, "session", fail_commit)
    with pytest.raises(ContinuationConsentError, match="^continuation consent requires review$"):
        store.record(**values)
    monkeypatch.setattr(database, "session", original)
    assert history(database) == before
    with database.session() as session:
        assert session.scalar(select(ResearchContinuationRow)) is None


def test_busy_writer_refuses_under_local_lock_bound(prepared):
    database, store, values, _ = prepared
    store.lock_timeout_seconds = .05
    with database.engine.connect() as writer:
        writer.exec_driver_sql("BEGIN IMMEDIATE")
        started = monotonic()
        with pytest.raises(ContinuationConsentError):
            store.record(**values)
        assert monotonic() - started < 1
        writer.rollback()
    with database.session() as session:
        assert session.scalar(select(ResearchContinuationRow)) is None


@pytest.mark.parametrize("timeout", [None, 0, float("nan")])
@pytest.mark.parametrize("mutated", [False, True])
def test_no_unbounded_or_invalid_transaction_option(prepared, timeout, mutated):
    database, store, values, _ = prepared
    before = history(database)
    with pytest.raises(ContinuationConsentError):
        if mutated:
            store.lock_timeout_seconds = timeout
            store.record(**values)
        else:
            ContinuationConsentStore(database, codec=store.codec, lock_timeout_seconds=timeout)
    assert history(database) == before


def test_newer_checkpoint_cannot_be_silently_ignored(prepared):
    database, store, values, _ = prepared
    observed = values["expected_observation"]
    with database.session() as session:
        row = session.get(ResearchCheckpointRow, observed.checkpoint_record_id)
        cp = store.codec.decode(row.payload)
        cp.pending_writes.append((str(uuid4()), "market_report", "new synthetic pending output"))
        raw = store.codec.encode(cp)
        columns = {column.name: getattr(row, column.name) for column in ResearchCheckpointRow.__table__.columns}
        columns.update(record_id=uuid4(), sequence=row.sequence + 1, payload=raw,
            content_hash=hashlib.sha256(raw).hexdigest())
        session.add(ResearchCheckpointRow(**columns))
    before = history(database)
    with pytest.raises(ContinuationConsentError):
        store.record(**values)
    assert history(database) == before


def test_migration_roundtrip_preserves_original_research_history(prepared):
    database, _, _, _ = prepared
    before = history(database)
    url = str(database.engine.url)
    # Only the fresh task-owned fixture. Never a private owner database.
    downgrade_database(url, "0011_research_checkpoints")
    assert "research_continuations" not in inspect(database.engine).get_table_names()
    assert history(database) == before
    upgrade_database(url)
    assert "research_continuations" in inspect(database.engine).get_table_names()
    assert history(database) == before


@pytest.mark.parametrize("mutation", ["boolean_payload", "digest", "checkpoint", "future_date"])
def test_idempotent_link_rejects_corrupt_persisted_receipt(prepared, mutation):
    database, store, values, clock = prepared
    first = store.record(**values)
    with database.session() as session:
        row = session.get(ResearchContinuationRow, first.execution_id)
        if mutation == "boolean_payload":
            value = deepcopy(row.payload)
            value["observation"]["accounting"]["started_calls"] = True
            # Bypass ORM JSON dirty equality for this corruption fixture:
            # assigning an equal-looking dict would not actually issue UPDATE.
            session.execute(update(ResearchContinuationRow).where(
                ResearchContinuationRow.execution_id == first.execution_id).values(payload=value))
        elif mutation == "digest":
            row.observation_hash = "b" * 64
        elif mutation == "checkpoint":
            row.checkpoint_record_id = uuid4()
        else:
            row.created_at = clock[0] + timedelta(days=1)
    with pytest.raises(ContinuationConsentError):
        store.record(**values)
