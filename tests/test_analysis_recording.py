"""Original AnalysisEngine wiring with real SDK construction, no provider calls."""

from uuid import uuid4

import pytest

from tests import test_initialized_graph_fingerprint as bindings
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.platform.analysis import AnalysisEngine
from tradingagents.platform.analysis.checkpoint_saver import CommittedSnapshotSaver
from tradingagents.platform.analysis.client_binding import build_initialized_graph_fingerprint
from tradingagents.platform.analysis.observer import ResearchBudgetExceeded, ResearchObserver
from tradingagents.platform.analysis.recording import SnapshotRecorder
from tradingagents.platform.analysis.recovery_fingerprint import RecoveryFingerprintError

initialized = bindings.initialized


def recorder(args, graph, **updates):
    if args["request"].execution_observer is None:
        args["request"] = args["request"].model_copy(update={"execution_observer": ResearchObserver(
            check_cancelled=lambda: None, emit=lambda *args: None)})
    values = {"owner_id": args["owner_id"], "run": args["run"],
              "expected_fingerprint": build_initialized_graph_fingerprint(graph=graph, **args),
              "commit": lambda raw: (_ for _ in ()).throw(AssertionError("unexpected commit"))}
    values.update(updates)
    return SnapshotRecorder(**values)


@pytest.mark.parametrize("field,value", [("owner_id", uuid4()), ("expected_fingerprint", "NEVER_ECHO"),
    ("expected_fingerprint", None), ("commit", None)])
def test_invalid_setup_has_fixed_nonprivate_diagnostic(initialized, field, value):
    args, graph = initialized
    with pytest.raises(RecoveryFingerprintError) as raised:
        recorder(args, graph, **{field: value})
    assert str(raised.value) == "invalid snapshot recorder setup"
    assert raised.value.__cause__ is None


def test_recorder_factory_restriction_before_graph_initialization(initialized):
    args, graph = initialized
    with pytest.raises(ValueError, match="invalid analysis recorder configuration"):
        AnalysisEngine(snapshot_recorder=recorder(args, graph), graph_factory=object)
    with pytest.raises(ValueError, match="invalid analysis recorder configuration"):
        AnalysisEngine(snapshot_recorder=object())


def test_non_snapshot_request_cannot_enter_recording_graph(initialized):
    args, graph = initialized
    engine = AnalysisEngine(base_config=args["base_config"], snapshot_recorder=recorder(args, graph))
    request = args["request"].model_copy(update={"snapshot_context": None})
    with pytest.raises(ValueError, match="snapshot recorder requires snapshot research"):
        engine.analyze(request)


@pytest.mark.parametrize("match", [True, False])
def test_original_engine_prepares_actual_graph_before_invocation(initialized, monkeypatch, match):
    args, graph = initialized
    configured = recorder(args, graph, **({} if match else {"expected_fingerprint": "0" * 64}))
    constructed = []
    invoked = []
    original_init = TradingAgentsGraph.__init__

    def initialize(instance, *values, **options):
        original_init(instance, *values, **options)
        constructed.append(instance)

    def invocation(instance, *values, **options):
        invoked.append((instance, values, options))
        return {}, "REVIEW"

    monkeypatch.setattr(TradingAgentsGraph, "__init__", initialize)
    # Explicit wiring spy, not native full-flow or financial acceptance.
    monkeypatch.setattr(TradingAgentsGraph, "propagate_snapshots", invocation)
    engine = AnalysisEngine(base_config=args["base_config"], snapshot_recorder=configured)
    try:
        if match:
            result = engine.analyze(args["request"])
            assert result.decision_payload is None and result.narrative_signal == "REVIEW"
            assert len(invoked) == 1
            instance, _, options = invoked[0]
            assert instance is constructed[0] and instance is not graph
            saver = options["checkpoint_saver"]
            assert type(saver) is CommittedSnapshotSaver
            assert saver.codec.fingerprint == configured.expected_fingerprint
            assert options["checkpoint_thread_id"] == str(args["run"].run_id)
        else:
            with pytest.raises(RecoveryFingerprintError, match="snapshot recorder identity requires review"):
                engine.analyze(args["request"])
            assert not invoked
    finally:
        import asyncio

        for instance in constructed:
            for llm in (instance.quick_thinking_llm, instance.deep_thinking_llm):
                llm.root_client.close()
                asyncio.run(llm.root_async_client.close())


def test_context_repr_does_not_echo_private_original_inputs(initialized):
    args, graph = initialized
    configured = recorder(args, graph)
    assert str(args["owner_id"]) not in repr(configured)
    assert str(args["run"].run_id) not in repr(configured)
    assert configured.expected_fingerprint not in repr(configured)


@pytest.mark.parametrize("mutation", ["missing", "wall", "calls", "exhausted"])
def test_original_allowance_is_required_and_never_reset(initialized, mutation):
    args, graph = initialized
    configured = recorder(args, graph)
    observer = args["request"].execution_observer
    started = observer.started
    if mutation == "missing":
        args["request"] = args["request"].model_copy(update={"execution_observer": None})
    elif mutation == "wall":
        observer.max_seconds += 1
    elif mutation == "calls":
        observer.max_calls += 1
    else:
        observer.clock = lambda: started + observer.max_seconds + 1
    expected = ResearchBudgetExceeded if mutation == "exhausted" else RecoveryFingerprintError
    with pytest.raises(expected):
        configured.prepare(request=args["request"], graph=graph, base_config=args["base_config"])
    assert observer.started == started and observer.started_calls == 0
