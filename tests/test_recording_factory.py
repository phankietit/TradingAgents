"""Factory proof; native identity, mocked lease and commit boundaries."""

from datetime import timedelta
from uuid import uuid4

import pytest

from tests.test_initialized_preflight import _assert_reaped, _NativeContext
from tests.test_recovery_fingerprint import inputs
from tests.test_risk_engine import NOW
from tradingagents.platform.analysis import initialized_preflight, recording_factory as factory
from tradingagents.platform.analysis.checkpoint_store import CheckpointCommit
from tradingagents.platform.analysis.initialized_preflight import PreparedRecordingIdentity
from tradingagents.platform.analysis.observer import ResearchBudgetExceeded, ResearchObserver
from tradingagents.platform.analysis.supervision import SupervisedAnalysisEngine
from tradingagents.platform.jobs.worker import JobExecutionContext


@pytest.fixture
def setup(tmp_path, monkeypatch):
    args = inputs()
    args.pop("client_binding")
    args.pop("owner_id")
    args["base_config"].update(data_cache_dir=str(tmp_path / "cache"), results_dir=str(tmp_path / "reports"))
    template = SupervisedAnalysisEngine(base_config=args.pop("base_config"))
    # This diagnostic does not prove a real DB/lease or owner authorization.
    monkeypatch.setattr(JobExecutionContext, "raise_if_cancelled", lambda self: None)
    context = JobExecutionContext(None, uuid4(), "synthetic-worker", timedelta(minutes=5), lambda: NOW)
    observer = ResearchObserver(check_cancelled=context.raise_if_cancelled, emit=lambda *args: None)
    args["request"] = args["request"].model_copy(update={"execution_observer": observer})
    return dict(args, template=template, context=context, observer=observer)


def test_native_factory_creates_per_run_binding_without_mutating_template(setup, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-only")
    native = _NativeContext("success")
    monkeypatch.setattr(initialized_preflight, "get_context", lambda mode: native)
    result = factory.build_recorded_engine(**setup)
    original = setup["template"]
    assert result is not original and original.checkpoint_options is None
    assert original.recording_inputs is None and original.checkpoint_commit is None
    assert result.recording_inputs.validate_request(setup["request"]).run == setup["run"]
    assert result.checkpoint_options["thread_id"] == str(setup["run"].run_id)
    assert result.checkpoint_options["fingerprint"] == result.recording_inputs.read().expected_fingerprint
    assert result.restore_checkpoint is None and result.linked_context is None
    assert setup["observer"].started_calls == 0
    _assert_reaped(native)


@pytest.mark.parametrize("mutation", ["template", "configured", "context", "observer", "calls", "budget", "retained", "source", "request_observer"])
def test_staged_factory_refuses_unsafe_setup_before_preflight(setup, monkeypatch, mutation):
    def forbidden(**kwargs):
        pytest.fail("unsafe factory reached client preflight")
    monkeypatch.setattr(factory, "prepare_recording_identity", forbidden)
    if mutation == "template":
        setup["template"] = object()
    elif mutation == "configured":
        setup["template"].checkpoint_options = {"fingerprint": "a" * 64}
    elif mutation == "context":
        setup["context"] = object()
    elif mutation == "observer":
        setup["observer"].check_cancelled = lambda: None
    elif mutation == "calls":
        setup["observer"].started_calls = 1
    elif mutation == "budget":
        setup["observer"].max_calls += 1
    elif mutation == "retained":
        setup["observer"]._retained_elapsed_seconds = 1
    elif mutation == "source":
        setup["request"] = setup["request"].model_copy(update={"snapshot_context": None})
    else:
        setup["request"] = setup["request"].model_copy(update={"execution_observer": object()})
    with pytest.raises(ValueError, match="^original recording (setup|allowance) requires review$"):
        factory.build_recorded_engine(**setup)


def test_checkpoint_callback_retains_original_parent_fence_and_bounded_ack(setup, monkeypatch):
    monkeypatch.setattr(factory, "prepare_recording_identity", lambda **kwargs:
        PreparedRecordingIdentity("a" * 64, ("Market Analyst", "Portfolio Manager")))
    calls = []
    receipt = CheckpointCommit(uuid4(), 1, "b" * 64)

    def commit(store, **kwargs):
        calls.append(kwargs)
        return receipt

    monkeypatch.setattr(factory.PrivateCheckpointStore, "commit", commit)
    engine = factory.build_recorded_engine(**setup)
    assert engine.checkpoint_commit(b"synthetic bytes") is receipt
    assert calls[0]["context"] is setup["context"]
    assert calls[0]["owner_id"] == setup["run"].owner_id
    assert calls[0]["run_id"] == setup["run"].run_id
    assert 0 < calls[0]["lock_timeout_seconds"] <= 5
    assert setup["observer"].started_calls == 0


def test_late_database_ack_is_withheld_without_replenishing_original_budget(setup, monkeypatch):
    monkeypatch.setattr(factory, "prepare_recording_identity", lambda **kwargs:
        PreparedRecordingIdentity("a" * 64, ("Market Analyst", "Portfolio Manager")))
    clock = [0.0]
    observer = setup["observer"]
    observer.clock = lambda: clock[0]
    observer.started = 0.0
    committed = []

    def commit(store, **kwargs):
        committed.append(kwargs)
        clock[0] = observer.max_seconds + 1
        return CheckpointCommit(uuid4(), 1, "b" * 64)

    monkeypatch.setattr(factory.PrivateCheckpointStore, "commit", commit)
    engine = factory.build_recorded_engine(**setup)
    with pytest.raises(ResearchBudgetExceeded):
        engine.checkpoint_commit(b"synthetic bytes")
    assert len(committed) == 1
    assert observer.started == 0.0 and observer.started_calls == 0
