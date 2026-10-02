"""Spawn-isolated snapshot research with parent-owned budget/publication authority.

No database, lease, artifact writer or raw model messages cross into the child.
Stopping local execution does not guarantee that a provider stops billing.
"""

import hashlib
from contextlib import suppress
from multiprocessing import get_context, parent_process
from os import _exit
from pickle import loads
from queue import Empty, Full, Queue
from threading import Event, Lock, Thread
from types import SimpleNamespace
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler

from .checkpoint_codec import SnapshotCheckpointCodec
from .checkpoint_store import CheckpointCommit, CheckpointDatabaseError
from .engine import AnalysisEngine, AnalysisRequest, AnalysisResult
from .observer import STAGES, ResearchExecutionFailed
from .recording_context import SnapshotRecordingInputs
from .stage_records import STAGE_PATHS, stage_sections

# Exactly the fields used by the web report publisher, not raw graph messages.
RESULT_FIELDS = frozenset({
    "final_trade_decision", "structured_diagnostics", "structured_decision",
    "rejected_structured_decision", "structured_draft", "market_report",
    "sentiment_report", "news_report", "fundamentals_report", "investment_plan",
    "trader_investment_plan", "investment_debate_state", "risk_debate_state",
})


class _Bridge(BaseCallbackHandler):
    raise_error = True
    run_inline = True

    def __init__(self, connection, checkpoint_options=None):
        self.connection = connection
        self.active = {}
        self.lock = Lock()
        self.checkpoint_options = checkpoint_options

    def commit_checkpoint(self, raw):
        if self.checkpoint_options is None:
            raise ResearchExecutionFailed("checkpoint bridge is not enabled")
        return self.rpc("checkpoint_commit", raw)

    def validate_recording_allowance(self, *, wall_seconds, model_calls, fingerprint, thread_id):
        if self.checkpoint_options is None:
            raise ResearchExecutionFailed("recording allowance requires review")
        reply = self.rpc("recording_allowance", {"wall_seconds": wall_seconds,
            "model_calls": model_calls, "fingerprint": fingerprint, "thread_id": thread_id})
        if reply is not True:
            raise ResearchExecutionFailed("recording allowance requires review")

    def rpc(self, method, payload):
        # Concurrent callback threads must not interleave pipe frames or consume
        # another call's acknowledgement. The parent still owns admission.
        with self.lock:
            self.connection.send((method, payload))
            return self.connection.recv()

    def on_chain_start(self, serialized, inputs, *, run_id, name=None, **kwargs):
        if name in STAGES:
            self.rpc("stage_start", (run_id, name))
            self.active[run_id] = name

    def on_chain_end(self, outputs, *, run_id, **kwargs):
        stage = self.active.pop(run_id, None)
        if stage:
            self.rpc("stage_end", (run_id, stage_sections(stage, outputs)))

    def on_chat_model_start(self, serialized, messages, *, run_id, **kwargs):
        self.rpc("model_start", run_id)

    def on_llm_end(self, response, *, run_id, **kwargs):
        message = response.generations[0][0].message if response.generations and response.generations[0] else None
        usage = getattr(message, "usage_metadata", None)
        # Only provider-reported counters, never assistant text or reasoning.
        self.rpc("model_end", (run_id, {key: usage.get(key) for key in
            ("input_tokens", "output_tokens", "total_tokens")} if isinstance(usage, dict) else None))

    def on_llm_error(self, error, *, run_id, **kwargs):
        self.rpc("model_error", run_id)


def _child(connection, base_config, request_data, engine_factory, checkpoint_options=None,
           recording_data=None):
    stopped = Event()

    def guard_parent():
        parent = parent_process()
        while not stopped.wait(0.2):
            if parent is not None and not parent.is_alive():
                # A killed/crashed worker cannot leave an orphan SDK call.
                # There is no child publication authority or cleanup to run.
                _exit(1)

    guard = Thread(target=guard_parent, name="research-parent-guard", daemon=True)
    guard.start()
    try:
        request = AnalysisRequest.model_validate(request_data).model_copy(
            update={"execution_observer": _Bridge(connection, checkpoint_options)})
        options = {}
        if recording_data is not None:
            from .recording import SnapshotRecorder

            if engine_factory is not AnalysisEngine or checkpoint_options is None:
                raise ValueError()
            inputs = SnapshotRecordingInputs(recording_data).validate_request(request)
            if (inputs.expected_fingerprint != checkpoint_options["fingerprint"]
                    or str(inputs.run.run_id) != checkpoint_options["thread_id"]):
                raise ValueError()
            options["snapshot_recorder"] = SnapshotRecorder(
                owner_id=inputs.owner_id, expected_fingerprint=inputs.expected_fingerprint,
                run=inputs.run, portfolio_snapshot=inputs.portfolio_snapshot, policy=inputs.policy,
                risk_snapshots=inputs.risk_snapshots, commit=request.execution_observer.commit_checkpoint)
        result = engine_factory(base_config=base_config, **options).analyze(request)
        result = result.model_copy(update={"final_state": {
            key: value for key, value in result.final_state.items() if key in RESULT_FIELDS}})
        for key in ("investment_debate_state", "risk_debate_state"):
            if key in result.final_state:
                result.final_state[key] = {"history": result.final_state[key].get("history", "")}
        connection.send(("result", result.model_dump(mode="json")))
    except BaseException:
        # Never transfer a raw vendor exception, credentials or traceback.
        with suppress(BrokenPipeError, EOFError, OSError):
            connection.send(("failure", None))
    finally:
        stopped.set()
        guard.join()
        connection.close()


def _outputs(stage, sections):
    outputs = {}
    for label, text in sections.items():
        path = STAGE_PATHS[stage][label]
        current = outputs
        for key in path[:-1]:
            current = current.setdefault(key, {})
        current[path[-1]] = text
    return outputs


class SupervisedAnalysisEngine:
    """Default web-worker engine; CLI and explicitly injected engines are unchanged."""

    def __init__(self, *, base_config=None, engine_factory=AnalysisEngine,
                 checkpoint_codec=None, checkpoint_thread_id=None, checkpoint_commit=None,
                 recording_inputs=None):
        self.base_config = base_config
        self.engine_factory = engine_factory
        supplied = (checkpoint_codec, checkpoint_thread_id, checkpoint_commit)
        self.checkpoint_options = None
        self.checkpoint_codec = checkpoint_codec
        self.checkpoint_commit = checkpoint_commit
        self.recording_inputs = recording_inputs
        if recording_inputs is not None or any(value is not None for value in supplied):
            try:
                original = None
                if recording_inputs is not None:
                    if type(recording_inputs) is not SnapshotRecordingInputs or engine_factory is not AnalysisEngine:
                        raise ValueError()
                    original = recording_inputs.read()
                if (type(checkpoint_codec) is not SnapshotCheckpointCodec
                        or not callable(checkpoint_commit)
                        or (original is None and getattr(engine_factory, "supports_checkpoint_bridge", False) is not True)
                        or str(UUID(checkpoint_thread_id)) != checkpoint_thread_id):
                    raise ValueError()
                if original is not None and (original.expected_fingerprint != checkpoint_codec.fingerprint
                        or str(original.run.run_id) != checkpoint_thread_id):
                    raise ValueError()
            except (ValueError, TypeError, AttributeError):
                raise ValueError("invalid checkpoint bridge configuration") from None
            # Explicit private context is separate; DB/lease/callback remain
            # parent-only. Default worker never supplies these options.
            self.checkpoint_options = {"fingerprint": checkpoint_codec.fingerprint,
                                       "thread_id": checkpoint_thread_id}

    def analyze(self, request):
        # Legacy live-tool jobs retain their existing engine contract.
        if request.snapshot_context is None:
            if self.checkpoint_options is not None:
                raise ValueError("checkpoint bridge requires snapshot research")
            return self.engine_factory(base_config=self.base_config).analyze(request)
        observer = request.execution_observer
        if observer is None:
            raise ValueError("snapshot supervision requires a research observer")
        observer.remaining_seconds()
        recording_data = None
        if self.recording_inputs is not None:
            inputs = self.recording_inputs.validate_request(request)
            if (inputs.expected_fingerprint != self.checkpoint_options["fingerprint"]
                    or str(inputs.run.run_id) != self.checkpoint_options["thread_id"]):
                raise ValueError("invalid checkpoint bridge configuration")
            recording_data = self.recording_inputs.raw
        context = get_context("spawn")  # Never fork a worker's live DB/lease thread.
        parent, child = context.Pipe()
        process = context.Process(target=_child, args=(child, self.base_config,
            request.model_dump(mode="python"), self.engine_factory, self.checkpoint_options,
            recording_data), daemon=True)
        pending_models = set()
        checkpoint_commits = 0
        received = Queue(maxsize=1)
        stopped = Event()

        def receive():
            # Receiving a large/partial frame must not block the budget owner.
            # This is a private pipe from trusted spawned code, not user input.
            while not stopped.is_set():
                try:
                    message = loads(parent.recv_bytes(maxlength=32_000_000))
                except Exception:
                    message = ("failure", None)
                while not stopped.is_set():
                    try:
                        received.put(message, timeout=0.2)
                        break
                    except Full:
                        continue
                if message[0] in {"failure", "result"}:
                    return

        reader = Thread(target=receive, name="research-pipe-reader", daemon=True)
        try:
            process.start()
            observer.supervision_mode = "spawned_process"
            child.close()
            reader.start()
            while True:
                observer.check_cancelled()
                # Drain returned notes/usage already waiting at a deadline,
                # matching the observer's retain-before-boundary semantics.
                try:
                    method, payload = received.get_nowait()
                except Empty:
                    remaining = observer.remaining_seconds()
                    try:
                        method, payload = received.get(timeout=min(0.2, remaining))
                    except Empty:
                        if not reader.is_alive() and received.empty():
                            raise ResearchExecutionFailed("research child stopped without a result") from None
                        continue
                # Cancellation/deadline always wins over a queued final result.
                observer.check_cancelled()
                if method == "result":
                    observer.remaining_seconds()
                    if pending_models:
                        raise ResearchExecutionFailed("research returned with unfinished model calls")
                    if self.checkpoint_options is not None and checkpoint_commits == 0:
                        raise ResearchExecutionFailed("research returned without committed checkpoints")
                    result = AnalysisResult.model_validate(payload)
                    if (result.instrument != request.instrument
                            or result.analysis_date != request.analysis_date):
                        raise ResearchExecutionFailed("research result context mismatch")
                    process.join(timeout=1)
                    return result
                if method == "failure":
                    raise ResearchExecutionFailed("isolated research execution requires review")
                reply = None
                if method == "checkpoint_commit":
                    observer.remaining_seconds()
                    try:
                        if self.checkpoint_options is None:
                            raise ValueError()
                        value = self.checkpoint_codec.decode(payload)
                        if value.config["configurable"]["thread_id"] != self.checkpoint_options["thread_id"]:
                            raise ValueError()
                        reply = self.checkpoint_commit(payload)
                        if (type(reply) is not CheckpointCommit or type(reply.sequence) is not int
                                or reply.sequence < 1 or type(reply.record_id) is not UUID
                                or reply.content_hash != hashlib.sha256(payload).hexdigest()):
                            raise ValueError()
                    except CheckpointDatabaseError:
                        # Do not immediately re-enter an unbounded DB-backed
                        # lease/cancel query after a bounded DB failure.
                        raise ResearchExecutionFailed("checkpoint commit requires review") from None
                    except Exception:
                        # Recheck cancellation/lease before sanitizing a failed
                        # callback; never echo DB/checkpoint exception payloads.
                        observer.check_cancelled()
                        raise ResearchExecutionFailed("checkpoint commit requires review") from None
                    # Cancellation/deadline at commit/ACK never grants advance.
                    observer.check_cancelled()
                    observer.remaining_seconds()
                    checkpoint_commits += 1
                elif method == "recording_allowance":
                    if (self.checkpoint_options is None or type(payload) is not dict
                            or set(payload) != {"wall_seconds", "model_calls", "fingerprint", "thread_id"}
                            or type(payload["wall_seconds"]) is not int
                            or type(payload["model_calls"]) is not int
                            or type(payload["fingerprint"]) is not str
                            or type(payload["thread_id"]) is not str
                            or payload["wall_seconds"] != observer.max_seconds
                            or payload["model_calls"] != observer.max_calls
                            or payload["fingerprint"] != self.checkpoint_options["fingerprint"]
                            or payload["thread_id"] != self.checkpoint_options["thread_id"]):
                        raise ResearchExecutionFailed("recording allowance requires review")
                    # Parent alone checks its original clock/lease/cancellation.
                    # This ACK is not a new budget, checkpoint or consent.
                    observer.remaining_seconds()
                    reply = True
                elif method == "stage_start":
                    run_id, stage = payload
                    observer.on_chain_start({}, {}, run_id=run_id, name=stage)
                elif method == "stage_end":
                    run_id, sections = payload
                    stage = observer.active.get(run_id)
                    if stage not in STAGES:
                        raise ResearchExecutionFailed("research stage context missing")
                    observer.on_chain_end(_outputs(stage, sections), run_id=run_id)
                elif method == "model_start":
                    observer.on_chat_model_start({}, [], run_id=payload)
                    pending_models.add(payload)
                elif method == "model_end":
                    run_id, usage = payload
                    response = SimpleNamespace(generations=[[SimpleNamespace(
                        message=SimpleNamespace(usage_metadata=usage))]])
                    observer.on_llm_end(response, run_id=run_id)
                    pending_models.discard(run_id)
                    observer.remaining_seconds()
                elif method == "model_error":
                    observer.on_llm_error(RuntimeError("isolated model call failed"), run_id=payload)
                    pending_models.discard(payload)
                    observer.remaining_seconds()
                else:
                    raise ResearchExecutionFailed("unsupported research bridge operation")
                parent.send(reply)
        finally:
            # Do not leave a detached SDK call or child capable of local work.
            child_stopped = False
            if process.pid is not None:
                if process.is_alive():
                    process.terminate()
                process.join(timeout=1)
                if process.is_alive():
                    process.kill()
                    process.join()
                process.close()
                child_stopped = True
            stopped.set()
            parent.close()
            child.close()
            if reader.ident is not None:
                reader.join()
            # No token/cost fabrication for interrupted requests. Preserve the
            # original cancellation/deadline error if its event fence rejects.
            for run_id in pending_models:
                with suppress(Exception):
                    observer.on_llm_error(RuntimeError("local execution stopped"), run_id=run_id)
            if child_stopped:
                # Only after child reaping AND reader shutdown. Lease/cancel
                # fences may refuse this append; preserve the original outcome
                # and leave missing durable stop evidence unknown, not inferred.
                with suppress(Exception):
                    observer._record_supervised_stop()
