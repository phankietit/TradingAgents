"""Original-attempt recording factory, no dispatch or consent authority."""

from collections.abc import Mapping
from copy import deepcopy

from tradingagents.contracts.runs import ResearchExecutionLimits
from tradingagents.platform.analysis.checkpoint_codec import SnapshotCheckpointCodec
from tradingagents.platform.analysis.checkpoint_store import PrivateCheckpointStore
from tradingagents.platform.analysis.engine import AnalysisEngine
from tradingagents.platform.analysis.initialized_preflight import prepare_recording_identity
from tradingagents.platform.analysis.observer import ResearchObserver
from tradingagents.platform.analysis.recording_context import SnapshotRecordingInputs
from tradingagents.platform.analysis.supervision import SupervisedAnalysisEngine
from tradingagents.platform.jobs.worker import JobExecutionContext


def build_recorded_engine(*, template, context, run, request, observer,
                          portfolio_snapshot=None, policy=None, risk_snapshots=()):
    """Trusted handler must already load/authenticate original owner inputs.

    One fresh original attempt only: no linked/restore mode, fallback, shared
    engine mutation, new observer, CLI path or model invocation in this factory.
    """
    limits = run.execution_limits or ResearchExecutionLimits()
    if (type(template) is not SupervisedAnalysisEngine or template.engine_factory is not AnalysisEngine
            or not isinstance(template.base_config, Mapping)
            or any(getattr(template, field) is not None for field in (
                "checkpoint_options", "checkpoint_codec", "checkpoint_commit", "recording_inputs",
                "restore_checkpoint", "linked_context"))
            or type(context) is not JobExecutionContext or type(observer) is not ResearchObserver
            or request.execution_observer is not observer
            or getattr(observer.check_cancelled, "__self__", None) is not context
            or getattr(observer.check_cancelled, "__func__", None) is not JobExecutionContext.raise_if_cancelled
            or request.snapshot_context is None):
        raise ValueError("original recording setup requires review")
    with observer.lock:
        if (observer.max_seconds != limits.wall_seconds or observer.max_calls != limits.model_calls
                or observer.started_calls or any(observer.usage.values())
                or observer.active or observer.completed or observer.seen_model_runs
                or observer._retained_elapsed_seconds or observer._retained_started_calls
                or observer._execution_stopped):
            raise ValueError("original recording allowance requires review")
    base_config = deepcopy(dict(template.base_config))
    observer.remaining_seconds()
    identity = prepare_recording_identity(observer=observer, owner_id=run.owner_id,
        run=run, request=request, base_config=base_config, portfolio_snapshot=portfolio_snapshot,
        policy=policy, risk_snapshots=risk_snapshots)
    observer.remaining_seconds()
    codec = SnapshotCheckpointCodec(fingerprint=identity.fingerprint, nodes=identity.nodes)
    inputs = SnapshotRecordingInputs.create(owner_id=run.owner_id, run=run,
        expected_fingerprint=identity.fingerprint, portfolio_snapshot=portfolio_snapshot,
        policy=policy, risk_snapshots=risk_snapshots)
    inputs.validate_request(request)
    store = PrivateCheckpointStore(codec=codec)

    def commit(raw):
        # Existing publication_session/DB ACK and original observer remain the
        # parent authority. A late committed ACK is withheld, not refunded.
        remaining = observer.remaining_seconds()
        receipt = store.commit(context=context, owner_id=run.owner_id, run_id=run.run_id,
            raw=raw, lock_timeout_seconds=min(5.0, remaining))
        observer.remaining_seconds()
        return receipt

    return SupervisedAnalysisEngine(base_config=base_config, checkpoint_codec=codec,
        checkpoint_thread_id=str(run.run_id), checkpoint_commit=commit, recording_inputs=inputs)
