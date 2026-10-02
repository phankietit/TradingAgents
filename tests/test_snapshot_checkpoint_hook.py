"""Internal graph recording hook: no providers or private runtime state."""

from contextlib import nullcontext
from types import SimpleNamespace
from uuid import uuid4

import pytest
from langgraph.checkpoint.memory import InMemorySaver

from tests.test_snapshot_checkpoint_codec import checkpoint
from tradingagents.graph.propagation import Propagator
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.platform.analysis.checkpoint_codec import SnapshotCheckpointCodec
from tradingagents.platform.analysis.checkpoint_saver import CommittedSnapshotSaver


def graph_fixture(*, failure=False):
    graph = object.__new__(TradingAgentsGraph)
    graph.snapshot_mode = True
    graph.config_scope = nullcontext
    graph.propagator = Propagator(123)
    graph.execution_observer = object()
    calls = []

    def invoke(state, **options):
        calls.append((state, options))
        if failure:
            raise ValueError("commit requires review")
        return {"structured_decision": {"rating": "Hold"}}

    original = SimpleNamespace(invoke=invoke)
    graph.graph = original
    compiled = []

    def compile(**options):
        compiled.append(options)
        return SimpleNamespace(invoke=invoke)

    graph.workflow = SimpleNamespace(compile=compile)
    return graph, original, calls, compiled


def run(graph, **options):
    return graph.propagate_snapshots("BTC-USD", "2026-01-01",
        asset_type="crypto", instrument_context="Verified snapshot", **options)


@pytest.mark.parametrize("failure", [False, True])
def test_internal_hook_uses_sync_and_does_not_replace_instance_graph(failure):
    graph, original, calls, compiled = graph_fixture(failure=failure)
    saver = InMemorySaver()
    thread = str(uuid4())
    if failure:
        with pytest.raises(ValueError, match="commit requires review"):
            run(graph, checkpoint_saver=saver, checkpoint_thread_id=thread)
    else:
        assert run(graph, checkpoint_saver=saver, checkpoint_thread_id=thread)[1] == "Hold"
    assert graph.graph is original
    assert compiled == [{"checkpointer": saver}]
    state, options = calls[0]
    assert state["research_only"] is True
    assert state["past_context"] == ""
    assert options["durability"] == "sync"
    assert options["config"] == {"recursion_limit": 123,
        "callbacks": [graph.execution_observer], "configurable": {"thread_id": thread}}


@pytest.mark.parametrize("saver,thread", [(None, str(uuid4())), (InMemorySaver(), None),
    (object(), str(uuid4())), (InMemorySaver(), "PRIVATE_BAD_THREAD"),
    (InMemorySaver(), uuid4()), (InMemorySaver(), "AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA")])
def test_incomplete_or_invalid_hook_rejected_before_compile_or_invoke(saver, thread):
    graph, original, calls, compiled = graph_fixture()
    with pytest.raises(ValueError) as error:
        run(graph, checkpoint_saver=saver, checkpoint_thread_id=thread)
    assert str(error.value) == "invalid snapshot checkpoint setup"
    assert not compiled and not calls
    assert graph.graph is original


def test_default_snapshot_path_keeps_original_invocation():
    graph, original, calls, compiled = graph_fixture()
    run(graph)
    assert not compiled and graph.graph is original
    assert "durability" not in calls[0][1]
    assert "configurable" not in calls[0][1]["config"]


def test_non_snapshot_graph_rejects_hook_before_any_invocation():
    graph, original, calls, compiled = graph_fixture()
    graph.snapshot_mode = False
    with pytest.raises(ValueError, match="snapshot propagation requires"):
        run(graph, checkpoint_saver=InMemorySaver(), checkpoint_thread_id=str(uuid4()))
    assert not compiled and not calls
    assert graph.graph is original


def test_restored_hook_uses_native_none_input_sync_and_original_callbacks():
    graph, original, calls, compiled = graph_fixture()
    thread = str(uuid4())
    codec = SnapshotCheckpointCodec(fingerprint="a" * 64, nodes={"Market Analyst"})
    value = checkpoint()
    value.config["configurable"]["thread_id"] = thread
    value.metadata["thread_id"] = thread
    saver = CommittedSnapshotSaver(codec=codec, commit=lambda raw: None)
    saver.restore(codec.encode(value), expected_thread_id=thread)
    run(graph, checkpoint_saver=saver, checkpoint_thread_id=thread, checkpoint_resume=True)
    assert graph.graph is original
    assert compiled == [{"checkpointer": saver}]
    assert calls[0][0] is None
    assert calls[0][1]["durability"] == "sync"
    assert calls[0][1]["config"]["callbacks"] == [graph.execution_observer]


@pytest.mark.parametrize("resume,saver", [(True, None), (True, InMemorySaver()),
    (1, None), ("true", None)])
def test_invalid_resume_rejected_before_compile_or_invocation(resume, saver):
    graph, original, calls, compiled = graph_fixture()
    with pytest.raises(ValueError, match="invalid snapshot checkpoint setup"):
        run(graph, checkpoint_resume=resume,
            **({"checkpoint_saver": saver, "checkpoint_thread_id": str(uuid4())} if saver else {}))
    assert not calls and not compiled and graph.graph is original
