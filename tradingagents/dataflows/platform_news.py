"""Current-vintage Yahoo news collection for immutable platform evidence.

No historical as-of parameter: publication dates do not prove that today's
article text was available in the past. Persistence must use retrieved_at.
This adapter does not replace the legacy CLI or silently select a provider.
"""

import contextlib
import json
import subprocess
import sys
from datetime import datetime, timedelta
from typing import Literal
from uuid import UUID

import yfinance as yf
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, HttpUrl, model_validator

from tradingagents._compat import UTC
from tradingagents.contracts import DataQualityStatus, InstrumentContract
from tradingagents.dataflows.platform_prices import approved_symbol
from tradingagents.dataflows.stockstats_utils import yf_retry
from tradingagents.dataflows.yfinance_news import _extract_article_data


class NewsPreparationError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class NewsArticle(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    title: str = Field(min_length=1, max_length=1000)
    summary: str = Field(max_length=50000)
    publisher: str = Field(min_length=1, max_length=500)
    url: HttpUrl
    published_at: AwareDatetime


class NewsCollection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    dataset: Literal["news"] = "news"
    vendor: Literal["yfinance"] = "yfinance"
    retrieval_path: Literal["Ticker.get_news"] = "Ticker.get_news"
    instrument_id: UUID
    canonical_symbol: str
    asset_class: str
    venue: str
    quote_currency: str
    timezone: str
    requested_at: AwareDatetime
    retrieved_at: AwareDatetime
    window_start: AwareDatetime
    coverage: Literal["recent_feed_not_exhaustive"] = "recent_feed_not_exhaustive"
    quality_status: DataQualityStatus
    reason: str
    articles: tuple[NewsArticle, ...] = ()
    excluded_out_of_window: int = Field(default=0, ge=0)
    invalid_records: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def eligible(self):
        if not self.window_start <= self.requested_at <= self.retrieved_at:
            raise ValueError("invalid news observation window")
        if any(not self.window_start <= article.published_at <= self.requested_at
               for article in self.articles):
            raise ValueError("article outside requested publication window")
        if len({str(article.url) for article in self.articles}) != len(self.articles):
            raise ValueError("duplicate news article")
        if (self.quality_status is DataQualityStatus.OK) != bool(self.articles):
            raise ValueError("only nonempty eligible articles may have OK status")
        if self.invalid_records and self.quality_status is DataQualityStatus.OK:
            raise ValueError("malformed feed cannot be marked OK")
        return self


def collect_yahoo_news(instrument: InstrumentContract, *, lookback_days=7,
                       article_limit=100, clock=lambda: datetime.now(UTC), fetch=None):
    """Explicit Yahoo-only collection; never mutate or backdate prior evidence.

    OK means usable recent articles, NOT complete coverage of the whole window.
    Feed truncation and unpublished items cannot be inferred from Yahoo results.
    ``fetch`` and ``clock`` are dependency-injection seams, not fallback vendors.
    """
    if not 1 <= lookback_days <= 30 or not 1 <= article_limit <= 200:
        raise ValueError("news collection bounds exceeded")
    symbol = approved_symbol(instrument)
    started = clock()
    if started.tzinfo is None or started.utcoffset() is None:
        raise ValueError("news clock must be timezone aware")
    start = started - timedelta(days=lookback_days)
    base = {"instrument_id":instrument.instrument_id,
            "canonical_symbol":instrument.canonical_symbol, "requested_at":started,
            "asset_class":instrument.asset_class.value, "venue":instrument.venue,
            "quote_currency":instrument.quote_currency, "timezone":instrument.timezone,
            "window_start":start}
    try:
        raw = (fetch(symbol, article_limit) if fetch is not None
               else yf_retry(lambda: yf.Ticker(symbol).get_news(count=article_limit)))
    except Exception:
        # Vendor text can contain credentials/URLs. Retain a stable reason only.
        return NewsCollection(**base, retrieved_at=clock(),
            quality_status=DataQualityStatus.UNAVAILABLE, reason="vendor_request_failed")
    observed = clock()
    if not isinstance(raw, list) or len(raw) > article_limit:
        return NewsCollection(**base, retrieved_at=observed,
            quality_status=DataQualityStatus.INVALID, reason="invalid_feed_envelope")
    articles, seen, invalid, excluded = [], set(), 0, 0
    for item in raw:
        try:
            data = _extract_article_data(item)
            article = NewsArticle(title=data["title"].strip(), summary=data["summary"],
                publisher=data["publisher"].strip(), url=data["link"], published_at=data["pub_date"])
            if article.title == "No title" or article.publisher == "Unknown":
                raise ValueError("missing article attribution")
        except (ValueError, TypeError, AttributeError, KeyError):
            invalid += 1
            continue
        if not start <= article.published_at <= started:
            excluded += 1
            continue
        if str(article.url) not in seen:
            seen.add(str(article.url))
            articles.append(article)
    if invalid:
        status, reason, articles = DataQualityStatus.INVALID, "malformed_article_records", []
    elif articles:
        status, reason = DataQualityStatus.OK, "eligible_recent_articles_not_exhaustive"
    elif raw:
        status, reason = DataQualityStatus.COVERAGE_GAP, "no_articles_in_requested_window"
    else:
        status, reason = DataQualityStatus.NO_DATA, "empty_vendor_feed"
    return NewsCollection(**base, retrieved_at=observed, quality_status=status,
        reason=reason, articles=tuple(sorted(articles, key=lambda item: item.published_at)),
        excluded_out_of_window=excluded, invalid_records=invalid)


def fetch_current_yahoo_news(instrument: InstrumentContract) -> NewsCollection:
    """Isolate vendor access and cap the entire acquisition at 45 seconds."""
    approved_symbol(instrument)
    try:
        result = subprocess.run(
            [sys.executable, "-m", __name__],
            input=instrument.model_dump_json(),
            text=True,
            capture_output=True,
            timeout=45,
            check=False,
        )
        if result.returncode:
            raise NewsPreparationError("unavailable")
        if len(result.stdout) > 2_000_000:
            raise NewsPreparationError("invalid")
        value = json.loads(result.stdout)
        if "error" in value:
            raise NewsPreparationError("unavailable")
        collection = NewsCollection.model_validate(value)
        if collection.instrument_id != instrument.instrument_id:
            raise NewsPreparationError("invalid")
        return collection
    except NewsPreparationError:
        raise
    except (subprocess.TimeoutExpired, OSError, ValueError) as error:
        raise NewsPreparationError("unavailable") from error


def main():
    try:
        instrument = InstrumentContract.model_validate_json(sys.stdin.read(16_384))
        with contextlib.redirect_stdout(sys.stderr):
            result = collect_yahoo_news(instrument)
        output = result.model_dump(mode="json")
    except Exception:
        output = {"error": "unavailable"}
    print(json.dumps(output, allow_nan=False))


if __name__ == "__main__":
    main()
