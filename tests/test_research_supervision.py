"""Spawned local engines: never contact a market/LLM provider."""

import json
import os
import signal
import subprocess
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager, suppress
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from multiprocessing import get_context
from pathlib import Path
from threading import Event, Thread
from time import monotonic, sleep
from types import SimpleNamespace
from uuid import uuid4, uuid5

import pytest

from tests.test_risk_engine import NOW
from tests.test_risk_provenance import setup_risk
from tradingagents._compat import UTC
from tradingagents.contracts import (
    ArtifactKind,
    AssetClass,
    InstrumentContract,
    JobKind,
    JobStatus,
    Tradability,
)
from tradingagents.contracts.runs import DecisionRunInputs
from tradingagents.platform.analysis.engine import AnalysisRequest, AnalysisResult
from tradingagents.platform.analysis.observer import (
    ResearchBudgetExceeded,
    ResearchExecutionFailed,
    ResearchObserver,
)
from tradingagents.platform.analysis.snapshots import SnapshotAnalysisContext
from tradingagents.platform.analysis.supervision import (
    SupervisedAnalysisEngine,
    _Bridge,
    _wait_for_linked_exit,
)
from tradingagents.platform.artifacts import ArtifactService
from tradingagents.platform.jobs import DurableJobQueue, JobWorker
from tradingagents.platform.jobs.analysis import AnalysisJobHandler
from tradingagents.platform.jobs.worker import JobCancellationRequested
from tradingagents.platform.persistence import PlatformRepository


class SpawnFixtureEngine:
    def __init__(self, *, base_config=None):
        self.config = base_config or {}

    def analyze(self, request):
        observer = request.execution_observer
        stage_id, model_id = uuid4(), uuid4()
        observer.on_chain_start({}, {}, run_id=stage_id, name="Market Analyst")
        observer.on_chat_model_start({}, [], run_id=model_id)
        Path(self.config["marker"]).write_text(str(os.getpid()))
        mode = self.config.get("mode", "success")
        if mode == "hang":
            while True:
                sleep(0.01)
        if mode == "failure":
            raise ValueError("sk-private-vendor-error")
        if mode == "http":
            from openai import OpenAI

            OpenAI(api_key="synthetic-local-only", base_url=self.config["url"],
                timeout=600, max_retries=1).chat.completions.create(
                    model="synthetic", messages=[{"role": "user", "content": "local fixture"}])
        observer.on_llm_end(SimpleNamespace(generations=[[SimpleNamespace(
            message=SimpleNamespace(usage_metadata={"input_tokens": 3,
                "output_tokens": 2, "total_tokens": 5}))]]), run_id=model_id)
        observer.on_chain_end({"market_report": "Synthetic returned note",
            "messages": ["private reasoning must not cross"]}, run_id=stage_id)
        return AnalysisResult(instrument=request.instrument, analysis_date=request.analysis_date,
            selected_analysts=("market",), profile_name="equity", reference_only=False,
            final_state={"market_report": "Synthetic returned note",
                "final_trade_decision": "REVIEW", "messages": ["private reasoning"]},
            narrative_signal="REVIEW")


@pytest.mark.parametrize("mode", ["slow_clean", "unclean", "deadline", "cancel", "late_cancel"])
def test_linked_exit_wait_preserves_original_budget_and_cancel(mode):
    clock = [0.0]
    joins = []
    finish = 1.5 if mode == "slow_clean" else .5
    if mode in {"deadline", "cancel"}:
        finish = 10

    class Process:
        def is_alive(self):
            return clock[0] < finish

        def join(self, timeout):
            joins.append(timeout)
            clock[0] = min(finish, clock[0] + timeout)

        @property
        def exitcode(self):
            return None if self.is_alive() else (1 if mode == "unclean" else 0)

    def check_cancelled():
        if mode in {"cancel", "late_cancel"} and clock[0] >= .5:
            raise JobCancellationRequested("synthetic cancellation")

    observer = ResearchObserver(clock=lambda: clock[0], check_cancelled=check_cancelled,
        emit=lambda *_: None, max_seconds=1 if mode == "deadline" else 3)
    expected = {"unclean": ResearchExecutionFailed, "deadline": ResearchBudgetExceeded,
                "cancel": JobCancellationRequested, "late_cancel": JobCancellationRequested}
    if mode == "slow_clean":
        _wait_for_linked_exit(Process(), observer)
        assert clock[0] == finish and observer.started == 0
    else:
        with pytest.raises(expected[mode]):
            _wait_for_linked_exit(Process(), observer)
    assert all(0 < duration <= .2 for duration in joins)
    assert clock[0] <= observer.max_seconds
    assert observer.started_calls == 0 and not observer._execution_stopped


def test_bridge_serializes_concurrent_frames_and_acknowledgements():
    class EchoConnection:
        def send(self, value):
            self.value = value
            sleep(0.005)

        def recv(self):
            return self.value

    bridge = _Bridge(EchoConnection())
    with ThreadPoolExecutor(max_workers=8) as pool:
        answers = list(pool.map(lambda value: bridge.rpc("echo", value), range(20)))
    assert answers == [("echo", value) for value in range(20)]


def request_with(observer):
    return AnalysisRequest(instrument=InstrumentContract(instrument_id=uuid4(),
        symbol="AAPL", canonical_symbol="AAPL", display_name="Synthetic Apple",
        asset_class=AssetClass.EQUITY, tradability=Tradability.INVESTABLE,
        venue="NASDAQ", quote_currency="USD", timezone="America/New_York",
        session_calendar="XNYS"), analysis_date=date(2026, 10, 2),
        selected_analysts=("market",), execution_observer=observer,
        snapshot_context=SnapshotAnalysisContext(as_of=datetime(2026, 10, 2, tzinfo=UTC),
            by_analyst={}, source_max_age_seconds={}))


def assert_child_stopped(marker):
    pid = int(marker.read_text())
    if os.name == "posix":
        with pytest.raises(ProcessLookupError):
            os.kill(pid, 0)


def _orphan_parent(marker):
    observer = ResearchObserver(check_cancelled=lambda: None, emit=lambda *_: None, max_seconds=60)
    SupervisedAnalysisEngine(base_config={"marker": marker, "mode": "hang"},
        engine_factory=SpawnFixtureEngine).analyze(request_with(observer))


def _process_running(pid):
    result = subprocess.run(["ps", "-p", str(pid), "-o", "stat="],
        check=False, capture_output=True, text=True)
    state = result.stdout.strip()
    return bool(state) and not state.startswith("Z")


@pytest.mark.skipif(os.name != "posix", reason="POSIX crash/orphan acceptance only")
def test_killed_parent_does_not_leave_an_executing_orphan_child(tmp_path):
    marker = tmp_path / "orphan-child"
    parent = get_context("spawn").Process(target=_orphan_parent, args=(str(marker),))
    child_pid = None
    try:
        parent.start()
        until = monotonic() + 20
        while not marker.exists() and monotonic() < until and parent.is_alive():
            sleep(0.05)
        assert marker.exists(), "isolated fixture child did not start"
        child_pid = int(marker.read_text())
        assert _process_running(child_pid)
        parent.kill()
        parent.join(timeout=3)
        assert not parent.is_alive()
        until = monotonic() + 5
        while _process_running(child_pid) and monotonic() < until:
            sleep(0.05)
        assert not _process_running(child_pid), "child kept executing after its parent died"
    finally:
        if parent.is_alive():
            parent.kill()
        parent.join(timeout=3)
        parent.close()
        # Only the PID written by this task-created private fixture is in scope.
        if child_pid is not None and _process_running(child_pid):
            with suppress(ProcessLookupError):
                os.kill(child_pid, signal.SIGKILL)


def test_spawn_retains_events_usage_and_reader_text_but_not_raw_messages(tmp_path):
    marker = tmp_path / "child"
    saved, events = [], []

    def emit(kind, payload):
        if payload.get("execution_stopped"):
            assert_child_stopped(marker)
        events.append((kind, payload))

    observer = ResearchObserver(check_cancelled=lambda: None,
        emit=emit, max_seconds=30,
        save_stage=lambda stage, outputs: saved.append((stage, outputs)))
    engine = SupervisedAnalysisEngine(base_config={"marker": str(marker)}, engine_factory=SpawnFixtureEngine)
    result = engine.analyze(request_with(observer))
    assert result.final_state == {"market_report": "Synthetic returned note", "final_trade_decision": "REVIEW"}
    assert saved == [("Market Analyst", {"market_report": "Synthetic returned note"})]
    assert observer.completed == ["Market Analyst"]
    assert observer.receipt()["usage"]["total_tokens"] == 5
    assert observer.receipt()["supervision_mode"] == "spawned_process"
    assert [event[0] for event in events] == ["stage.started", "model.usage", "model.usage", "stage.completed", "model.usage"]
    assert events[-1][1]["execution_stopped"] is True
    assert events[1][1]["usage"]["model_calls"] == 0
    assert events[1][1]["usage"]["started_model_calls"] == 1
    assert_child_stopped(marker)


@pytest.mark.parametrize("mode", ["success", "failure"])
def test_stop_append_refusal_does_not_replace_original_outcome(tmp_path, mode):
    marker = tmp_path / "child-stop-refusal"
    events, attempted = [], []

    def emit(kind, payload):
        if payload.get("execution_stopped"):
            assert_child_stopped(marker)
            attempted.append(True)
            raise RuntimeError("PRIVATE_STOP_APPEND_ERROR")
        events.append((kind, payload))

    observer = ResearchObserver(check_cancelled=lambda: None, emit=emit, max_seconds=30)
    engine = SupervisedAnalysisEngine(base_config={"marker": str(marker), "mode": mode},
                                     engine_factory=SpawnFixtureEngine)
    if mode == "failure":
        with pytest.raises(ResearchExecutionFailed, match="isolated research execution requires review") as raised:
            engine.analyze(request_with(observer))
        assert "PRIVATE_STOP_APPEND_ERROR" not in str(raised.value)
    else:
        result = engine.analyze(request_with(observer))
        assert result.narrative_signal == "REVIEW"
    assert attempted == [True]
    assert all("execution_stopped" not in payload for _, payload in events)
    assert observer.receipt()["usage"]["cost"] is None
    assert_child_stopped(marker)


@pytest.mark.parametrize("reason", ["deadline", "cancel", "failure"])
def test_hung_or_failed_child_stops_without_background_work_or_final_output(tmp_path, reason):
    marker = tmp_path / "child"
    clock = [0]

    def check():
        if marker.exists():
            if reason == "cancel":
                raise JobCancellationRequested("cancelled")
            if reason == "deadline":
                clock[0] = 31

    observer = ResearchObserver(check_cancelled=check, emit=lambda *_: None,
        clock=lambda: clock[0], max_seconds=30)
    engine = SupervisedAnalysisEngine(base_config={"marker": str(marker),
        "mode": "failure" if reason == "failure" else "hang"}, engine_factory=SpawnFixtureEngine)
    error = {"deadline": ResearchBudgetExceeded, "cancel": JobCancellationRequested,
             "failure": ResearchExecutionFailed}[reason]
    started = monotonic()
    with pytest.raises(error) as raised:
        engine.analyze(request_with(observer))
    assert monotonic() - started < 30
    assert "sk-private" not in str(raised.value)
    assert observer.completed == []
    usage = observer.receipt()["usage"]
    assert usage["started_model_calls"] == usage["failed_calls"] == 1
    assert usage["provider_request_attempts"] is None and usage["cost"] is None
    assert_child_stopped(marker)


def test_supervision_requires_authority_for_snapshot_jobs():
    with pytest.raises(ValueError, match="observer"):
        SupervisedAnalysisEngine().analyze(request_with(None))


def test_real_elapsed_deadline_does_not_reset_while_child_blocks(tmp_path):
    marker = tmp_path / "child"
    observer = ResearchObserver(check_cancelled=lambda: None, emit=lambda *_: None, max_seconds=10)
    engine = SupervisedAnalysisEngine(base_config={"marker": str(marker), "mode": "hang"},
                                     engine_factory=SpawnFixtureEngine)
    started = monotonic()
    with pytest.raises(ResearchBudgetExceeded):
        engine.analyze(request_with(observer))
    assert 9 <= monotonic() - started < 13
    assert_child_stopped(marker)


@pytest.mark.parametrize("mode", ["success", "failure"])
def test_real_durable_worker_keeps_parent_owned_stage_and_publication_gates(tmp_path, mode):
    database, store, seeded = setup_risk(tmp_path)
    marker = tmp_path / "child"
    with database.session() as session:
        repo = PlatformRepository(session, artifact_store=store)
        original = repo.get_run(seeded.run_id, seeded.owner_id)
        inputs = DecisionRunInputs(snapshots_by_analyst={"market": (seeded.risk_snapshot_ids[0],)},
            source_max_age_seconds={"market": 86400})
        run = original.model_copy(update={"run_id": uuid4(), "selected_analysts": ("market",),
            "snapshot_ids": inputs.snapshot_ids(), "decision_inputs": inputs})
        repo.save_run(run)
        DurableJobQueue(session).enqueue(owner_id=run.owner_id, run_id=run.run_id,
            idempotency_key=str(run.run_id), max_attempts=3, now=NOW, payload={
                "instrument_id": str(run.instrument_id), "analysis_as_of": NOW.isoformat(),
                "selected_analysts": ["market"], "config_hash": run.config_hash,
                "decision_inputs": inputs.model_dump(mode="json")})
    engine = SupervisedAnalysisEngine(base_config={"marker": str(marker), "mode": mode},
                                     engine_factory=SpawnFixtureEngine)
    handler = AnalysisJobHandler(database, store, engine=engine)
    job = JobWorker(database, worker_id="qa-supervised-worker", clock=lambda: NOW,
                   handlers={JobKind.ANALYSIS_RUN: handler}).run_once()
    assert job.status == (JobStatus.SUCCEEDED if mode == "success" else JobStatus.FAILED)
    assert job.attempt == 1
    with database.session() as session:
        repo = PlatformRepository(session, artifact_store=store)
        artifacts = ArtifactService(store, repo)
        report = artifacts.read(uuid5(run.run_id, "analysis-report-v1"), run.owner_id)
        stages = [item for item in repo.list_run_artifacts(run.run_id, run.owner_id)
                  if item.kind is ArtifactKind.RESEARCH_STAGE]
        if mode == "failure":
            assert report is None and not stages
            assert repo.get_decision(uuid5(run.run_id, "decision-v1"), run.owner_id) is None
            assert job.error_code == "RESEARCH_EXECUTION_FAILED"
        else:
            assert len(stages) == 1
            saved = json.loads(artifacts.read(stages[0].artifact_id, run.owner_id)[1])
            assert saved["approval_eligible"] is False
            content = json.loads(report[1])
            assert content["structured_narrative"] is None
            assert content["execution"]["supervision_mode"] == "spawned_process"
            assert "private reasoning" not in report[1].decode()
    assert_child_stopped(marker)


@contextmanager
def local_provider(mode):
    seen, stop = Event(), Event()
    calls = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_POST(self):
            calls.append(1)
            self.rfile.read(int(self.headers["Content-Length"]))
            seen.set()
            if mode == "retry":
                self.send_response(503)
                self.send_header("Retry-After", "2")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", "100000")
            self.end_headers()
            if mode == "trickle":
                with suppress(BrokenPipeError, ConnectionResetError):
                    while not stop.wait(0.01):
                        self.wfile.write(b" ")
                        self.wfile.flush()
            else:
                stop.wait(15)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/v1", seen, calls
    finally:
        stop.set()
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.mark.parametrize("mode", ["blocked", "trickle", "retry"])
def test_real_sdk_blocked_read_trickle_and_retry_backoff_are_stopped_locally(tmp_path, mode):
    marker = tmp_path / "child"
    clock = [0]
    with local_provider(mode) as (url, seen, calls):
        def check():
            if seen.is_set():
                clock[0] = 31

        observer = ResearchObserver(check_cancelled=check, emit=lambda *_: None,
            clock=lambda: clock[0], max_seconds=30)
        engine = SupervisedAnalysisEngine(base_config={"marker": str(marker),
            "mode": "http", "url": url}, engine_factory=SpawnFixtureEngine)
        with pytest.raises(ResearchBudgetExceeded):
            engine.analyze(request_with(observer))
        assert seen.is_set() and len(calls) == 1
        assert_child_stopped(marker)
        sleep(0.05)
        assert len(calls) == 1  # No locally detached retry after child termination.
        assert observer.receipt()["usage"]["failed_calls"] == 1
