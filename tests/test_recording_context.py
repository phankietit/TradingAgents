"""Internal original-context transfer; no network, paid model or private DB."""

import json
from uuid import uuid4

import pytest

from tests.test_recovery_fingerprint import inputs
from tests.test_risk_engine import _policy, _portfolio
from tests.test_snapshot_checkpoint_codec import checkpoint
from tradingagents.platform.analysis import AnalysisEngine, AnalysisResult
from tradingagents.platform.analysis.checkpoint_codec import SnapshotCheckpointCodec
from tradingagents.platform.analysis.observer import ResearchObserver
from tradingagents.platform.analysis.recording import SnapshotRecorder
from tradingagents.platform.analysis.recording_context import (
    MAX_RECORDING_CONTEXT_BYTES,
    SnapshotRecordingInputs,
)
from tradingagents.platform.analysis.recovery_fingerprint import RecoveryFingerprintError
from tradingagents.platform.analysis.supervision import SupervisedAnalysisEngine, _Bridge, _child


def envelope(args=None, **updates):
    args = args or inputs()
    values = {"owner_id": args["owner_id"], "run": args["run"], "expected_fingerprint": "a" * 64}
    values.update(updates)
    return SnapshotRecordingInputs.create(**values)


def supervisor(args, value, **updates):
    options = {"base_config": args["base_config"], "recording_inputs": value,
        "checkpoint_codec": SnapshotCheckpointCodec(fingerprint="a" * 64, nodes=("market",)),
        "checkpoint_thread_id": str(args["run"].run_id), "checkpoint_commit": lambda raw: None}
    options.update(updates)
    return SupervisedAnalysisEngine(**options)


def restore_bytes(args, *, fingerprint="a" * 64, thread=None):
    value = checkpoint()
    thread = thread or str(args["run"].run_id)
    value.config["configurable"]["thread_id"] = thread
    value.metadata["thread_id"] = thread
    value.checkpoint["versions_seen"] = {"market": {"messages": 1}}
    return SnapshotCheckpointCodec(fingerprint=fingerprint, nodes={"market"}).encode(value)


@pytest.mark.parametrize("failure", ["malformed", "type", "thread", "fingerprint", "context"])
def test_restore_transport_setup_rejects_before_spawn(failure):
    args = inputs()
    raw = restore_bytes(args)
    if failure == "malformed":
        raw = b"PRIVATE_NEVER_ECHO"
    elif failure == "type":
        raw = bytearray(raw)
    elif failure == "thread":
        raw = restore_bytes(args, thread=str(uuid4()))
    elif failure == "fingerprint":
        raw = restore_bytes(args, fingerprint="b" * 64)
    with pytest.raises(ValueError) as raised:
        supervisor(args, None if failure == "context" else envelope(args), restore_checkpoint=raw)
    assert str(raised.value) == "invalid checkpoint bridge configuration"
    assert raised.value.__cause__ is None


def test_restore_transport_revalidated_before_new_process(monkeypatch):
    args = inputs()
    engine = supervisor(args, envelope(args), restore_checkpoint=restore_bytes(args))
    engine.restore_checkpoint = b"PRIVATE_MUTATED_BYTES"
    request = args["request"].model_copy(update={"execution_observer": ResearchObserver(
        check_cancelled=lambda: None, emit=lambda *args: None)})

    def forbidden(*args, **kwargs):
        raise AssertionError("invalid restore spawned a child")

    monkeypatch.setattr("tradingagents.platform.analysis.supervision.get_context", forbidden)
    with pytest.raises(ValueError, match="^invalid checkpoint bridge configuration$"):
        engine.analyze(request)
    assert request.execution_observer.started_calls == 0


def test_json_only_roundtrip_and_nonprivate_repr():
    args = inputs()
    value = envelope(args)
    decoded = value.validate_request(args["request"])
    assert decoded.run == args["run"]
    assert decoded.owner_id == args["owner_id"]
    assert decoded.expected_fingerprint == "a" * 64
    assert str(args["owner_id"]) not in repr(value) + repr(decoded)
    assert str(args["run"].run_id) not in repr(value) + repr(decoded)
    assert "a" * 64 not in repr(value) + repr(decoded)
    assert json.loads(value.raw)["run"]["decision_inputs"]
    # Caller mutation cannot change serialized original inputs.
    args["run"].decision_inputs.source_max_age_seconds["market"] = 100
    assert value.read().run.decision_inputs.source_max_age_seconds == {"market": 0}
    decoded.run.decision_inputs.source_max_age_seconds["market"] = 200
    assert value.read().run.decision_inputs.source_max_age_seconds == {"market": 0}


@pytest.mark.parametrize("updates", [
    {"owner_id": uuid4()}, {"expected_fingerprint": "NEVER_ECHO"},
    {"commit": lambda raw: None}, {"api_key": "NEVER_ECHO"}, {"run": object()},
])
def test_invalid_creation_sanitized(updates):
    with pytest.raises(RecoveryFingerprintError) as raised:
        envelope(**updates)
    assert str(raised.value) == "invalid recording context"
    assert raised.value.__cause__ is None


@pytest.mark.parametrize("raw", [b"", b"NEVER_ECHO", b"x" * (MAX_RECORDING_CONTEXT_BYTES + 1),
                                  "NEVER_ECHO", None])
def test_invalid_wire_rejected_without_echo(raw):
    with pytest.raises(RecoveryFingerprintError, match="^invalid recording context$"):
        SnapshotRecordingInputs(raw).read()


@pytest.mark.parametrize("mutation", ["owner", "error", "missing", "unknown"])
def test_revalidate_wire_not_only_constructor(mutation):
    data = json.loads(envelope().raw)
    if mutation == "owner":
        data["run"]["owner_id"] = str(uuid4())
    elif mutation == "error":
        data["run"]["error_message"] = "PRIVATE_NEVER_ECHO"
    elif mutation == "missing":
        data["run"]["decision_inputs"] = None
    else:
        data["credentials"] = "PRIVATE_NEVER_ECHO"
    with pytest.raises(RecoveryFingerprintError, match="^invalid recording context$"):
        SnapshotRecordingInputs(json.dumps(data).encode()).read()


@pytest.mark.parametrize("raw", [b'{"owner_id": "NEVER_ECHO", "owner_id": null}', b'{"policy": NaN}'])
def test_duplicate_fields_and_nonfinite_json_rejected(raw):
    with pytest.raises(RecoveryFingerprintError, match="^invalid recording context$"):
        SnapshotRecordingInputs(raw).read()


@pytest.mark.parametrize("mutation", [None, "owner", "policy_owner", "credential", "object", "nan"])
def test_full_book_policy_context_and_secret_object_rejection(mutation):
    args = inputs()
    book = _portfolio(args["owner_id"], args["run"].instrument_id)
    policy = _policy(args["owner_id"])
    declared = args["run"].decision_inputs.model_copy(update={"portfolio_snapshot_id": book.portfolio_id,
        "policy_id": policy.policy_id, "policy_version": policy.policy_version, "requested_target_weight": .4})
    args["run"] = args["run"].model_copy(update={"decision_inputs": declared})
    if mutation == "owner":
        book = book.model_copy(update={"owner_id": uuid4()})
    elif mutation == "policy_owner":
        policy = policy.model_copy(update={"owner_id": uuid4()})
    elif mutation == "credential":
        policy.parameters["nested"] = {"api_key": "PRIVATE_NEVER_ECHO"}
    elif mutation == "object":
        policy.parameters["nested"] = object()
    elif mutation == "nan":
        policy.parameters["nested"] = float("nan")
    if mutation is not None:
        with pytest.raises(RecoveryFingerprintError, match="^invalid recording context$"):
            envelope(args, portfolio_snapshot=book, policy=policy)
    else:
        value = envelope(args, portfolio_snapshot=book, policy=policy)
        assert value.read().portfolio_snapshot == book
        assert value.read().policy == policy


@pytest.mark.parametrize("field,value", [
    ("checkpoint_thread_id", str(uuid4())), ("checkpoint_commit", None),
    ("checkpoint_codec", SnapshotCheckpointCodec(fingerprint="b" * 64, nodes=("market",))),
    ("engine_factory", object), ("recording_inputs", object()),
])
def test_parent_requires_complete_exact_original_engine_setup(field, value):
    args = inputs()
    with pytest.raises(ValueError, match="^invalid checkpoint bridge configuration$"):
        supervisor(args, envelope(args), **{field: value})


def test_original_engine_capability_is_not_globally_enabled():
    assert getattr(AnalysisEngine, "supports_checkpoint_bridge", False) is not True
    args = inputs()
    assert supervisor(args, envelope(args)).engine_factory is AnalysisEngine
    with pytest.raises(ValueError, match="^invalid checkpoint bridge configuration$"):
        supervisor(args, None)
    assert SupervisedAnalysisEngine().recording_inputs is None


@pytest.mark.parametrize("mutation", ["date", "roles", "source", "freshness", "missing"])
def test_request_mismatch_rejected_before_spawn(monkeypatch, mutation):
    args = inputs()
    value = envelope(args)
    engine = supervisor(args, value)
    request = args["request"].model_copy(update={"execution_observer": ResearchObserver(
        check_cancelled=lambda: None, emit=lambda *args: None)})
    if mutation == "date":
        from datetime import timedelta

        request = request.model_copy(update={"analysis_date": request.analysis_date + timedelta(days=1)})
    elif mutation == "roles":
        request = request.model_copy(update={"selected_analysts": ("news",)})
    elif mutation == "source":
        source = request.snapshot_context.by_analyst["market"][0]
        request.snapshot_context.by_analyst["market"] = (source.model_copy(update={"payload": "PRIVATE_NEVER_ECHO"}),)
    elif mutation == "freshness":
        request.snapshot_context.source_max_age_seconds["market"] = 100
    else:
        request = request.model_copy(update={"snapshot_context": None})

    def forbidden(*args, **kwargs):
        raise AssertionError("invalid input spawned a child")

    monkeypatch.setattr("tradingagents.platform.analysis.supervision.get_context", forbidden)
    with pytest.raises(ValueError):
        engine.analyze(request)
    assert request.execution_observer.started_calls == 0


def test_child_unit_constructs_exact_recorder_with_bridge_not_parent_objects(monkeypatch):
    # Explicit unit wiring probe, not actual-engine/native-spawn acceptance.
    args = inputs()
    value = envelope(args)
    captured = []
    sent = []

    class Pipe:
        closed = False

        def send(self, message):
            sent.append(message)

        def close(self):
            self.closed = True

    class Probe:
        def __init__(self, *, base_config, snapshot_recorder):
            captured.append((base_config, snapshot_recorder))

        def analyze(self, request):
            configured = captured[0][1]
            assert type(configured) is SnapshotRecorder
            assert type(request.execution_observer) is _Bridge
            assert configured.commit.__self__ is request.execution_observer
            assert configured.run == args["run"]
            assert configured.owner_id == args["owner_id"]
            return AnalysisResult(instrument=request.instrument, analysis_date=request.analysis_date,
                selected_analysts=request.selected_analysts, profile_name="fixture", reference_only=False,
                final_state={}, narrative_signal="REVIEW")

    monkeypatch.setattr("tradingagents.platform.analysis.supervision.AnalysisEngine", Probe)
    pipe = Pipe()
    _child(pipe, args["base_config"], args["request"].model_dump(mode="python"), Probe,
        {"fingerprint": "a" * 64, "thread_id": str(args["run"].run_id)}, value.raw)
    assert len(captured) == 1
    assert len(sent) == 1 and sent[0][0] == "result"
    assert pipe.closed
