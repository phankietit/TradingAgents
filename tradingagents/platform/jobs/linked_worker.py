"""Execute one durable original continuation; no browser credentials or retries."""

from contextlib import contextmanager
from datetime import datetime
from threading import Event, Thread

from tradingagents._compat import UTC
from tradingagents.platform.analysis.linked_execution import LinkedExecutionStore
from tradingagents.platform.analysis.linked_factory import build_linked_recorded_engine
from tradingagents.platform.analysis.linked_publication import LinkedPublicationContext
from tradingagents.platform.analysis.linked_recording import LinkedOriginalResearch
from tradingagents.platform.analysis.linked_results import LinkedResultPublisher
from tradingagents.platform.analysis.preparation_refusals import (
    next_reserved_execution,
    record_preparation_refusal,
)
from tradingagents.platform.analysis.reserved_preparation import prepare_reserved_continuation
from tradingagents.platform.analysis.supervision import SupervisedAnalysisEngine


@contextmanager
def _keepalive(context, *, lease_seconds):
    stopped = Event()

    def renew():
        while not stopped.wait(lease_seconds / 3):
            try:
                context.heartbeat(lease_seconds=lease_seconds)
            except Exception:
                # The existing exact callback/publication gates refuse as soon
                # as renewal becomes uncertain, not only after lease expiration.
                context._renewal_failed = True
                return

    thread = Thread(target=renew, name="linked-research-lease", daemon=True)
    thread.start()
    try:
        yield
    finally:
        stopped.set()
        thread.join()


def execute_reserved_continuation(*, database, artifact_store, execution_id, base_config,
                                  worker_id, clock=lambda: datetime.now(UTC), lease_seconds=300):
    """Trusted worker operation: derive, claim once, restore, reap and publish.

    Any uncertain claim/entry/dispatch/result ACK raises a fixed error. No automatic
    retry, replenished cap or original job/run transition is performed. Durable
    polling/status/cancel integration is separate from this single operation.
    """
    try:
        prepared = prepare_reserved_continuation(database=database, artifact_store=artifact_store,
            execution_id=execution_id, base_config=base_config, clock=clock)
        executions = LinkedExecutionStore(prepared.consents)
        lease = executions.claim(execution_id=execution_id, worker_id=worker_id, lease_seconds=lease_seconds)
        publisher = LinkedResultPublisher(artifact_store)
        context = LinkedPublicationContext.prepare(executions, lease, save_stage=publisher.save_stage)
        with _keepalive(context, lease_seconds=lease_seconds):
            original = LinkedOriginalResearch.load(context=context, artifact_store=artifact_store)
            publisher.bind(context, original)
            engine = build_linked_recorded_engine(template=SupervisedAnalysisEngine(base_config=base_config),
                                                 context=context, original=original)
            return engine.analyze(original.request)
    except Exception:
        raise ValueError('linked worker execution requires review') from None


def poll_reserved_continuation(*, database, artifact_store, base_config, worker_id,
                               clock=lambda: datetime.now(UTC)):
    """At most one reservation. Failures never become automatic paid retries."""
    execution_id = next_reserved_execution(database)
    if execution_id is None:
        return None
    try:
        return execute_reserved_continuation(database=database, artifact_store=artifact_store,
            execution_id=execution_id, base_config=base_config, worker_id=worker_id, clock=clock)
    except ValueError:
        # Before claim: append one refusal so restart cannot loop the same item.
        # After claim: no relabel/requeue; its private lease/stop/receipt governs.
        record_preparation_refusal(database=database, execution_id=execution_id, worker_id=worker_id, clock=clock)
        return execution_id
