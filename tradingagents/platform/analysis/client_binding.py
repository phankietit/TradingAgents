"""Read reviewed initialized OpenAI-compatible clients without invoking them.

Internal prerequisite only; no graph/worker hook or paid continuation authority.
Other SDKs/custom transports require dedicated reviewed adapters, not guesses.
"""

import hashlib
import json

import httpx
import openai

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
