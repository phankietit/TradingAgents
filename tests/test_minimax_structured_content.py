import asyncio
import json
from datetime import date
from typing import Literal

import httpx
import pytest
from pydantic import BaseModel, ConfigDict

from tradingagents.agents.utils.structured import bind_structured, invoke_structured_or_freetext
from tradingagents.llm_clients.openai_client import MinimaxChatOpenAI
from tradingagents.llm_clients.structured_content import parse_structured_content
from tradingagents.platform.analysis.observer import ResearchObserver


class Pick(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["Hold", "Buy"]


def client_for(messages, *, finish_reason="stop"):
    requests = []
    def respond(request):
        requests.append(json.loads(request.content))
        message = messages[min(len(requests) - 1, len(messages) - 1)]
        return httpx.Response(200, json={"id":"fixture", "object":"chat.completion",
            "created":0, "model":"MiniMax-M2.7", "choices":[{"index":0,
                "finish_reason":finish_reason, "message":{"role":"assistant", **message}}],
            "usage":{"prompt_tokens":3, "completion_tokens":2, "total_tokens":5}})
    transport = httpx.MockTransport(respond)
    return MinimaxChatOpenAI(model="MiniMax-M2.7", api_key="test-placeholder",
        base_url="https://api.minimax.io/v1", max_retries=0,
        http_client=httpx.Client(transport=transport),
        http_async_client=httpx.AsyncClient(transport=transport)), requests


@pytest.mark.parametrize("content", ['{"action":"Hold"}', '```json\n{"action":"Hold"}\n```'])
def test_whole_json_content_satisfies_same_schema_with_one_request(content):
    model, requests = client_for([{"content":content, "reasoning_content":"private reasoning fixture"}])
    result = model.with_structured_output(Pick).invoke("Choose from supplied evidence")
    assert result == Pick(action="Hold")
    assert len(requests) == 1
    assert requests[0]["tools"][0]["function"]["name"] == "Pick"
    assert not requests[0].get("tool_choice")
    assert "response_format" not in requests[0]
    assert requests[0]["reasoning_split"] is True


@pytest.mark.parametrize("content", [
    'Here is the result: {"action":"Hold"}', '{"action":"Hold"} trailing text',
    '```json\n{"action":"Hold"}\n```\n```json\n{}\n```',
    '{"action":"Hold","action":"Buy"}', '{"action":"Unknown"}',
    '{"action":"Hold","extra":true}', '[{"action":"Hold"}]',
    '{"action":NaN}', 'not JSON',
])
def test_no_extraction_schema_relaxation_or_reasoning_fallback(content):
    model, requests = client_for([{"content":content, "reasoning_content":'{"action":"Hold"}'}])
    with pytest.raises(ValueError):
        model.with_structured_output(Pick).invoke("Choose")
    assert len(requests) == 1


def test_failed_unknown_tool_is_not_hidden_by_valid_content():
    model, requests = client_for([{"content":'{"action":"Hold"}', "tool_calls":[{
        "id":"call-fixture", "type":"function", "function":{"name":"unknown_tool", "arguments":"{}"}}]}])
    with pytest.raises(ValueError):
        model.with_structured_output(Pick).invoke("Choose")
    assert len(requests) == 1


def test_real_schema_tool_still_works():
    model, requests = client_for([{"content":None, "tool_calls":[{
        "id":"call-fixture", "type":"function", "function":{"name":"Pick", "arguments":'{"action":"Hold"}'}}]}])
    assert model.with_structured_output(Pick).invoke("Choose").action == "Hold"
    assert len(requests) == 1


@pytest.mark.parametrize("extra_call", [False, True])
def test_tool_output_cannot_hide_duplicate_fields_or_additional_tools(extra_call):
    calls = [{"id":"call-fixture", "type":"function", "function":{"name":"Pick",
        "arguments":'{"action":"Hold"}' if extra_call else '{"action":"Hold","action":"Buy"}'}}]
    if extra_call:
        calls.append({"id":"call-other", "type":"function", "function":{"name":"unknown_tool", "arguments":"{}"}})
    model, _ = client_for([{"content":None, "tool_calls":calls}])
    with pytest.raises(ValueError):
        model.with_structured_output(Pick).invoke("Choose")


def test_wire_rejection_flag_is_not_sent_back_to_provider():
    model, _ = client_for([{"content":"unused"}])
    response = {"id":"fixture", "object":"chat.completion", "created":0,
        "model":"MiniMax-M2.7", "choices":[{"index":0, "finish_reason":"tool_calls",
            "message":{"role":"assistant", "content":None, "tool_calls":[{
                "id":"call-fixture", "type":"function", "function":{"name":"Pick",
                "arguments":'{"action":"Hold","action":"Buy"}'}}]}}]}
    message = model._create_chat_result(response).generations[0].message
    assert message.additional_kwargs["_invalid_structured_tool_arguments"] is True
    payload = model._get_request_payload([message])
    assert "_invalid_structured_tool_arguments" not in payload["messages"][0]


@pytest.mark.parametrize("reason", ["length", "content_filter"])
def test_incomplete_completion_is_not_accepted_even_with_valid_json(reason):
    model, _ = client_for([{"content":'{"action":"Hold"}'}], finish_reason=reason)
    with pytest.raises(ValueError):
        model.with_structured_output(Pick).invoke("Choose")


def test_async_and_explicit_raw_contracts_remain_supported():
    model, requests = client_for([{"content":'{"action":"Hold"}'}])
    assert asyncio.run(model.with_structured_output(Pick).ainvoke("Choose")).action == "Hold"
    raw = model.with_structured_output(Pick, include_raw=True).invoke("Choose")
    assert raw["parsed"] is None and raw["raw"].content == '{"action":"Hold"}'
    assert len(requests) == 2


def test_content_fast_path_does_not_bypass_publication_callback_or_repair_budget():
    model, requests = client_for([{"content":'{"action":"Buy"}'}, {"content":'{"action":"Hold"}'}])
    accepted, diagnostics = [], []
    def validate(value):
        if value.action == "Buy":
            raise ValueError("fixture publication rejection")
        accepted.append(value)
    result = invoke_structured_or_freetext(bind_structured(model, Pick, "Fixture"), model,
        "Use supplied evidence only", lambda value:value.action, "Fixture",
        repair_schema=Pick, on_structured=validate, diagnostics=diagnostics)
    assert result == "Hold" and accepted == [Pick(action="Hold")]
    assert len(requests) == 2 and len(diagnostics) == 1


def test_strict_repair_parser_rejects_nested_duplicate_keys():
    with pytest.raises(ValueError, match="duplicate JSON field"):
        parse_structured_content(Pick, '{"nested":{"key":1,"key":2}}')


def test_json_mode_semantics_preserve_strict_date_schemas():
    class Dated(BaseModel):
        model_config = ConfigDict(strict=True)
        as_of: date
    assert parse_structured_content(Dated, '{"as_of":"2026-09-27"}').as_of == date(2026, 9, 27)


def test_fast_path_keeps_usage_accounting_at_one_model_call():
    model, _ = client_for([{"content":'{"action":"Hold"}'}])
    observer = ResearchObserver(check_cancelled=lambda:None, emit=lambda *_:None)
    model.callbacks = [observer]
    assert model.with_structured_output(Pick).invoke("Choose").action == "Hold"
    usage = observer.receipt()["usage"]
    assert usage["model_calls"] == 1 and usage["total_tokens"] == 5


def test_rejected_fast_path_and_repair_never_open_a_third_call():
    model, requests = client_for([{"content":'{"action":"Buy"}'}])
    def reject(_):
        raise ValueError("fixture publication rejection")
    result = invoke_structured_or_freetext(bind_structured(model, Pick, "Fixture"), model,
        "Use supplied evidence only", lambda value:value.action, "Fixture",
        repair_schema=Pick, on_structured=reject, diagnostics=[])
    assert result.startswith("UNVALIDATED RESEARCH")
    assert len(requests) == 2
