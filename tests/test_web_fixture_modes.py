import argparse
import json

import pytest

from scripts.web_fixture import FailedSyntheticGraph, fixture_session_seconds


@pytest.mark.parametrize("value", ["300", "3600", "43200"])
def test_fixture_ttl_is_explicit_and_bounded(value):
    assert fixture_session_seconds(value) == int(value)


@pytest.mark.parametrize("value", ["0", "-1", "10", "299", "43201"])
def test_fixture_rejects_invalid_ttl(value):
    with pytest.raises(argparse.ArgumentTypeError):
        fixture_session_seconds(value)


def test_failed_fixture_has_no_live_fallback():
    graph = FailedSyntheticGraph(snapshot_reports={"market": json.dumps([{"snapshot_id": "synthetic"}])})
    assert not hasattr(graph, "propagate")
    with pytest.raises(RuntimeError, match="no provider was contacted"):
        graph.propagate_snapshots()
