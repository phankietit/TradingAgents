"""Native scheduler sync durability and ACK failure behavior; no provider calls."""

import hashlib
from threading import Event, Thread
from typing import TypedDict
from uuid import uuid4

import pytest
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


@pytest.mark.parametrize("ack", ["exception", "none", "wrong_hash", "wrong_sequence"])
def test_ambiguous_ack_poisoned_saver_cannot_be_reused(ack):
    codec = SnapshotCheckpointCodec(fingerprint="a" * 64, nodes={"Market Analyst"})

    def commit(raw):
        if ack == "exception":
            raise RuntimeError("PRIVATE_PAYLOAD_NEVER_ECHO")
        if ack == "none":
            return None
        value = receipt(raw)
        return CheckpointCommit(value.record_id, 0 if ack == "wrong_sequence" else 1,
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
