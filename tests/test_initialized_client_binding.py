"""Real SDK initialization with synthetic credentials and no network invocation."""

import asyncio

import httpx
import pytest

from tests.test_recovery_fingerprint import inputs
from tradingagents.llm_clients.openai_client import MinimaxChatOpenAI, NormalizedChatOpenAI
from tradingagents.platform.analysis.client_binding import bind_initialized_clients
from tradingagents.platform.analysis.recovery_fingerprint import (
    RecoveryFingerprintError,
    build_recovery_fingerprint,
)


@pytest.fixture(autouse=True)
def forbid_requests(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("binding sent network/model request")

    monkeypatch.setattr(httpx.Client, "send", forbidden)
    monkeypatch.setattr(httpx.AsyncClient, "send", forbidden)
    monkeypatch.setattr(NormalizedChatOpenAI, "invoke", forbidden)


def close(instance):
    instance.root_client.close()
    asyncio.run(instance.root_async_client.close())


def client(**overrides):
    return NormalizedChatOpenAI(
        model="fixture-model",
        api_key="synthetic-NEVER_ECHO",
        base_url="https://example.test/v1",
        timeout=600,
        max_retries=1,
        **overrides,
    )


def test_actual_sdk_endpoint_timeout_options_bind_without_invocation(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("binding sent network/model request")

    monkeypatch.setattr("httpx.Client.send", forbidden)
    monkeypatch.setattr(NormalizedChatOpenAI, "invoke", forbidden)
    quick, deep = client(), client()
    try:
        binding = bind_initialized_clients(quick=quick, deep=deep)
        assert binding.quick_endpoint == "https://example.test/v1/"
        assert binding.quick_options_hash == binding.deep_options_hash
        assert "NEVER_ECHO" not in binding.model_dump_json()
        assert httpx.Timeout(quick.root_client.timeout).read == 600
        deep.root_client.max_retries = 2
        assert (
            bind_initialized_clients(quick=quick, deep=deep).deep_options_hash
            != binding.deep_options_hash
        )
    finally:
        close(quick)
        close(deep)


@pytest.mark.parametrize(
    "options",
    [
        {"temperature": 0.2},
        {"max_tokens": 500},
        {"reasoning_effort": "high"},
        {"use_responses_api": True},
        {"extra_body": {"reasoning_split": True}},
    ],
)
def test_effective_model_options_change_binding(options):
    base, changed = client(), client(**options)
    try:
        result = bind_initialized_clients(quick=base, deep=changed)
        assert result.quick_options_hash != result.deep_options_hash
    finally:
        close(base)
        close(changed)


@pytest.mark.parametrize(
    "options",
    [
        {"default_headers": {"Authorization": "NEVER_ECHO"}},
        {"default_query": {"api_key": "NEVER_ECHO"}},
        {"extra_body": {"api_key": "NEVER_ECHO"}},
    ],
)
def test_custom_request_credentials_not_ignored_or_persisted(options):
    instance = client(**options)
    try:
        with pytest.raises(RecoveryFingerprintError) as raised:
            bind_initialized_clients(quick=instance, deep=instance)
        assert str(raised.value) == "initialized client binding is unsupported or unsafe"
    finally:
        close(instance)


def test_unreviewed_client_object_cannot_supply_descriptor():
    with pytest.raises(RecoveryFingerprintError):
        bind_initialized_clients(quick=object(), deep=object())


def test_existing_minimax_class_has_distinct_initialized_identity():
    instance = MinimaxChatOpenAI(
        model="MiniMax-M3",
        api_key="synthetic-NEVER_ECHO",
        base_url="https://example.test/v1",
        timeout=600,
        max_retries=1,
    )
    try:
        binding = bind_initialized_clients(quick=instance, deep=instance)
        assert binding.quick_client_class.endswith("MinimaxChatOpenAI")
        assert "NEVER_ECHO" not in binding.model_dump_json()
    finally:
        close(instance)


def test_sdk_descriptor_composes_with_original_run_fingerprint():
    args = inputs()
    quick, deep = client(), client()
    try:
        quick.model_name = "quick"
        deep.model_name = "deep"
        args["client_binding"] = bind_initialized_clients(quick=quick, deep=deep)
        original = build_recovery_fingerprint(**args)
        deep.root_client.max_retries = 2
        args["client_binding"] = bind_initialized_clients(quick=quick, deep=deep)
        assert build_recovery_fingerprint(**args) != original
    finally:
        close(quick)
        close(deep)


def test_actual_sdk_timeout_mutation_invalidates_binding():
    instance = client()
    try:
        original = bind_initialized_clients(quick=instance, deep=instance)
        instance.root_client.timeout = httpx.Timeout(600, read=300)
        changed = bind_initialized_clients(quick=instance, deep=instance)
        assert changed.quick_options_hash != original.quick_options_hash
    finally:
        close(instance)


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://other.test/v1/",
        "https://example.test/v2/",
        "https://example.test/v1//",
        "https://example.test/v1/?api_key=NEVER_ECHO",
        "https://user:NEVER_ECHO@example.test/v1/",
    ],
)
def test_sdk_endpoint_normalization_does_not_allow_other_changes(endpoint):
    args = inputs()
    args["client_binding"] = args["client_binding"].model_copy(update={"deep_endpoint": endpoint})
    with pytest.raises(RecoveryFingerprintError) as raised:
        build_recovery_fingerprint(**args)
    assert str(raised.value) == "recovery inputs are invalid or incompatible"
