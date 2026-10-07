"""Bounded spawn-only actual SDK identity probe, never research or consent.

Default LangChain transports are process-cached: fresh SDK roots cannot be
disposed safely in the worker. Only the probe child creates/closes SDKs. Parent
credentials stay in its environment; no SDK, observer, DB or callable is sent.
"""

import asyncio
import json
from copy import deepcopy
from dataclasses import dataclass
from multiprocessing import get_context, parent_process
from os import _exit
from queue import Empty, Queue
from threading import Event, Thread
from time import monotonic
from uuid import UUID

import openai
from pydantic import BaseModel, ConfigDict, Field

from tradingagents.contracts import PolicyContract, PortfolioSnapshot, RunManifest
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.llm_clients.openai_client import (
    OPENAI_COMPATIBLE_PROVIDERS,
    DeepSeekChatOpenAI,
    LocalCompatibleChatOpenAI,
    MinimaxChatOpenAI,
    NormalizedChatOpenAI,
)

from .checkpoint_codec import SnapshotCheckpointCodec
from .client_binding import build_initialized_graph_fingerprint
from .engine import AnalysisRequest
from .observer import ResearchExecutionFailed, ResearchObserver
from .recording_context import MAX_RECORDING_CONTEXT_BYTES, _invalid_constant, _unique_fields
from .recovery_fingerprint import _no_credentials
from .snapshots import AnalysisSnapshot

PREFLIGHT_SECONDS = 45
MAX_REPLY_BYTES = 8192
_REVIEWED = (NormalizedChatOpenAI, LocalCompatibleChatOpenAI, DeepSeekChatOpenAI, MinimaxChatOpenAI)


class InitializedPreflightError(ResearchExecutionFailed):
    """Fixed refusal; no input or SDK exception escapes the process boundary."""


def _reject():
    raise InitializedPreflightError("initialized recording preflight requires review") from None


class _Inputs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    owner_id: UUID = Field(repr=False)
    run: RunManifest = Field(repr=False)
    request: AnalysisRequest = Field(repr=False)
    base_config: dict = Field(repr=False)
    portfolio_snapshot: PortfolioSnapshot | None = Field(default=None, repr=False)
    policy: PolicyContract | None = Field(default=None, repr=False)
    risk_snapshots: tuple[AnalysisSnapshot, ...] = Field(default=(), max_length=100, repr=False)


class _Reply(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$", repr=False)
    nodes: tuple[str, ...] = Field(min_length=1, max_length=40, repr=False)


@dataclass(frozen=True, repr=False)
class PreparedRecordingIdentity:
    fingerprint: str
    nodes: tuple[str, ...]


def _read(raw, model, limit):
    if type(raw) is not bytes or not 0 < len(raw) <= limit:
        _reject()
    data = json.loads(raw, object_pairs_hook=_unique_fields, parse_constant=_invalid_constant)
    return model.model_validate(data)


def _validate_inputs(value):
    if value.request.snapshot_context is None or value.request.execution_observer is not None:
        _reject()
    _no_credentials(value.base_config)
    _no_credentials(dict(value.request.config_overrides))
    # Reject non-JSON/nonfinite config before Pydantic's JSON serializer can
    # normalize NaN/Infinity to null and change the original effective options.
    json.dumps(value.base_config, allow_nan=False)
    json.dumps(dict(value.request.config_overrides), allow_nan=False)
    if value.policy is not None:
        _no_credentials(value.policy.parameters)
        json.dumps(value.policy.parameters, allow_nan=False)
    effective = deepcopy(value.base_config)
    effective.update(deepcopy(dict(value.request.config_overrides)))
    provider = effective.get("llm_provider", "").lower()
    spec = OPENAI_COMPATIBLE_PROVIDERS.get(provider)
    if provider != "openai" and (spec is None or spec.chat_class not in _REVIEWED):
        _reject()
    return effective


def _close_child_clients(graph):
    # Child-only: process-scoped default pools cannot affect worker SDKs.
    seen, failed = set(), False
    for attribute in ("deep_thinking_llm", "quick_thinking_llm"):
        llm = getattr(graph, attribute, None)
        if llm is None:
            continue
        if type(llm) not in _REVIEWED:
            failed = True
            continue
        for field, cls in (("root_client", openai.OpenAI), ("root_async_client", openai.AsyncOpenAI)):
            client = getattr(llm, field, None)
            if type(client) is not cls:
                failed = True
                continue
            if id(client) in seen:
                continue
            seen.add(id(client))
            try:
                if not client.is_closed():
                    if cls is openai.AsyncOpenAI:
                        asyncio.run(client.close())
                    else:
                        client.close()
            except Exception:
                failed = True
    return not failed


def _prepare_in_child(raw):
    value = _read(raw, _Inputs, MAX_RECORDING_CONTEXT_BYTES)
    effective = _validate_inputs(value)
    request = value.request
    reports = request.snapshot_context.reports(request.instrument.instrument_id, request.selected_analysts)
    # Keep the exact original instance reachable through partial __init__ failure.
    graph = object.__new__(TradingAgentsGraph)
    try:
        TradingAgentsGraph.__init__(graph, config=effective,
            selected_analysts=request.selected_analysts, snapshot_reports=reports)
        fingerprint = build_initialized_graph_fingerprint(graph=graph, owner_id=value.owner_id,
            run=value.run, request=request, base_config=value.base_config,
            portfolio_snapshot=value.portfolio_snapshot, policy=value.policy, risk_snapshots=value.risk_snapshots)
        reply = _Reply(fingerprint=fingerprint, nodes=tuple(sorted(graph.workflow.nodes)))
    finally:
        if not _close_child_clients(graph):
            _reject()
    # Cleanup must succeed before the child publishes an identity.
    return reply.model_dump_json().encode("utf-8")


def _preflight_child(connection, raw):
    stopped = Event()

    def guard_parent():
        parent = parent_process()
        while not stopped.wait(0.2):
            if parent is not None and not parent.is_alive():
                _exit(1)

    guard = Thread(target=guard_parent, name="preflight-parent-guard", daemon=True)
    guard.start()
    try:
        reply = _prepare_in_child(raw)
        if len(reply) > MAX_REPLY_BYTES:
            _reject()
        connection.send_bytes(reply)
    except Exception:
        # Fixed bounded refusal, never pickle or forward provider exception text.
        connection.send_bytes(b"{}")
    finally:
        connection.close()
        stopped.set()
        guard.join(timeout=1)


def prepare_recording_identity(*, observer, **values):
    """Internal worker prerequisite using the original observer wall/lease fence.

    Authenticated source loading remains mandatory. No model invocation, budget
    reservation, checkpoint commit, continuation grant or graph object escapes.
    Neither a client/factory nor a browser descriptor is accepted in values.
    """
    if type(observer) is not ResearchObserver:
        _reject()
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        pass
    else:
        _reject()  # Synchronous worker-only; do not block an HTTP event loop.
    deadline = monotonic() + PREFLIGHT_SECONDS

    def boundary():
        remaining = min(observer.remaining_seconds(), deadline - monotonic())
        if remaining <= 0:
            _reject()
        return remaining

    boundary()
    try:
        # The excluded observer stays parent-owned, even if on the request.
        value = _Inputs.model_validate(values)
        if (value.request.execution_observer is not None
                and value.request.execution_observer is not observer):
            _reject()
        value = value.model_copy(update={"request": value.request.model_copy(
            update={"execution_observer": None})})
        _validate_inputs(value)
        json.dumps(value.model_dump(mode="json", warnings=False), allow_nan=False)
        value = _Inputs.model_validate_json(value.model_dump_json(warnings=False))
        _validate_inputs(value)
        raw = value.model_dump_json(warnings=False).encode("utf-8")
        if len(raw) > MAX_RECORDING_CONTEXT_BYTES:
            _reject()
    except Exception:
        _reject()
    boundary()
    try:
        context = get_context("spawn")
        parent, child = context.Pipe(duplex=False)
    except Exception:
        _reject()
    try:
        process = context.Process(target=_preflight_child, args=(child, raw), daemon=True)
    except Exception:
        parent.close()
        child.close()
        _reject()
    received = Queue(maxsize=1)

    def receive():
        try:
            received.put(parent.recv_bytes(maxlength=MAX_REPLY_BYTES))
        except Exception:
            received.put(b"{}")

    reader = Thread(target=receive, name="preflight-pipe-reader", daemon=True)
    reply = None
    try:
        boundary()
        try:
            process.start()
        except Exception:
            _reject()
        child.close()
        reader.start()
        while reply is None:
            remaining = boundary()
            try:
                raw_reply = received.get(timeout=min(0.1, remaining))
            except Empty:
                continue
            boundary()  # Cancellation/lease/deadline wins over queued success.
            try:
                reply = _read(raw_reply, _Reply, MAX_REPLY_BYTES)
                if (reply.nodes != tuple(sorted(set(reply.nodes)))
                        or any(not node or len(node) > 100 for node in reply.nodes)):
                    _reject()
                SnapshotCheckpointCodec(fingerprint=reply.fingerprint, nodes=reply.nodes)
            except Exception:
                _reject()
        while process.is_alive():
            process.join(timeout=min(0.1, boundary()))
        boundary()
        if process.exitcode != 0:
            _reject()
    finally:
        # Reap only this owned child; never close SDKs or clear worker caches.
        if process.pid is not None:
            if process.is_alive():
                process.terminate()
            process.join(timeout=1)
            if process.is_alive():
                process.kill()
                process.join(timeout=1)
        parent.close()
        child.close()
        if reader.ident is not None:
            reader.join(timeout=1)
        clean = not process.is_alive() and not reader.is_alive()
        if clean:
            process.close()
        if not clean:
            _reject()
    boundary()
    return PreparedRecordingIdentity(reply.fingerprint, reply.nodes)
