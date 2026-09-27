from datetime import datetime, timedelta, timezone

import pytest

from tradingagents.contracts import DataQualityStatus
from tradingagents.dataflows.platform_news import NewsCollection, collect_yahoo_news
from tradingagents.platform.instruments import INITIAL_INSTRUMENT_CATALOG

NOW = datetime(2026, 9, 27, 12, tzinfo=timezone.utc)
INSTRUMENT = next(item.instrument for item in INITIAL_INSTRUMENT_CATALOG
                  if item.instrument.canonical_symbol == "AAPL")


def article(at=NOW, url="https://example.com/news"):
    return {"content":{"title":"Research update", "summary":"Untrusted source text",
        "provider":{"displayName":"Fixture publisher"}, "canonicalUrl":{"url":url},
        "pubDate":at.isoformat()}}


def collect(raw):
    ticks = iter([NOW, NOW + timedelta(seconds=2)])
    return collect_yahoo_news(INSTRUMENT, clock=lambda: next(ticks), fetch=lambda *_: raw)


def test_recent_collection_has_observation_provenance_and_no_historical_claim():
    result = collect([article(NOW-timedelta(days=1)), article(NOW-timedelta(days=1))])
    assert result.quality_status is DataQualityStatus.OK
    assert len(result.articles) == 1
    assert result.retrieved_at > result.requested_at
    assert result.coverage == "recent_feed_not_exhaustive"
    assert result.retrieval_path == "Ticker.get_news"
    assert (result.asset_class, result.venue, result.quote_currency, result.timezone) == (
        INSTRUMENT.asset_class.value, INSTRUMENT.venue, INSTRUMENT.quote_currency, INSTRUMENT.timezone)
    assert NewsCollection.model_validate_json(result.model_dump_json()) == result


@pytest.mark.parametrize("raw,status", [
    ([], DataQualityStatus.NO_DATA), (None, DataQualityStatus.INVALID),
    ({}, DataQualityStatus.INVALID), ([{}], DataQualityStatus.INVALID),
    ([article(NOW + timedelta(seconds=1))], DataQualityStatus.COVERAGE_GAP),
    ([article(NOW - timedelta(days=8))], DataQualityStatus.COVERAGE_GAP),
])
def test_failure_states_are_not_neutral_or_silently_usable(raw, status):
    result = collect(raw)
    assert result.quality_status is status and not result.articles


@pytest.mark.parametrize("mutate", [
    lambda item: item["content"].update(pubDate="2026-09-27T11:00:00"),
    lambda item: item["content"].update(pubDate=None),
    lambda item: item["content"].update(provider=None),
    lambda item: item["content"].update(canonicalUrl={"url":"javascript:alert(1)"}),
    lambda item: item["content"].update(title=" "),
])
def test_malformed_record_cannot_hide_in_a_good_feed(mutate):
    bad = article(url="https://example.com/bad")
    mutate(bad)
    result = collect([article(), bad])
    assert result.quality_status is DataQualityStatus.INVALID
    assert result.invalid_records == 1 and not result.articles


def test_vendor_failure_does_not_leak_exception_or_become_no_data():
    def fail(*_):
        raise RuntimeError("secret fixture credential")
    result = collect_yahoo_news(INSTRUMENT, clock=lambda: NOW, fetch=fail)
    assert result.quality_status is DataQualityStatus.UNAVAILABLE
    assert "secret" not in result.model_dump_json()


def test_cutoff_is_request_start_not_end_of_network_call():
    result = collect([article(), article(NOW+timedelta(seconds=1), "https://example.com/future")])
    assert len(result.articles) == 1 and result.excluded_out_of_window == 1


def test_bounds_and_clock_are_validated_before_fetch():
    def unexpected(*_):
        pytest.fail("must not fetch")
    for options in ({"lookback_days":0}, {"article_limit":201}):
        with pytest.raises(ValueError):
            collect_yahoo_news(INSTRUMENT, fetch=unexpected, **options)
    with pytest.raises(ValueError):
        collect_yahoo_news(INSTRUMENT, fetch=unexpected, clock=lambda: NOW.replace(tzinfo=None))


def test_collection_contract_rejects_backdating_and_future_articles():
    data = collect([article()]).model_dump()
    for patch in ({"retrieved_at":NOW-timedelta(seconds=1)},
                  {"requested_at":NOW-timedelta(seconds=1)},
                  {"quality_status":DataQualityStatus.NO_DATA}):
        with pytest.raises(ValueError):
            NewsCollection.model_validate({**data, **patch})


def test_default_adapter_calls_existing_yahoo_method_without_fallback(monkeypatch):
    from tradingagents.dataflows import platform_news
    calls = []
    class Ticker:
        def __init__(self, symbol):
            calls.append(symbol)
        def get_news(self, *, count):
            calls.append(count)
            return [article()]
    monkeypatch.setattr(platform_news.yf, "Ticker", Ticker)
    monkeypatch.setattr(platform_news, "yf_retry", lambda call: call())
    result = collect_yahoo_news(INSTRUMENT, clock=lambda: NOW, article_limit=25)
    assert result.quality_status is DataQualityStatus.OK
    assert calls == ["AAPL", 25]
