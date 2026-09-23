"""Per-run configuration must be isolated for concurrent platform workers."""

from __future__ import annotations

import asyncio
import copy
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager

import pytest

import tradingagents.default_config as default_config
from tradingagents.dataflows.config import config_scope, get_config, set_config
from tradingagents.graph.trading_graph import TradingAgentsGraph


@pytest.mark.unit
def test_config_scope_isolated_across_concurrent_workers():
    barrier = threading.Barrier(2)

    def observe(provider: str, language: str) -> tuple[str, str]:
        with config_scope({"llm_provider": provider, "output_language": language}):
            barrier.wait(timeout=5)
            active = get_config()
            return active["llm_provider"], active["output_language"]

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(observe, "openai", "English")
        second = pool.submit(observe, "google", "Vietnamese")

    assert first.result() == ("openai", "English")
    assert second.result() == ("google", "Vietnamese")


@pytest.mark.unit
def test_config_scope_isolated_across_async_tasks():
    async def observe(provider: str) -> str:
        with config_scope({"llm_provider": provider}):
            await asyncio.sleep(0)
            return get_config()["llm_provider"]

    async def run_both() -> list[str]:
        return await asyncio.gather(observe("openai"), observe("google"))

    assert asyncio.run(run_both()) == ["openai", "google"]


@pytest.mark.unit
def test_config_scope_restores_previous_scope_after_exception():
    set_config({"output_language": "English"})

    with (
        pytest.raises(RuntimeError, match="stop"),
        config_scope({"output_language": "Vietnamese"}),
    ):
        assert get_config()["output_language"] == "Vietnamese"
        raise RuntimeError("stop")

    assert get_config()["output_language"] == "English"


@pytest.mark.unit
def test_scoped_config_inherits_defaults_not_mutable_process_config():
    set_config({"data_vendors": {"core_stock_apis": "alpha_vantage"}})

    with config_scope({"output_language": "Vietnamese"}):
        active = get_config()

    assert active["output_language"] == "Vietnamese"
    assert active["data_vendors"]["core_stock_apis"] == "yfinance"


@pytest.mark.unit
def test_graph_owns_config_copy_and_does_not_publish_it_globally(tmp_path, mock_llm_client):
    baseline = get_config()
    supplied = copy.deepcopy(default_config.DEFAULT_CONFIG)
    supplied.update(
        {
            "output_language": "Vietnamese",
            "data_cache_dir": str(tmp_path / "cache"),
            "results_dir": str(tmp_path / "results"),
            "memory_log_path": str(tmp_path / "memory.md"),
        }
    )

    graph = TradingAgentsGraph(selected_analysts=("market",), config=supplied)
    supplied["output_language"] = "English"

    assert graph.config["output_language"] == "Vietnamese"
    assert get_config() == baseline
    with graph.config_scope():
        assert get_config()["output_language"] == "Vietnamese"
    assert get_config() == baseline


@pytest.mark.unit
def test_propagate_activates_the_owning_graph_config():
    graph = object.__new__(TradingAgentsGraph)
    graph.config = {"output_language": "Vietnamese"}

    @contextmanager
    def checkpoint_scope(*args, **kwargs):
        yield None

    graph.checkpoint_scope = checkpoint_scope
    graph._run_graph = lambda *args, **kwargs: get_config()["output_language"]

    assert graph.propagate("AAPL", "2026-09-01") == "Vietnamese"
