"""Native scheduler sync durability and ACK failure behavior; no provider calls."""

import hashlib
from threading import Event, Thread
from typing import TypedDict
from uuid import uuid4

import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from tests.test_snapshot_checkpoint_codec import checkpoint
from tradingagents.platform.analysis.checkpoint_codec import SnapshotCheckpointCodec
from tradingagents.platform.analysis.checkpoint_saver import (
    CheckpointCommitError,
    CommittedSnapshotSaver,
)
from tradingagents.platform.analysis.checkpoint_store import CheckpointCommit


def receipt(raw):
    return CheckpointCommit(uuid4(), 1, hashlib.sha256(raw).hexdigest())


def test_every_native_put_and_pending_write_commits_only_filtered_json():
    codec = SnapshotCheckpointCodec(fingerprint="a" * 64, nodes={"Market Analyst"})
    commits = []

    def commit(raw):
        commits.append(raw)
        return receipt(raw)

    saver = CommittedSnapshotSaver(codec=codec, commit=commit)
    value = checkpoint()
    saved = saver.put({"configurable": {"thread_id": "fixture", "checkpoint_ns": ""}},
                      value.checkpoint, value.metadata, value.checkpoint["channel_versions"])
    saver.put_writes(saved, [("market_report", "Pending reader output")], str(uuid4()))
    assert len(commits) == 2
    for raw in commits:
        assert b"PRIVATE_RAW_MESSAGE" not in raw and b"PRIVATE_REASONING" not in raw
        codec.decode(raw)
    assert codec.decode(commits[-1]).pending_writes[0][2] == "Pending reader output"


def test_restore_retains_native_tuple_without_republishing_history():
    codec = SnapshotCheckpointCodec(fingerprint="a" * 64, nodes={"Market Analyst"})
    raw = codec.encode(checkpoint())
    commits = []
    saver = CommittedSnapshotSaver(codec=codec, commit=lambda data: commits.append(data))
    config = saver.restore(raw, expected_thread_id="fixture")
    assert codec.decode(codec.encode(saver.get_tuple(config))) == codec.decode(raw)
    assert not commits


@pytest.mark.parametrize("failure", ["thread", "fingerprint", "malformed", "occupied", "repeated"])
def test_restore_invalid_or_nonfresh_target_poisoned_without_commit(failure):
    codec = SnapshotCheckpointCodec(fingerprint="a" * 64, nodes={"Market Analyst"})
    raw = codec.encode(checkpoint())
    commits = []
    saver = CommittedSnapshotSaver(codec=codec, commit=lambda data: (commits.append(data), receipt(data))[1])
    if failure == "occupied":
        value = checkpoint()
        saver.put(value.config, value.checkpoint, value.metadata, value.checkpoint["channel_versions"])
    if failure == "repeated":
        saver.restore(raw, expected_thread_id="fixture")
    if failure == "fingerprint":
        raw = SnapshotCheckpointCodec(fingerprint="b" * 64, nodes={"Market Analyst"}).encode(checkpoint())
    if failure == "malformed":
        raw = b"PRIVATE_MALFORMED_BYTES"
    count = len(commits)
    with pytest.raises(CheckpointCommitError) as raised:
        saver.restore(raw, expected_thread_id="other" if failure == "thread" else "fixture")
    assert str(raised.value) == "snapshot checkpoint commit requires review"
    assert raised.value.__cause__ is None
    assert len(commits) == count
    with pytest.raises(CheckpointCommitError):
        saver.get_tuple({"configurable": {"thread_id": "fixture"}})


def test_partial_native_restore_failure_cannot_advance_or_republish(monkeypatch):
    codec = SnapshotCheckpointCodec(fingerprint="a" * 64, nodes={"Market Analyst"})
    raw = codec.encode(checkpoint())
    commits = []
    saver = CommittedSnapshotSaver(codec=codec, commit=lambda data: commits.append(data))

    def fail(*args, **kwargs):
        raise RuntimeError("PRIVATE_NATIVE_EXCEPTION")

    monkeypatch.setattr(InMemorySaver, "put_writes", fail)
    with pytest.raises(CheckpointCommitError) as raised:
        saver.restore(raw, expected_thread_id="fixture")
    assert raised.value.__cause__ is None
    assert "PRIVATE" not in str(raised.value)
    assert not commits
    with pytest.raises(CheckpointCommitError):
        list(saver.list(None))


@pytest.mark.parametrize("ack", ["exception", "none", "wrong_hash", "wrong_sequence",
    "bool_sequence", "float_sequence", "string_sequence", "string_record", "missing_record"])
def test_ambiguous_ack_poisoned_saver_cannot_be_reused(ack):
    codec = SnapshotCheckpointCodec(fingerprint="a" * 64, nodes={"Market Analyst"})

    def commit(raw):
        if ack == "exception":
            raise RuntimeError("PRIVATE_PAYLOAD_NEVER_ECHO")
        if ack == "none":
            return None
        value = receipt(raw)
        sequence = {"wrong_sequence": 0, "bool_sequence": True,
                    "float_sequence": 1.0, "string_sequence": "1"}.get(ack, 1)
        record = {"string_record": str(value.record_id), "missing_record": None}.get(ack, value.record_id)
        return CheckpointCommit(record, sequence,
                                "0" * 64 if ack == "wrong_hash" else value.content_hash)

    saver = CommittedSnapshotSaver(codec=codec, commit=commit)
    value = checkpoint()
    with pytest.raises(CheckpointCommitError) as raised:
        saver.put({"configurable": {"thread_id": "fixture", "checkpoint_ns": ""}},
                  value.checkpoint, value.metadata, value.checkpoint["channel_versions"])
    assert str(raised.value) == "snapshot checkpoint commit requires review"
    assert raised.value.__cause__ is None
    with pytest.raises(CheckpointCommitError):
        saver.get_tuple(value.config)
    with pytest.raises(CheckpointCommitError):
        list(saver.list(value.config))


class State(TypedDict):
    research_only: bool
    market_report: str


def test_sync_native_durability_blocks_next_node_until_commit_ack():
    entered, release, next_node, done = Event(), Event(), Event(), Event()
    errors = []
    codec = SnapshotCheckpointCodec(fingerprint="a" * 64, nodes={"Market Analyst", "News Analyst"})

    def commit(raw):
        value = codec.decode(raw)
        if value.checkpoint["channel_values"].get("market_report") == "first":
            entered.set()
            assert release.wait(5), "fixture ACK was never released"
        return receipt(raw)

    saver = CommittedSnapshotSaver(codec=codec, commit=commit)
    flow = StateGraph(State)
    flow.add_node("Market Analyst", lambda state: {"market_report": "first"})

    def second(state):
        next_node.set()
        return {"market_report": "second"}

    flow.add_node("News Analyst", second)
    flow.add_edge(START, "Market Analyst")
    flow.add_edge("Market Analyst", "News Analyst")
    flow.add_edge("News Analyst", END)
    graph = flow.compile(checkpointer=saver)

    def run():
        try:
            graph.invoke({"research_only": True, "market_report": ""},
                         {"configurable": {"thread_id": "fixture"}}, durability="sync")
        except Exception as error:
            errors.append(type(error).__name__)
        finally:
            done.set()

    thread = Thread(target=run)
    thread.start()
    try:
        assert entered.wait(5)
        assert not next_node.wait(.1) and not done.is_set()
    finally:
        release.set()
        thread.join(5)
    assert not thread.is_alive() and not errors and next_node.is_set()
