"""Bounded transport/native subprocess proof; no vendor or model requests."""

import json
import subprocess
import sys
import threading
import time
from datetime import timedelta

import pytest

from tests.test_platform_fred import AAPL, NOW, collect
from tradingagents.dataflows import platform_fred as fred


class Response:
    status_code = 200

    def __init__(self, chunks, headers=None):
        self.chunks, self.headers = chunks, headers or {}
        self.closed = False
        self.reads = 0

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.closed = True

    def iter_content(self, chunk_size):
        assert chunk_size == 8192
        for chunk in self.chunks:
            self.reads += 1
            yield chunk


def wire(monkeypatch, response):
    import requests

    def get(url, **kwargs):
        assert url == f"{fred.FRED_API_BASE}/series"
        assert kwargs == {"params": {"series_id": "DGS10", "api_key": "SYNTHETIC_KEY",
                                     "file_type": "json"},
                          "headers": {"Accept-Encoding": "identity"},
                          "stream": True, "allow_redirects": False, "timeout": 30}
        return response

    monkeypatch.setattr(fred, "get_api_key", lambda: "SYNTHETIC_KEY")
    monkeypatch.setattr(requests, "get", get)


def test_stream_uses_existing_host_and_closes_response(monkeypatch):
    response = Response([b'{"seriess":', b"[]}"])
    wire(monkeypatch, response)
    assert fred._stream_request("series", {"series_id": "DGS10"}) == {"seriess": []}
    assert response.closed and response.reads == 2


@pytest.mark.parametrize("headers", [{"Content-Length": "2000001"},
    {"Content-Length": "-1"}, {"Content-Length": "bad"}, {"Content-Encoding": "gzip"}])
def test_headers_reject_before_buffering(monkeypatch, headers):
    response = Response([b"PRIVATE_DO_NOT_ECHO"], headers)
    wire(monkeypatch, response)
    with pytest.raises(fred.InvalidFredResponse, match="^invalid_vendor_response$"):
        fred._stream_request("series", {"series_id": "DGS10"})
    assert response.closed and response.reads == 0


@pytest.mark.parametrize("chunks", [[b"x" * 1_000_000, b"x" * 1_000_001, b"NEVER_READ"],
    [b"PRIVATE_DO_NOT_ECHO"], [b"\xff"], [b"[" * 10000]])
def test_body_limits_and_parser_failures_do_not_echo_payload(monkeypatch, chunks):
    response = Response(chunks)
    wire(monkeypatch, response)
    with pytest.raises(fred.InvalidFredResponse, match="^invalid_vendor_response$"):
        fred._stream_request("series", {"series_id": "DGS10"})
    assert response.closed
    if len(chunks) == 3:
        assert response.reads == 2


@pytest.mark.parametrize("status", [301, 400, 401, 429, 503])
def test_http_failure_is_unavailable_not_empty(monkeypatch, status):
    response = Response([b"PRIVATE_DO_NOT_ECHO"])
    response.status_code = status
    wire(monkeypatch, response)
    with pytest.raises(fred.MacroPreparationError, match="^unavailable$"):
        fred._stream_request("series", {"series_id": "DGS10"})
    assert response.closed and response.reads == 0


@pytest.mark.parametrize("path", ["https://other.invalid", "../series", "release"])
def test_transport_path_is_not_a_network_destination(monkeypatch, path):
    monkeypatch.setattr(fred, "get_api_key", lambda: pytest.fail("path reached key"))
    with pytest.raises(ValueError, match="invalid FRED path"):
        fred._stream_request(path, {})


@pytest.fixture
def children(monkeypatch):
    original, children = subprocess.Popen, []

    def spawn(*args, **kwargs):
        child = original(*args, **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(fred.subprocess, "Popen", spawn)
    yield children
    assert children
    for child in children:
        assert child.poll() is not None and child.stdin.closed and child.stdout.closed
    assert not any(thread.name.startswith("fred-") for thread in threading.enumerate())


def test_native_child_reads_full_request_then_exits(children):
    command = [sys.executable, "-c", "import sys,json; print(json.dumps({'size':len(sys.stdin.buffer.read())}))"]
    assert fred._child_json(command, b"x" * 16384, wall_seconds=3) == {"size": 16384}


@pytest.mark.parametrize("script,code", [
    ("import time; time.sleep(30)", "unavailable"),
    ("import os,time; os.close(1); time.sleep(30)", "unavailable"),
    ("import sys,time; sys.stdout.write('{}'); sys.stdout.flush(); time.sleep(30)", "unavailable"),
    ("import sys,time\nwhile True:\n sys.stdout.write(' '); sys.stdout.flush(); time.sleep(.01)", "unavailable"),
    ("import sys; sys.stdin.buffer.read(); print('{}'); sys.exit(2)", "unavailable"),
    ("import sys; sys.stdin.buffer.read(); print('PRIVATE_DO_NOT_ECHO')", "invalid"),
    ("import sys; sys.stdin.buffer.read(); print('x'*200001)", "invalid"),
])
def test_actual_hang_trickle_nonzero_and_oversize_are_reaped(children, script, code):
    started = time.monotonic()
    with pytest.raises(fred.MacroPreparationError, match=f"^{code}$"):
        fred._child_json([sys.executable, "-c", script], b"{}", wall_seconds=.4, max_bytes=200000)
    assert time.monotonic() - started < 3


@pytest.mark.parametrize("fail_start", [1, 2])
def test_thread_start_failure_still_reaps_child(monkeypatch, children, fail_start):
    original, calls = threading.Thread.start, []

    def start(thread):
        calls.append(thread)
        if len(calls) == fail_start:
            raise RuntimeError("PRIVATE_DO_NOT_ECHO")
        return original(thread)

    monkeypatch.setattr(threading.Thread, "start", start)
    with pytest.raises(fred.MacroPreparationError, match="^unavailable$"):
        fred._child_json([sys.executable, "-c", "import time; time.sleep(30)"], b"{}")


def test_thread_construction_failure_still_reaps_child(monkeypatch, children):
    def broken(*_args, **_kwargs):
        raise RuntimeError("PRIVATE_DO_NOT_ECHO")

    monkeypatch.setattr(fred.threading, "Thread", broken)
    with pytest.raises(fred.MacroPreparationError, match="^unavailable$"):
        fred._child_json([sys.executable, "-c", "import time; time.sleep(30)"], b"{}")


def test_oversized_input_and_elapsed_deadline_refuse_before_spawn(monkeypatch):
    monkeypatch.setattr(fred.subprocess, "Popen", lambda *_args, **_kwargs: pytest.fail("spawned"))
    with pytest.raises(fred.MacroPreparationError, match="^invalid$"):
        fred._child_json([], b"x" * 16385)
    with pytest.raises(fred.MacroPreparationError, match="^unavailable$"):
        fred._child_json([], b"{}", deadline=time.monotonic() - 1)


def test_parent_withholds_collection_returned_after_whole_acquisition_deadline(monkeypatch):
    monkeypatch.setattr(fred, "get_api_key", lambda: "SYNTHETIC_KEY")
    monkeypatch.setattr(fred, "_child_json", lambda *_args, **_kwargs: collect().model_dump(mode="json"))
    times = iter([0, 100])
    monkeypatch.setattr(fred.monotonic_time, "monotonic", lambda: next(times))
    with pytest.raises(fred.MacroPreparationError, match="^unavailable$"):
        fred.fetch_current_fred_series(AAPL, "DGS10", analysis_as_of=NOW)


@pytest.mark.parametrize("update", [{"error": "invalid"}, {"error": "unavailable"}, [],
    {"venue": "wrong"}, {"series_id": "OTHER"},
    {"retrieved_at": NOW + timedelta(days=1000)},
    {"observation_start": NOW.date() - timedelta(days=367)}])
def test_supervised_collection_rechecks_scope_without_raw_failure(monkeypatch, update):
    monkeypatch.setattr(fred, "get_api_key", lambda: "SYNTHETIC_KEY")
    raw = collect().model_dump(mode="json")
    expected = "invalid"
    if type(update) is list or "error" in update:
        raw = update
        if update == {"error": "unavailable"}:
            expected = "unavailable"
    else:
        raw.update(update)
    monkeypatch.setattr(fred, "_child_json", lambda *_args, **_kwargs: raw)
    with pytest.raises(fred.MacroPreparationError, match=f"^{expected}$"):
        fred.fetch_current_fred_series(AAPL, "DGS10", analysis_as_of=NOW)


def test_current_wrapper_passes_fixed_command_no_key_and_original_window(monkeypatch):
    monkeypatch.setattr(fred, "get_api_key", lambda: "SYNTHETIC_KEY")

    def child(command, payload, *, deadline):
        assert command == [sys.executable, "-m", "tradingagents.dataflows.platform_fred"]
        assert b"SYNTHETIC_KEY" not in payload
        assert json.loads(payload)["lookback_days"] == 365
        assert deadline > time.monotonic()
        return collect().model_dump(mode="json")

    monkeypatch.setattr(fred, "_child_json", child)
    assert fred.fetch_current_fred_series(AAPL, "DGS10", analysis_as_of=NOW) == collect()


def test_missing_key_refuses_before_spawn(monkeypatch):
    from tradingagents.dataflows.fred import FredNotConfiguredError

    def missing():
        raise FredNotConfiguredError("PRIVATE_DO_NOT_ECHO")

    monkeypatch.setattr(fred, "get_api_key", missing)
    monkeypatch.setattr(fred, "_child_json", lambda *_args, **_kwargs: pytest.fail("spawned"))
    with pytest.raises(fred.MacroPreparationError, match="^unavailable$"):
        fred.fetch_current_fred_series(AAPL, "DGS10")
