"""Current-only structured social evidence from the original public sources.

No CLI change, historical feed claim, inferred sentiment or fallback vendor.
All eligible returned text is retained; bounds refuse rather than truncate.
"""

import contextlib
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Literal
from uuid import UUID

import requests
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, HttpUrl, model_validator

from tradingagents._compat import UTC
from tradingagents.contracts import DataQualityStatus, InstrumentContract
from tradingagents.dataflows import reddit, stocktwits
from tradingagents.dataflows.platform_fred import MacroPreparationError, _child_json
from tradingagents.dataflows.platform_prices import approved_symbol
from tradingagents.dataflows.symbol_utils import crypto_base

MAX_BYTES = 2_000_000
MAX_POSTS = 1000
WINDOW_DAYS = 7
Vendor = Literal["reddit", "stocktwits"]


class SocialPreparationError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


class SocialPost(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    post_id: str = Field(min_length=1, max_length=200)
    title: str = Field(default="", max_length=2000)
    body: str = Field(max_length=100_000)
    published_at: AwareDatetime
    updated_at: AwareDatetime | None = None
    community: str | None = Field(default=None, max_length=100)
    url: HttpUrl | None = None
    label: Literal["Bullish", "Bearish", "unlabeled"] = "unlabeled"

    @model_validator(mode="after")
    def valid_post(self):
        if not self.title.strip() and not self.body.strip():
            raise ValueError("empty social post")
        if self.updated_at is not None and self.updated_at < self.published_at:
            raise ValueError("social edit precedes publication")
        if self.url is not None and (self.url.host not in {"www.reddit.com", "reddit.com"}
                or self.url.scheme != "https" or self.url.username or self.url.password
                or self.url.port not in {None, 443}):
            raise ValueError("invalid social source link")
        return self


class SocialCollection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    dataset: Literal["social"] = "social"
    vendor: Vendor
    retrieval_path: Literal["combined_subreddit_search_rss", "public_symbol_stream"]
    instrument_id: UUID
    canonical_symbol: str
    asset_class: str
    venue: str
    quote_currency: str
    timezone: str
    provider_symbol: str
    requested_at: AwareDatetime
    retrieved_at: AwareDatetime
    window_start: AwareDatetime
    coverage: Literal["recent_sample_not_exhaustive_not_historical"] = "recent_sample_not_exhaustive_not_historical"
    communities: tuple[str, ...] = ()
    quality_status: DataQualityStatus
    reason: Literal["eligible_recent_posts_not_exhaustive", "empty_vendor_feed",
        "no_posts_in_requested_window", "vendor_request_failed", "invalid_vendor_response"]
    posts: tuple[SocialPost, ...] = Field(default=(), max_length=MAX_POSTS)
    received_posts: int | None = Field(default=None, ge=0, le=MAX_POSTS, strict=True)
    excluded_out_of_window: int = Field(default=0, ge=0, le=MAX_POSTS, strict=True)
    invalid_records: int = Field(default=0, ge=0, le=MAX_POSTS, strict=True)

    @model_validator(mode="after")
    def valid_collection(self):
        expected = {"reddit": ("combined_subreddit_search_rss", crypto_base(self.canonical_symbol) or self.canonical_symbol,
                               reddit.DEFAULT_SUBREDDITS),
                    "stocktwits": ("public_symbol_stream", stocktwits._stocktwits_symbol(self.canonical_symbol), ())}
        if (self.retrieval_path, self.provider_symbol, self.communities) != expected[self.vendor]:
            raise ValueError("social request scope mismatch")
        if self.window_start != self.requested_at - timedelta(days=WINDOW_DAYS) or self.requested_at > self.retrieved_at:
            raise ValueError("invalid social observation window")
        ids = [post.post_id for post in self.posts]
        if len(ids) != len(set(ids)) or list(self.posts) != sorted(self.posts, key=lambda post: (post.published_at, post.post_id)):
            raise ValueError("duplicate or unordered social posts")
        if any(not self.window_start <= post.published_at <= self.requested_at
               or (post.updated_at is not None and post.updated_at > self.requested_at) for post in self.posts):
            raise ValueError("social content outside cutoff")
        if self.vendor == "reddit" and any(post.label != "unlabeled" or post.community not in self.communities
                                            or post.url is None for post in self.posts):
            raise ValueError("Reddit feed has no sentiment labels or engagement counts")
        if self.vendor == "stocktwits" and any(post.community is not None or post.url is not None for post in self.posts):
            raise ValueError("StockTwits unsupported post attribution")
        semantics = {
            "eligible_recent_posts_not_exhaustive": DataQualityStatus.OK,
            "empty_vendor_feed": DataQualityStatus.NO_DATA,
            "no_posts_in_requested_window": DataQualityStatus.COVERAGE_GAP,
            "vendor_request_failed": DataQualityStatus.UNAVAILABLE,
            "invalid_vendor_response": DataQualityStatus.INVALID,
        }
        if self.quality_status is not semantics[self.reason] or (self.quality_status is DataQualityStatus.OK) != bool(self.posts):
            raise ValueError("invalid social quality semantics")
        if self.invalid_records and self.quality_status is not DataQualityStatus.INVALID:
            raise ValueError("malformed social rows cannot be usable")
        if (self.quality_status in {DataQualityStatus.OK, DataQualityStatus.NO_DATA, DataQualityStatus.COVERAGE_GAP}
                and self.received_posts != len(self.posts) + self.excluded_out_of_window):
            raise ValueError("social received count mismatch")
        if self.reason == "empty_vendor_feed" and self.received_posts:
            raise ValueError("nonempty feed is not silence")
        if len(self.model_dump_json().encode()) > MAX_BYTES:
            raise ValueError("social payload exceeds bound")
        return self


def _scope(instrument, vendor):
    symbol = approved_symbol(instrument)
    if vendor not in {"reddit", "stocktwits"}:
        raise SocialPreparationError("unsupported")
    return {"vendor": vendor, "instrument_id": instrument.instrument_id,
        "canonical_symbol": instrument.canonical_symbol, "asset_class": instrument.asset_class.value,
        "venue": instrument.venue, "quote_currency": instrument.quote_currency, "timezone": instrument.timezone,
        "provider_symbol": (crypto_base(symbol) or symbol) if vendor == "reddit" else stocktwits._stocktwits_symbol(symbol),
        "retrieval_path": "combined_subreddit_search_rss" if vendor == "reddit" else "public_symbol_stream",
        "communities": reddit.DEFAULT_SUBREDDITS if vendor == "reddit" else ()}


def _fetch(vendor, symbol):
    """Original fixed public endpoints/UA, no redirect, unbounded body or fallback."""
    url = (reddit._RSS.format(sub="+".join(reddit.DEFAULT_SUBREDDITS), qs=reddit._search_qs(symbol, reddit._FEED_PAGE))
           if vendor == "reddit" else stocktwits._API.format(ticker=symbol))
    ua = reddit._UA if vendor == "reddit" else stocktwits._UA
    # Keep the original Reddit single bounded Retry-After/backoff semantics.
    for attempt in range(2 if vendor == "reddit" else 1):
        with requests.get(url, headers={"User-Agent": ua, "Accept-Encoding": "identity"},
                          timeout=15, stream=True, allow_redirects=False) as response:
            if response.status_code == 429 and vendor == "reddit" and attempt == 0:
                try:
                    delay = float(response.headers.get("Retry-After", "60"))
                    if not 0 <= delay <= 60:
                        delay = 60
                except (ValueError, TypeError):
                    delay = 60
            else:
                if response.status_code != 200:
                    raise SocialPreparationError("unavailable")
                try:
                    size = int(response.headers.get("Content-Length", "0"))
                    if not 0 <= size <= MAX_BYTES or response.headers.get("Content-Encoding", "identity").lower() != "identity":
                        raise ValueError()
                    body = bytearray()
                    for chunk in response.iter_content(chunk_size=8192):
                        if len(body) + len(chunk) > MAX_BYTES:
                            raise ValueError()
                        body.extend(chunk)
                    return bytes(body)
                except (ValueError, UnicodeError):
                    raise SocialPreparationError("invalid") from None
        time.sleep(delay)
    raise SocialPreparationError("unavailable")


def _parse(raw, vendor, symbol):
    if type(raw) is not bytes or len(raw) > MAX_BYTES:
        raise ValueError("invalid social response")
    # Fixed public feeds are UTF-8. Refuse alternate encodings before XML
    # declaration checks so UTF-16 cannot conceal an entity expansion.
    decoded = raw.decode("utf-8-sig")
    if vendor == "stocktwits":
        def unique_object(pairs):
            value = {}
            for key, item in pairs:
                if key in value:
                    raise ValueError("duplicate social JSON field")
                value[key] = item
            return value

        def nonfinite(_value):
            raise ValueError("nonfinite social JSON value")

        document = json.loads(decoded, object_pairs_hook=unique_object, parse_constant=nonfinite)
        if (type(document) is not dict or document.get("response", {}).get("status") != 200
                or document.get("symbol", {}).get("symbol") != symbol
                or type(document.get("messages")) is not list):
            raise ValueError("invalid social envelope")
        rows = document["messages"]
        if len(rows) > MAX_POSTS:
            raise ValueError("social sample too large")
        posts = []
        for row in rows:
            if type(row.get("id")) is not int or row["id"] <= 0 or type(row.get("body")) is not str:
                raise ValueError("invalid social post")
            entities = row.get("entities")
            if entities is not None and type(entities) is not dict:
                raise ValueError("invalid social entities")
            sentiment = (entities or {}).get("sentiment")
            label = "unlabeled" if sentiment is None else sentiment["basic"]
            posts.append(SocialPost(post_id=str(row["id"]), body=row["body"],
                published_at=row["created_at"], label=label))
        return posts
    # Reject declarations/entities, including expansion attacks, before stdlib XML.
    if re.search(r"<!\s*(DOCTYPE|ENTITY)", decoded, re.I):
        raise ValueError("unsafe social XML")
    root = ET.fromstring(decoded)
    if root.tag != "{http://www.w3.org/2005/Atom}feed":
        raise ValueError("invalid social feed")
    rows = root.findall("atom:entry", reddit._ATOM_NS)
    if len(rows) > reddit._FEED_PAGE:
        raise ValueError("social feed exceeds requested sample")
    posts = []
    for row in rows:
        def text(name, entry=row):
            return entry.findtext("atom:" + name, namespaces=reddit._ATOM_NS)
        category = row.find("atom:category", reddit._ATOM_NS)
        links = row.findall("atom:link", reddit._ATOM_NS)
        link = next((item.get("href") for item in links if item.get("rel", "alternate") == "alternate"), None)
        posts.append(SocialPost(post_id=text("id"), title=text("title"),
            body=reddit._strip_html(text("content") or ""), published_at=text("published"),
            updated_at=text("updated"), community=category.get("term") if category is not None else None,
            url=link))
    return posts


def collect_social(instrument, vendor, *, analysis_as_of=None, clock=lambda: datetime.now(UTC), fetch=None):
    base = _scope(instrument, vendor)
    requested = analysis_as_of or clock()
    if requested.tzinfo is None or requested.utcoffset() is None or requested > clock():
        raise ValueError("invalid social request cutoff")
    base.update(requested_at=requested, window_start=requested - timedelta(days=WINDOW_DAYS))
    try:
        raw = (fetch or _fetch)(vendor, base["provider_symbol"])
    except SocialPreparationError as error:
        return SocialCollection(**base, retrieved_at=clock(), quality_status=(DataQualityStatus.INVALID
            if error.code == "invalid" else DataQualityStatus.UNAVAILABLE),
            reason="invalid_vendor_response" if error.code == "invalid" else "vendor_request_failed")
    except Exception:
        return SocialCollection(**base, retrieved_at=clock(), quality_status=DataQualityStatus.UNAVAILABLE,
            reason="vendor_request_failed")
    try:
        posts = _parse(raw, vendor, base["provider_symbol"])
        if len({post.post_id for post in posts}) != len(posts):
            raise ValueError("duplicate social post")
        received = len(posts)
        eligible = [post for post in posts if base["window_start"] <= post.published_at <= requested
                    and (post.updated_at is None or post.updated_at <= requested)]
        reason = ("eligible_recent_posts_not_exhaustive" if eligible else
                  "no_posts_in_requested_window" if posts else "empty_vendor_feed")
        status = (DataQualityStatus.OK if eligible else DataQualityStatus.COVERAGE_GAP
                  if posts else DataQualityStatus.NO_DATA)
        return SocialCollection(**base, retrieved_at=clock(), posts=tuple(sorted(eligible,
            key=lambda post: (post.published_at, post.post_id))), received_posts=received,
            excluded_out_of_window=received-len(eligible), quality_status=status, reason=reason)
    except (ValueError, TypeError, AttributeError, KeyError, ET.ParseError, RecursionError, OverflowError):
        return SocialCollection(**base, retrieved_at=clock(), quality_status=DataQualityStatus.INVALID,
            reason="invalid_vendor_response", invalid_records=1)


class SocialAcquisitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    instrument: InstrumentContract
    vendor: Vendor
    analysis_as_of: AwareDatetime


def fetch_current_social(instrument, vendor, *, analysis_as_of=None):
    _scope(instrument, vendor)
    request = SocialAcquisitionRequest(instrument=instrument, vendor=vendor,
        analysis_as_of=analysis_as_of or datetime.now(UTC))
    deadline = time.monotonic() + 75
    try:
        if request.analysis_as_of > datetime.now(UTC):
            raise SocialPreparationError("invalid")
        # Reuse the already native-tested bounded pipe/lifetime mechanism.
        raw = _child_json([sys.executable, "-m", __name__], request.model_dump_json().encode(), deadline=deadline)
        if type(raw) is not dict or "error" in raw:
            raise SocialPreparationError("invalid" if raw == {"error": "invalid"} else "unavailable")
        collection = SocialCollection.model_validate(raw)
        if (any(getattr(collection, name) != value for name, value in _scope(instrument, vendor).items())
                or collection.requested_at != request.analysis_as_of or collection.retrieved_at > datetime.now(UTC)):
            raise SocialPreparationError("invalid")
        if time.monotonic() >= deadline:
            raise SocialPreparationError("unavailable")
        return collection
    except SocialPreparationError:
        raise
    except MacroPreparationError as error:
        raise SocialPreparationError(error.code) from None
    except (ValueError, TypeError):
        raise SocialPreparationError("invalid") from None
    except OSError:
        raise SocialPreparationError("unavailable") from None


def main():
    try:
        request = SocialAcquisitionRequest.model_validate_json(sys.stdin.read(16385))
        with contextlib.redirect_stdout(sys.stderr):
            value = collect_social(request.instrument, request.vendor, analysis_as_of=request.analysis_as_of)
        output = value.model_dump_json().encode()
        if len(output) > MAX_BYTES:
            output = b'{"error":"invalid"}'
    except Exception:
        output = b'{"error":"unavailable"}'
    sys.stdout.buffer.write(output)


if __name__ == "__main__":
    main()
