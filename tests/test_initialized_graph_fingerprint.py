"""Real graph and SDK construction with synthetic credentials, never invoke."""

import asyncio
import hashlib
from copy import deepcopy
from uuid import uuid4

import httpx
import pytest

from tests.test_recovery_fingerprint import inputs
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.llm_clients.openai_client import NormalizedChatOpenAI
from tradingagents.platform.analysis.client_binding import (
    bind_initialized_clients,
    build_initialized_graph_fingerprint,
)
from tradingagents.platform.analysis.recovery_fingerprint import (
    RecoveryFingerprintError,
    build_recovery_fingerprint,
)


@pytest.fixture
def initialized(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("identity guard attempted model/network invocation")

    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-NEVER_ECHO")
    monkeypatch.setattr(httpx.Client, "send", forbidden)
    monkeypatch.setattr(httpx.AsyncClient, "send", forbidden)
    monkeypatch.setattr(NormalizedChatOpenAI, "invoke", forbidden)
    args = inputs()
    args.pop("client_binding")
    args["base_config"].update(data_cache_dir=str(tmp_path / "cache"), results_dir=str(tmp_path / "results"))
    request = args["request"]
    graph = TradingAgentsGraph(config=args["base_config"], selected_analysts=request.selected_analysts,
        snapshot_reports=request.snapshot_context.reports(request.instrument.instrument_id, request.selected_analysts))
    try:
        yield args, graph
    finally:
        for llm in (graph.quick_thinking_llm, graph.deep_thinking_llm):
            llm.root_client.close()
            asyncio.run(llm.root_async_client.close())


def test_real_graph_clients_supply_full_original_identity_without_invoke(initialized):
    args, graph = initialized
    actual = build_initialized_graph_fingerprint(graph=graph, **args)
    binding = bind_initialized_clients(quick=graph.quick_thinking_llm, deep=graph.deep_thinking_llm)
    assert actual == build_recovery_fingerprint(**args, client_binding=binding)
    assert len(actual) == 64 and "NEVER_ECHO" not in actual
    assert graph.memory_log is None and graph.tool_nodes == {}


@pytest.mark.parametrize("mutation", ["config", "roles", "quick_model", "deep_model", "mode",
    "owner", "source", "run_model", "endpoint", "client_class"])
def test_mismatch_rejected_before_any_invocation(initialized, mutation):
    args, graph = initialized
    if mutation == "config":
        graph.config["max_debate_rounds"] += 1
    elif mutation == "roles":
        graph.selected_analysts = ("news",)
    elif mutation in {"quick_model", "deep_model"}:
        llm = graph.quick_thinking_llm if mutation == "quick_model" else graph.deep_thinking_llm
        llm.model_name = "NEVER_ECHO"
    elif mutation == "mode":
        graph.snapshot_mode = False
    elif mutation == "owner":
        args["owner_id"] = uuid4()
    elif mutation == "source":
        source = args["request"].snapshot_context.by_analyst["market"][0]
        args["request"].snapshot_context.by_analyst["market"] = (source.model_copy(update={"payload": "NEVER_ECHO"}),)
    elif mutation == "run_model":
        args["run"] = args["run"].model_copy(update={"quick_model": "NEVER_ECHO"})
    elif mutation == "endpoint":
        graph.deep_thinking_llm.root_client.base_url = "https://other.test/v1/"
    else:
        class Unreviewed(type(graph)):
            pass
        graph.__class__ = Unreviewed
    with pytest.raises(RecoveryFingerprintError) as raised:
        build_initialized_graph_fingerprint(graph=graph, **args)
    assert str(raised.value) == "initialized graph recovery identity is incompatible"
    assert raised.value.__cause__ is None


def test_actual_sdk_option_change_changes_identity_not_declared_config(initialized):
    args, graph = initialized
    original = build_initialized_graph_fingerprint(graph=graph, **args)
    config = deepcopy(graph.config)
    graph.deep_thinking_llm.root_client.max_retries = 2
    assert build_initialized_graph_fingerprint(graph=graph, **args) != original
    assert graph.config == config


def test_non_graph_cannot_supply_precomputed_descriptor(initialized):
    args, _ = initialized
    with pytest.raises(RecoveryFingerprintError, match="initialized graph recovery identity is incompatible"):
        build_initialized_graph_fingerprint(graph=object(), **args)


def test_valid_rehashed_source_still_must_match_actual_graph_readers(initialized):
    args, graph = initialized
    source = args["request"].snapshot_context.by_analyst["market"][0]
    payload = '{"close": 999}'
    changed = source.model_copy(update={"payload": payload, "manifest": source.manifest.model_copy(
        update={"content_hash": "sha256:" + hashlib.sha256(payload.encode()).hexdigest()})})
    args["request"].snapshot_context.by_analyst["market"] = (changed,)
    with pytest.raises(RecoveryFingerprintError, match="initialized graph recovery identity is incompatible"):
        build_initialized_graph_fingerprint(graph=graph, **args)
