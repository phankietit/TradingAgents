"""Raw-source parsing/current scope/transport, no live vendor or model requests."""

import hashlib
import json
import sys
import time
from datetime import timedelta
from unittest.mock import Mock

import pytest

from tests.test_platform_fred import AAPL, NOW
from tradingagents.contracts import DataQualityStatus
from tradingagents.dataflows import platform_social as social
from tradingagents.platform.instruments.catalog import INITIAL_INSTRUMENT_CATALOG


def message(index=1, label="Bullish", **updates):
    row = {"id": index, "body": "Synthetic full retail opinion " + str(index),
        "created_at": (NOW-timedelta(hours=index)).isoformat(),
        "entities": {"sentiment": None if label == "unlabeled" else {"basic": label}},
        "user": {"username": "UNNEEDED_ACCOUNT_FIELD", "private_like_field": "NEVER_STORE"}}
    return {**row, **updates}


def envelope(rows=None, symbol="AAPL"):
    return json.dumps({"response": {"status": 200}, "symbol": {"symbol": symbol},
        "messages": [message(1), message(2, "Bearish"), message(3, "unlabeled")] if rows is None else rows}).encode()


def atom(*, published=None, updated=None, category="stocks", link="https://www.reddit.com/r/stocks/comments/abc/synthetic/"):
    published = published or (NOW-timedelta(hours=2)).isoformat()
    updated = updated or published
    return (f'<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>t3_abc</id>'
        f'<title>Synthetic complete discussion</title><published>{published}</published>'
        f'<updated>{updated}</updated><category term="{category}"/>'
        f'<link href="{link}"/><content type="html">&lt;p&gt;Complete discussion body&lt;/p&gt;</content>'
        '</entry></feed>').encode()


def collect(raw=None, vendor="stocktwits", instrument=AAPL, **kwargs):
    raw = envelope() if raw is None and vendor == "stocktwits" else atom() if raw is None else raw
    return social.collect_social(instrument, vendor, clock=lambda: NOW,
        fetch=lambda *_: raw, **kwargs)


@pytest.mark.parametrize("vendor", ["stocktwits", "reddit"])
def test_current_scope_original_window_and_full_raw_text(vendor):
    result = collect(vendor=vendor)
    assert result.quality_status is DataQualityStatus.OK
    assert result.window_start == NOW-timedelta(days=7)
    assert result.retrieved_at == NOW and result.requested_at == NOW
    assert result.received_posts == len(result.posts)
    assert "NEVER_STORE" not in result.model_dump_json() and "UNNEEDED_ACCOUNT_FIELD" not in result.model_dump_json()
    assert social.SocialCollection.model_validate_json(result.model_dump_json()) == result
    if vendor == "reddit":
        assert result.posts[0].label == "unlabeled" and result.posts[0].body == "Complete discussion body"
    else:
        assert len(result.posts) == 3 and {post.label for post in result.posts} == {"Bullish", "Bearish", "unlabeled"}


def test_no_cli_thirty_post_or_body_excerpt_truncation():
    rows = [message(index+1, created_at=(NOW-timedelta(minutes=index)).isoformat(), body="x"*1500)
            for index in range(80)]
    value = collect(envelope(rows))
    assert len(value.posts) == 80 and all(len(post.body) == 1500 for post in value.posts)


def test_exact_window_and_edit_cutoff_exclude_not_backdate():
    rows = [message(1, created_at=(NOW-timedelta(days=7)).isoformat()),
        message(2, created_at=(NOW-timedelta(days=7, microseconds=1)).isoformat()),
        message(3, created_at=(NOW+timedelta(microseconds=1)).isoformat())]
    value = collect(envelope(rows))
    assert len(value.posts) == 1 and value.posts[0].post_id == "1"
    assert value.received_posts == 3 and value.excluded_out_of_window == 2
    edited = collect(atom(updated=(NOW+timedelta(seconds=1)).isoformat()), vendor="reddit")
    assert edited.quality_status is DataQualityStatus.COVERAGE_GAP and not edited.posts


@pytest.mark.parametrize("raw", [b"null", b"[]", b"{}", b"private raw vendor error", b"\xff",
    envelope([message(1), message(1)]), envelope([message(body="")]), envelope([message(id=True)]),
    envelope([message(created_at="2026-10-03")]), envelope([message(created_at=None)]),
    envelope([message(1, "Neutral")]), envelope([message(body=5)]), envelope(symbol="MSFT"),
    envelope([None]), envelope([message(entities=[]) ]), b"x"*(social.MAX_BYTES+1),
    envelope().decode().replace('"status": 200', '"status": 503, "status": 200').encode(),
    envelope().decode().replace('"status": 200', '"status": NaN').encode(),
    envelope().decode().encode("utf-16")], ids=lambda raw: hashlib.sha256(raw).hexdigest()[:12])
def test_malformed_or_wrong_identity_feed_invalid_never_partial(raw):
    value = collect(raw)
    assert value.quality_status is DataQualityStatus.INVALID and not value.posts
    assert value.reason == "invalid_vendor_response" and value.invalid_records == 1
    assert value.received_posts is None  # Unknown, not fabricated zero/absence.
    assert "private raw vendor error" not in value.model_dump_json()


@pytest.mark.parametrize("raw", [b"<html/>", b'<!DOCTYPE feed [<!ENTITY x "secret">]><feed/>',
    atom(category="unknown"), atom(link="https://other.invalid/private"),
    atom(published="bad"), atom(updated="2020-01-01T00:00:00Z"),
    '<!DOCTYPE feed [<!ENTITY x "secret">]><feed/>'.encode("utf-16"),
    atom().decode().encode("utf-16")])
def test_invalid_reddit_no_labels_community_or_external_link(raw):
    value = collect(raw, vendor="reddit")
    assert value.quality_status is DataQualityStatus.INVALID and not value.posts


@pytest.mark.parametrize("vendor,empty", [("reddit", b'<feed xmlns="http://www.w3.org/2005/Atom"/>'),
    ("stocktwits", envelope([]))])
def test_reachable_empty_and_network_outage_are_not_equivalent(vendor, empty):
    assert collect(empty, vendor=vendor).quality_status is DataQualityStatus.NO_DATA
    failure = social.collect_social(AAPL, vendor, clock=lambda: NOW,
        fetch=Mock(side_effect=OSError("PRIVATE_DO_NOT_ECHO")))
    assert failure.quality_status is DataQualityStatus.UNAVAILABLE and failure.received_posts is None
    assert "PRIVATE_DO_NOT_ECHO" not in failure.model_dump_json()


def test_old_stream_is_coverage_gap_not_neutral_or_stale_current_claim():
    value = collect(envelope([message(created_at=(NOW-timedelta(days=20)).isoformat())]))
    assert value.quality_status is DataQualityStatus.COVERAGE_GAP and value.excluded_out_of_window == 1


@pytest.mark.parametrize("vendor,symbol", [("reddit", "BTC"), ("stocktwits", "BTC.X")])
def test_crypto_uses_original_alias_without_company_source(vendor, symbol):
    instrument = next(row.instrument for row in INITIAL_INSTRUMENT_CATALOG if row.instrument.canonical_symbol == "BTC-USD")
    fetch = Mock(return_value=atom() if vendor == "reddit" else envelope(symbol=symbol))
    value = social.collect_social(instrument, vendor, clock=lambda: NOW, fetch=fetch)
    fetch.assert_called_once_with(vendor, symbol)
    assert value.asset_class == "crypto" and value.provider_symbol == symbol


class Response:
    def __init__(self, body=None, status=200, headers=None):
        self.body, self.status_code, self.headers = envelope() if body is None else body, status, headers or {}
        self.closed = False
    def __enter__(self): return self
    def __exit__(self, *_): self.closed = True
    def iter_content(self, chunk_size):
        assert chunk_size == 8192
        yield self.body


@pytest.mark.parametrize("headers", [{"Content-Length": "-1"}, {"Content-Length": "2000001"},
    {"Content-Length": "bad"}, {"Content-Encoding": "gzip"}, {}])
def test_stream_fixed_options_limits_and_response_closure(monkeypatch, headers):
    response = Response(body=envelope() if headers else b"x"*(social.MAX_BYTES+1), headers=headers)
    def get(url, **options):
        assert url == social.stocktwits._API.format(ticker="AAPL")
        assert options == {"headers": {"User-Agent": social.stocktwits._UA, "Accept-Encoding": "identity"},
                           "timeout": 15, "stream": True, "allow_redirects": False}
        return response
    monkeypatch.setattr(social.requests, "get", get)
    with pytest.raises(social.SocialPreparationError, match="^invalid$"):
        social._fetch("stocktwits", "AAPL")
    assert response.closed


def test_reddit_one_bounded_retry_closes_before_backoff(monkeypatch):
    first, second = Response(status=429, headers={"Retry-After": "0"}), Response(body=atom())
    responses = iter([first, second])
    monkeypatch.setattr(social.requests, "get", lambda *_args, **_kwargs: next(responses))
    def sleep(seconds):
        assert seconds == 0 and first.closed
    monkeypatch.setattr(social.time, "sleep", sleep)
    assert social._fetch("reddit", "AAPL") == atom() and second.closed


@pytest.mark.parametrize("status", [301, 400, 401, 403, 429, 503])
def test_http_failure_not_empty(monkeypatch, status):
    response = Response(status=status)
    monkeypatch.setattr(social.requests, "get", lambda *_args, **_kwargs: response)
    with pytest.raises(social.SocialPreparationError, match="^unavailable$"):
        social._fetch("stocktwits", "AAPL")
    assert response.closed


def test_supervised_wrapper_fixed_command_no_secrets_and_full_identity(monkeypatch):
    def child(command, body, *, deadline):
        assert command == [sys.executable, "-m", "tradingagents.dataflows.platform_social"]
        request = json.loads(body)
        assert set(request) == {"instrument", "vendor", "analysis_as_of"}
        return collect().model_dump(mode="json")
    monkeypatch.setattr(social, "_child_json", child)
    assert social.fetch_current_social(AAPL, "stocktwits", analysis_as_of=NOW) == collect()


@pytest.mark.parametrize("update", [{"venue": "wrong"}, {"canonical_symbol": "MSFT"},
    {"requested_at": NOW-timedelta(seconds=1)}, {"retrieved_at": NOW+timedelta(days=2000)},
    {"quality_status": "OK", "posts": []}])
def test_supervised_wrong_scope_refuses_before_admission(monkeypatch, update):
    raw = collect().model_dump(mode="json")
    raw.update(update)
    monkeypatch.setattr(social, "_child_json", lambda *_args, **_kwargs: raw)
    with pytest.raises(social.SocialPreparationError, match="^invalid$"):
        social.fetch_current_social(AAPL, "stocktwits", analysis_as_of=NOW)


def test_parent_late_validation_and_child_failure_preserve_fixed_codes(monkeypatch):
    monkeypatch.setattr(social, "_child_json", lambda *_args, **_kwargs: collect().model_dump(mode="json"))
    times = iter([0, 100])
    monkeypatch.setattr(social.time, "monotonic", lambda: next(times))
    with pytest.raises(social.SocialPreparationError, match="^unavailable$"):
        social.fetch_current_social(AAPL, "stocktwits", analysis_as_of=NOW)


def test_model_copy_cannot_bypass_quality_or_cutoff():
    value = collect()
    for update in ({"received_posts": 0}, {"communities": ("stocks",)}, {"window_start": NOW},
        {"quality_status": "NO_DATA"}, {"provider_symbol": "MSFT"}):
        with pytest.raises(ValueError):
            social.SocialCollection.model_validate(value.model_copy(update=update).model_dump())


@pytest.mark.parametrize("vendor", ["reddit", "stocktwits"])
def test_native_main_bounded_stdio_original_parser_no_network(vendor):
    """Actual child/main/pipe shutdown, with explicitly synthetic HTTP bytes."""
    raw = atom() if vendor == "reddit" else envelope()
    program = "\n".join([
        "from tradingagents.dataflows import platform_social as social",
        f"body = {raw!r}",
        "class Response:",
        "    status_code = 200",
        "    headers = {}",
        "    def __enter__(self): return self",
        "    def __exit__(self, *_): pass",
        "    def iter_content(self, chunk_size): yield body",
        "social.requests.get = lambda *_args, **_kwargs: Response()",
        "social.main()",
    ])
    request = social.SocialAcquisitionRequest(instrument=AAPL, vendor=vendor, analysis_as_of=NOW)
    document = social._child_json([sys.executable, "-c", program], request.model_dump_json().encode(),
        deadline=time.monotonic()+20)
    result = social.SocialCollection.model_validate(document)
    expected = collect(vendor=vendor)
    assert result.posts == expected.posts and result.received_posts == expected.received_posts
    assert result.requested_at == NOW and result.retrieved_at >= NOW
    assert result.quality_status is DataQualityStatus.OK


def test_native_main_invalid_input_no_vendor_or_raw_echo():
    program = "\n".join([
        "from tradingagents.dataflows import platform_social as social",
        "def forbidden(*_args, **_kwargs): raise AssertionError('must not fetch')",
        "social.requests.get = forbidden",
        "social.main()",
    ])
    result = social._child_json([sys.executable, "-c", program], b'{"private":"DO_NOT_ECHO"}',
        deadline=time.monotonic()+20)
    assert result == {"error": "unavailable"}
