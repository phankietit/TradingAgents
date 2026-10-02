"""Untrusted checkpoint bytes cannot deserialize arbitrary objects or authority."""

import json
from copy import deepcopy
from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage
from langgraph.checkpoint.base import CheckpointTuple

from tradingagents.platform.analysis.checkpoint_codec import (
    MAX_CHECKPOINT_BYTES,
    MAX_TEXT,
    CheckpointCodecError,
    SnapshotCheckpointCodec,
)


def checkpoint():
    identity = str(uuid4())
    state = {"research_only": True, "past_context": "", "market_report": "Reader report",
             "messages": [AIMessage(content="PRIVATE_RAW_MESSAGE", additional_kwargs={
                 "reasoning_content": "PRIVATE_REASONING"})]}
    config = {"configurable": {"thread_id": "fixture", "checkpoint_ns": "", "checkpoint_id": identity}}
    return CheckpointTuple(config=config, checkpoint={"v": 4, "id": identity,
        "ts": "2026-10-02T00:00:00+00:00", "channel_values": deepcopy(state),
        "channel_versions": dict.fromkeys(state, 1),
        "versions_seen": {"Market Analyst": {"messages": 1}}, "updated_channels": ["market_report"]},
        metadata={"source": "loop", "step": 1, "parents": {}, "thread_id": "fixture"},
        pending_writes=[(str(uuid4()), "__start__", state), (str(uuid4()), "messages", state["messages"])])


@pytest.fixture
def codec():
    return SnapshotCheckpointCodec(fingerprint="a" * 64, nodes={"Market Analyst"})


def test_every_message_location_removed_without_mutating_input(codec):
    original = checkpoint()
    encoded = codec.encode(original)
    assert b"PRIVATE_RAW_MESSAGE" not in encoded and b"PRIVATE_REASONING" not in encoded
    decoded = codec.decode(encoded)
    assert decoded.checkpoint["channel_values"]["messages"] == []
    assert decoded.pending_writes[0][2]["messages"] == []
    assert decoded.pending_writes[1][2] == []
    assert original.checkpoint["channel_values"]["messages"][0].content == "PRIVATE_RAW_MESSAGE"
    assert decoded.checkpoint["channel_versions"] == original.checkpoint["channel_versions"]
    assert decoded.checkpoint["versions_seen"] == original.checkpoint["versions_seen"]


@pytest.mark.parametrize("location", ["top", "state", "initial", "pending", "metadata", "decision",
    "version", "node", "authority", "memory", "messages", "initial_messages", "pending_messages",
    "fingerprint", "schema", "native_version", "nonfinite", "parent_owner", "missing_authority",
    "diagnostic", "diagnostic_input", "routing", "timezone", "id", "typed_object",
    "duplicate_write", "unversioned_seen"])
def test_mutated_untrusted_bytes_rejected_without_echo(codec, location):
    envelope = json.loads(codec.encode(checkpoint()))
    cp = envelope["checkpoint"]
    state = cp["channel_values"]
    if location == "top":
        envelope["private_secret"] = "NEVER_ECHO"
    elif location == "state":
        state["reasoning_content"] = "NEVER_ECHO"
    elif location == "initial":
        envelope["pending_writes"][0][2]["prompt"] = "NEVER_ECHO"
    elif location == "pending":
        envelope["pending_writes"].append([str(uuid4()), "__error__", "NEVER_ECHO"])
    elif location == "metadata":
        envelope["metadata"]["api_key"] = "NEVER_ECHO"
    elif location == "decision":
        state["structured_decision"] = {"target_weight": .25, "reasoning": "NEVER_ECHO"}
    elif location == "version":
        cp["channel_versions"]["messages"] = True
    elif location == "node":
        cp["versions_seen"]["Unapproved agent"] = {}
    elif location == "authority":
        state["research_only"] = False
    elif location == "memory":
        state["past_context"] = "NEVER_ECHO"
    elif location == "messages":
        state["messages"] = ["NEVER_ECHO"]
    elif location == "initial_messages":
        envelope["pending_writes"][0][2]["messages"] = ["NEVER_ECHO"]
    elif location == "pending_messages":
        envelope["pending_writes"][1][2] = ["NEVER_ECHO"]
    elif location == "fingerprint":
        envelope["fingerprint"] = "b" * 64
    elif location == "schema":
        envelope["schema_version"] = "unknown"
    elif location == "native_version":
        cp["v"] = 3
    elif location == "nonfinite":
        cp["channel_versions"]["messages"] = float("nan")
    elif location == "parent_owner":
        envelope["parent_config"] = {"configurable": {"thread_id": "other"}}
    elif location == "missing_authority":
        del state["research_only"]
    elif location in {"diagnostic", "diagnostic_input"}:
        state["structured_diagnostics"] = [{"agent": "Market Analyst", "phase": "repair",
            "error_type": "ValidationError", "fields": [], "raw_input": "NEVER_ECHO"}]
        if location == "diagnostic_input":
            del state["structured_diagnostics"][0]["raw_input"]
            state["structured_diagnostics"][0]["fields"] = [{"field": "rating", "code": "invalid", "input": "NEVER_ECHO"}]
    elif location == "routing":
        state["branch:to:Market Analyst"] = {"instructions": "NEVER_ECHO"}
    elif location == "timezone":
        cp["ts"] = "2026-10-02T00:00:00"
    elif location == "id":
        cp["id"] = "NEVER_ECHO"
    elif location == "typed_object":
        state["market_report"] = {"__type__": "python", "constructor": "NEVER_ECHO"}
    elif location == "duplicate_write":
        envelope["pending_writes"].append(envelope["pending_writes"][0])
    elif location == "unversioned_seen":
        cp["versions_seen"]["Market Analyst"]["sender"] = 1
    with pytest.raises(CheckpointCodecError) as raised:
        codec.decode(json.dumps(envelope).encode())
    assert str(raised.value) == "snapshot checkpoint is invalid or incompatible"
    assert raised.value.__cause__ is None


@pytest.mark.parametrize("raw", [b"not-json", b'{"fingerprint":"a","fingerprint":"b"}',
    b"\x80\x04pickle", b"[" * 1000, b"{}" * (MAX_CHECKPOINT_BYTES // 2 + 1)])
def test_malformed_duplicate_recursive_and_oversized_bytes_fail_closed(codec, raw):
    with pytest.raises(CheckpointCodecError):
        codec.decode(raw)


def test_encoding_unknown_python_objects_never_calls_conversion_hooks(codec):
    class Forbidden:
        def __str__(self):
            raise AssertionError("arbitrary conversion executed")

        def __reduce__(self):
            raise AssertionError("pickle executed")

    original = checkpoint()
    original.checkpoint["channel_values"]["market_report"] = Forbidden()
    with pytest.raises(CheckpointCodecError):
        codec.encode(original)


def test_known_routing_pending_writes_preserve_order_and_task_identity(codec):
    original = checkpoint()
    original.checkpoint["channel_values"]["branch:to:Market Analyst"] = None
    original.checkpoint["channel_versions"]["branch:to:Market Analyst"] = "00002.25"
    original.pending_writes.append((str(uuid4()), "branch:to:Market Analyst", None))
    restored = codec.decode(codec.encode(original))
    assert restored.pending_writes[-1] == original.pending_writes[-1]
    assert restored.checkpoint["channel_values"]["branch:to:Market Analyst"] is None


def test_oversized_reader_text_is_rejected_not_truncated(codec):
    original = checkpoint()
    original.checkpoint["channel_values"]["market_report"] = "x" * (MAX_TEXT + 1)
    with pytest.raises(CheckpointCodecError):
        codec.encode(original)
    assert len(original.checkpoint["channel_values"]["market_report"]) == MAX_TEXT + 1
