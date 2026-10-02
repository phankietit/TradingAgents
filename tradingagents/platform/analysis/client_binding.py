"""Read reviewed initialized OpenAI-compatible clients without invoking them.

Internal prerequisite only; no graph/worker hook or paid continuation authority.
Other SDKs/custom transports require dedicated reviewed adapters, not guesses.
"""

import hashlib
import json
from copy import deepcopy

import httpx
import openai

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.llm_clients.openai_client import (
    DeepSeekChatOpenAI,
    LocalCompatibleChatOpenAI,
    MinimaxChatOpenAI,
    NormalizedChatOpenAI,
)

from .recovery_fingerprint import (
    RecoveryFingerprintError,
    ResolvedClientBinding,
    _endpoint,
    _no_credentials,
    build_recovery_fingerprint,
)


def _inspect(llm):
    if type(llm) not in {
        NormalizedChatOpenAI,
        LocalCompatibleChatOpenAI,
        DeepSeekChatOpenAI,
        MinimaxChatOpenAI,
    }:
        raise RecoveryFingerprintError("initialized client binding is unsupported or unsafe")
    if (
        llm.default_headers
        or llm.default_query
        or llm.http_client is not None
        or llm.http_async_client is not None
    ):
        raise RecoveryFingerprintError("initialized client binding is unsupported or unsafe")
    root = llm.root_client
    if type(root) is not openai.OpenAI:
        raise RecoveryFingerprintError("initialized client binding is unsupported or unsafe")
    endpoint = _endpoint(str(root.base_url))
    timeout = root.timeout
    if not isinstance(timeout, httpx.Timeout):
        timeout = httpx.Timeout(timeout)
    values = {
        "wire_params": llm._default_params,
        "sdk_max_retries": root.max_retries,
        "langchain_max_retries": llm.max_retries,
        "sdk_timeout": {key: getattr(timeout, key) for key in ("connect", "read", "write", "pool")},
        "use_responses_api": llm.use_responses_api,
        "output_version": llm.output_version,
        "disabled_params": llm.disabled_params,
        "disable_streaming": llm.disable_streaming,
        "stream_usage": llm.stream_usage,
        "include_response_headers": llm.include_response_headers,
    }
    _no_credentials(values)
    raw = json.dumps(
        values, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":")
    ).encode()
    identity = type(llm).__module__ + "." + type(llm).__qualname__
    return endpoint, identity, "sha256:" + hashlib.sha256(raw).hexdigest()


def bind_initialized_clients(*, quick, deep) -> ResolvedClientBinding:
    """Derive sanitized identity from actual sync clients, never model_dump.

    Credentials and SDK authentication/header properties are deliberately not
    read. Endpoint/options hashes only; this function sends no request and
    cannot validate provider reachability, account/quota or an owner's consent.
    """
    try:
        quick_endpoint, quick_class, quick_options = _inspect(quick)
        deep_endpoint, deep_class, deep_options = _inspect(deep)
        return ResolvedClientBinding(
            quick_endpoint=quick_endpoint,
            deep_endpoint=deep_endpoint,
            quick_client_class=quick_class,
            deep_client_class=deep_class,
            quick_options_hash=quick_options,
            deep_options_hash=deep_options,
        )
    except (ValueError, TypeError, AttributeError, KeyError, RecursionError):
        raise RecoveryFingerprintError(
            "initialized client binding is unsupported or unsafe"
        ) from None


def build_initialized_graph_fingerprint(*, graph, owner_id, run, request, base_config,
                                       portfolio_snapshot=None, policy=None, risk_snapshots=()):
    """Bind original inputs to an actual initialized snapshot graph, no invoke.

    Trusted construction and owner-readable loading remain caller obligations.
    This rejects discrepancies before a model call; it does not attest arbitrary
    SDK/header/HTTP mutations or authorize continuation/allowance changes.
    Never accept a graph/client descriptor from a browser or model.
    """
    try:
        effective = deepcopy(dict(base_config))
        effective.update(deepcopy(dict(request.config_overrides)))
        reports = request.snapshot_context.reports(request.instrument.instrument_id, run.selected_analysts)
        report_digest = hashlib.sha256(json.dumps(reports, sort_keys=True, ensure_ascii=False,
            allow_nan=False, separators=(",", ":")).encode()).hexdigest()
        if (type(graph) is not TradingAgentsGraph or graph.snapshot_mode is not True
                or graph.config != effective or graph.selected_analysts != run.selected_analysts
                or graph._snapshot_reports_digest != report_digest
                or graph.quick_thinking_llm.model_name != run.quick_model
                or graph.deep_thinking_llm.model_name != run.deep_model):
            raise ValueError("incompatible graph")
        binding = bind_initialized_clients(quick=graph.quick_thinking_llm,
                                           deep=graph.deep_thinking_llm)
        # The existing builder revalidates all original source/run/book inputs.
        # Descriptors here come from the clients on this graph, not arguments.
        return build_recovery_fingerprint(owner_id=owner_id, run=run, request=request,
            base_config=base_config, client_binding=binding, portfolio_snapshot=portfolio_snapshot,
            policy=policy, risk_snapshots=risk_snapshots)
    except (ValueError, TypeError, AttributeError, KeyError, RecursionError):
        raise RecoveryFingerprintError("initialized graph recovery identity is incompatible") from None
