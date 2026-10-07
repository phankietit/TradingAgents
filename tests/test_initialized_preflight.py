"""Native spawn identity and failure refusal, genuine SDKs with no requests."""

import asyncio
import multiprocessing
import threading
from decimal import Decimal
from time import sleep
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

import httpx
import openai
import pytest

from tests.test_recovery_fingerprint import inputs
from tests.test_risk_engine import _policy, _portfolio
from tradingagents.graph import trading_graph
from tradingagents.llm_clients.openai_client import NormalizedChatOpenAI
from tradingagents.platform.analysis import initialized_preflight as probe
from tradingagents.platform.analysis.observer import ResearchBudgetExceeded, ResearchObserver
from tradingagents.portfolio import PortfolioContext


def _forbidden(*args, **kwargs):
    raise AssertionError("preflight attempted model/network invocation")


def _exercise_child(connection, raw, case):
    models, attempts = [], []
    factory = trading_graph.create_llm_client
    original_close = openai.OpenAI.close
    failed = False

    def capture(**kwargs):
        wrapped = factory(**kwargs)

        def get_llm():
            attempts.append(True)
            if case == "partial" and len(attempts) == 2:
                raise RuntimeError("NEVER_ECHO")
            llm = wrapped.get_llm()
            models.append(llm)
            return llm

        return SimpleNamespace(get_llm=get_llm)

    def bad_close(client):
        nonlocal failed
        if models and client is models[0].root_client and not failed:
            failed = True
            raise RuntimeError("NEVER_ECHO")
        return original_close(client)

    with (patch.object(httpx.Client, "send", _forbidden),
          patch.object(httpx.AsyncClient, "send", _forbidden),
          patch.object(NormalizedChatOpenAI, "invoke", _forbidden),
          patch.object(trading_graph, "create_llm_client", capture)):
        if case == "oversize":
            connection.send_bytes(b"x" * (probe.MAX_REPLY_BYTES + 1))
            connection.close()
            return
        if case == "duplicate":
            connection.send_bytes(b'{"fingerprint":"a","fingerprint":"b","nodes":[]}')
            connection.close()
            return
        if case == "hang":
            sleep(60)
            return
        if case == "parent_loss":
            with patch.object(probe, "parent_process", lambda: SimpleNamespace(is_alive=lambda: False)):
                probe._preflight_child(connection, raw)
            raise AssertionError("lost-parent child should exit without a reply")
        if case == "cleanup":
            with patch.object(openai.OpenAI, "close", bad_close):
                probe._preflight_child(connection, raw)
            assert failed
        else:
            probe._preflight_child(connection, raw)
        assert len(models) == (1 if case == "partial" else 2)
        assert all(model.root_client.is_closed() and model.root_async_client.is_closed() for model in models)


class _NativeContext:
    def __init__(self, case):
        self.actual = multiprocessing.get_context("spawn")
        self.case = case
        self.children = []

    def Pipe(self, **kwargs):
        return self.actual.Pipe(**kwargs)

    def Process(self, *, target, args, daemon):
        assert target is probe._preflight_child
        child = self.actual.Process(target=_exercise_child, args=(*args, self.case), daemon=daemon)
        self.children.append(child)
        return child


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-only")
    args = inputs()
    args.pop("client_binding")
    # Each parent SDK is deliberately open and has exactly its child's settings.
    # A unique endpoint avoids closed pools left by unrelated earlier tests.
    endpoint = "https://example.test/v1/" + uuid4().hex
    args["base_config"].update(backend_url=endpoint, data_cache_dir=str(tmp_path / "cache"),
                               results_dir=str(tmp_path / "results"))
    observer = ResearchObserver(check_cancelled=lambda: None, emit=lambda *args: None)
    return args, observer


def _assert_reaped(context):
    for child in context.children:
        # Closed Process handles prove parent cleanup reached process.close().
        with pytest.raises(ValueError, match="closed"):
            child.is_alive()
    assert not any(t.name == "preflight-pipe-reader" for t in threading.enumerate())


def test_two_native_preflights_retain_original_identity_and_parent_sdk(setup, monkeypatch):
    args, observer = setup
    args["request"] = args["request"].model_copy(update={"execution_observer": observer})
    context = _NativeContext("success")
    monkeypatch.setattr(probe, "get_context", lambda mode: context)
    borrowed = NormalizedChatOpenAI(model="quick", api_key="synthetic-only",
        base_url=args["base_config"]["backend_url"], timeout=600, max_retries=1)
    try:
        first = probe.prepare_recording_identity(observer=observer, **args)
        second = probe.prepare_recording_identity(observer=observer, **args)
        assert first == second and len(first.fingerprint) == 64
        assert "Portfolio Manager" in first.nodes and "Market Analyst" in first.nodes
        assert not borrowed.root_client.is_closed() and not borrowed.root_async_client.is_closed()
        assert observer.started_calls == 0 and not any(observer.usage.values())
        _assert_reaped(context)
    finally:
        borrowed.root_client.close()
        asyncio.run(borrowed.root_async_client.close())


def test_native_transfer_binds_original_precise_book_and_policy(setup, monkeypatch):
    args, observer = setup
    context = _NativeContext("success")
    monkeypatch.setattr(probe, "get_context", lambda mode: context)
    book = _portfolio(args["owner_id"], args["run"].instrument_id)
    policy = _policy(args["owner_id"])
    args["run"] = args["run"].model_copy(update={"decision_inputs":
        args["run"].decision_inputs.model_copy(update={"portfolio_snapshot_id": book.portfolio_id,
            "policy_id": policy.policy_id, "policy_version": policy.policy_version,
            "requested_target_weight": .4})})
    args["request"] = args["request"].model_copy(update={"portfolio": PortfolioContext(cash=600, currency="USD")})
    args["portfolio_snapshot"], args["policy"] = book, policy
    first = probe.prepare_recording_identity(observer=observer, **args)
    # A value difference below a floating-point ULP must not disappear in JSON.
    cash = book.cash[0].model_copy(update={"amount": Decimal("600.000000000000000001")})
    args["portfolio_snapshot"] = book.model_copy(update={"cash": (cash, *book.cash[1:])})
    second = probe.prepare_recording_identity(observer=observer, **args)
    assert first.fingerprint != second.fingerprint
    _assert_reaped(context)


@pytest.mark.parametrize("case", ["partial", "cleanup", "oversize", "duplicate", "parent_loss"])
def test_native_failure_withholds_identity_reaps_child_and_reader(setup, monkeypatch, case):
    args, observer = setup
    context = _NativeContext(case)
    monkeypatch.setattr(probe, "get_context", lambda mode: context)
    with pytest.raises(probe.InitializedPreflightError) as raised:
        probe.prepare_recording_identity(observer=observer, **args)
    assert str(raised.value) == "initialized recording preflight requires review"
    assert raised.value.__cause__ is None
    assert observer.started_calls == 0
    _assert_reaped(context)


def test_child_startup_consumes_original_observer_budget_and_reaps(setup, monkeypatch):
    args, observer = setup
    context = _NativeContext("hang")
    monkeypatch.setattr(probe, "get_context", lambda mode: context)
    observer.max_seconds = 1
    with pytest.raises(ResearchBudgetExceeded):
        probe.prepare_recording_identity(observer=observer, **args)
    assert observer.started_calls == 0
    _assert_reaped(context)


def test_preflight_own_deadline_reaps_without_replenishing_observer(setup, monkeypatch):
    args, observer = setup
    context = _NativeContext("hang")
    monkeypatch.setattr(probe, "get_context", lambda mode: context)
    monkeypatch.setattr(probe, "PREFLIGHT_SECONDS", 0.2)
    with pytest.raises(probe.InitializedPreflightError):
        probe.prepare_recording_identity(observer=observer, **args)
    assert observer.started_calls == 0 and observer.remaining_seconds() < observer.max_seconds
    _assert_reaped(context)


def test_cancellation_after_spawn_reaps_and_preserves_original_error(setup, monkeypatch):
    args, observer = setup
    context = _NativeContext("hang")
    monkeypatch.setattr(probe, "get_context", lambda mode: context)
    checks = []

    def cancel():
        checks.append(True)
        if len(checks) >= 4:
            raise RuntimeError("synthetic owner cancellation")

    observer.check_cancelled = cancel
    with pytest.raises(RuntimeError, match="synthetic owner cancellation"):
        probe.prepare_recording_identity(observer=observer, **args)
    assert len(context.children) == 1
    _assert_reaped(context)


@pytest.mark.parametrize("mutation", ["provider", "secret", "graph", "no_snapshot", "owner_observer", "nonfinite", "oversize", "foreign_observer"])
def test_invalid_parent_setup_refuses_without_spawning(setup, monkeypatch, mutation):
    args, observer = setup
    monkeypatch.setattr(probe, "get_context", _forbidden)
    if mutation == "provider":
        args["base_config"]["llm_provider"] = "anthropic"
    elif mutation == "secret":
        args["base_config"]["api_key"] = "NEVER_ECHO"
    elif mutation == "graph":
        args["graph"] = object()
    elif mutation == "no_snapshot":
        args["request"] = args["request"].model_copy(update={"snapshot_context": None})
    elif mutation == "nonfinite":
        args["base_config"]["temperature"] = float("nan")
    elif mutation == "oversize":
        monkeypatch.setattr(probe, "MAX_RECORDING_CONTEXT_BYTES", 100)
    elif mutation == "foreign_observer":
        args["request"] = args["request"].model_copy(update={"execution_observer": object()})
    else:
        observer = object()
    with pytest.raises(probe.InitializedPreflightError, match="^initialized recording preflight requires review$"):
        probe.prepare_recording_identity(observer=observer, **args)


def test_parent_cancellation_remains_original_error_and_never_spawns(setup, monkeypatch):
    args, observer = setup
    monkeypatch.setattr(probe, "get_context", _forbidden)

    def cancel():
        raise RuntimeError("synthetic owner cancellation")

    observer.check_cancelled = cancel
    with pytest.raises(RuntimeError, match="synthetic owner cancellation"):
        probe.prepare_recording_identity(observer=observer, **args)


def test_running_event_loop_refuses_before_process_allocation(setup, monkeypatch):
    args, observer = setup
    monkeypatch.setattr(probe, "get_context", _forbidden)

    async def call():
        with pytest.raises(probe.InitializedPreflightError):
            probe.prepare_recording_identity(observer=observer, **args)

    asyncio.run(call())
