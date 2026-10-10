"""Internal linked factory: original inputs, retained observer, no dispatch."""
from collections.abc import Mapping
from copy import deepcopy

from tradingagents.platform.analysis.allowance import validate_retained_observer
from tradingagents.platform.analysis.engine import AnalysisEngine
from tradingagents.platform.analysis.initialized_preflight import prepare_recording_identity
from tradingagents.platform.analysis.linked_publication import LinkedPublicationContext
from tradingagents.platform.analysis.linked_recording import (
    LinkedOriginalResearch,
    validate_linked_recording,
)
from tradingagents.platform.analysis.linked_results import LinkedResultPublisher
from tradingagents.platform.analysis.supervision import SupervisedAnalysisEngine


def build_linked_recorded_engine(*, template, context, original):
    """Trusted parent setup only; no new observer, consent, model or restore call."""
    if (type(template) is not SupervisedAnalysisEngine or template.engine_factory is not AnalysisEngine
            or not isinstance(template.base_config, Mapping)
            or any(getattr(template, field) is not None for field in (
                'checkpoint_options', 'checkpoint_codec', 'checkpoint_commit', 'recording_inputs',
                'restore_checkpoint', 'linked_context'))
            or type(context) is not LinkedPublicationContext
            or type(original) is not LinkedOriginalResearch):
        raise ValueError('linked recording setup requires review')
    publisher = getattr(context, '_result_publisher', None)
    if (type(publisher) is not LinkedResultPublisher or publisher.original is not original
            or publisher._bound() is not context):
        raise ValueError('linked recording publisher requires review')
    observer = context._observer()
    value = validate_linked_recording(context=context, recording_inputs=original.recording_inputs,
                                    request=original.request, restore_checkpoint=original.restore_checkpoint)
    validate_retained_observer(observer=observer, run=value.run)
    base_config = deepcopy(dict(template.base_config))
    identity = prepare_recording_identity(observer=observer, owner_id=value.owner_id, run=value.run,
        request=original.request, base_config=base_config, portfolio_snapshot=value.portfolio_snapshot,
        policy=value.policy, risk_snapshots=value.risk_snapshots)
    observer.remaining_seconds()
    codec = context._store.consents.codec
    if (identity.fingerprint != codec.fingerprint or frozenset(identity.nodes) != codec.nodes):
        raise ValueError('linked recording identity requires review')
    # Reload under the original private lease after constructor/cleanup, before
    # returning setup. Supervision separately consumes one dispatch before spawn.
    validate_linked_recording(context=context, recording_inputs=original.recording_inputs,
                            request=original.request, restore_checkpoint=original.restore_checkpoint)
    validate_retained_observer(observer=observer, run=value.run)
    observer.remaining_seconds()
    return SupervisedAnalysisEngine(base_config=base_config, checkpoint_codec=codec,
        checkpoint_thread_id=str(value.run.run_id), checkpoint_commit=context.commit_checkpoint,
        recording_inputs=original.recording_inputs, restore_checkpoint=original.restore_checkpoint,
        linked_context=context)
