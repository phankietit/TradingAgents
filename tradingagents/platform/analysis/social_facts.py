"""Source sample counts, not calibrated market sentiment or probabilities."""

from decimal import Decimal, InvalidOperation

from tradingagents.contracts import DataQualityStatus, SnapshotManifest
from tradingagents.dataflows.platform_social import SocialCollection, _scope


class SnapshotSocialFacts:
    def __init__(self, source):
        from tradingagents.platform.market_data.social import _manifest
        self.collection = SocialCollection.model_validate(source["data"])
        manifest = SnapshotManifest.model_validate(source["provenance"])
        if (source["snapshot_id"] != str(manifest.snapshot_id)
                or manifest != _manifest(self.collection, manifest.snapshot_id)
                or self.collection.quality_status is not DataQualityStatus.OK):
            raise ValueError("social payload differs from eligible provenance")
        self.snapshot_id = str(manifest.snapshot_id)
        self.provenance = manifest.model_dump(mode="json")
        counts = {"posts": len(self.collection.posts)}
        if self.collection.vendor == "stocktwits":
            counts.update({label.lower(): sum(post.label == label for post in self.collection.posts)
                           for label in ("Bullish", "Bearish", "unlabeled")})
        self._catalog = {f"social.{self.collection.vendor}.sample_count.{key}": value
                         for key, value in counts.items()}

    def require_instrument(self, instrument):
        if any(getattr(self.collection, name) != value
               for name, value in _scope(instrument, self.collection.vendor).items()):
            raise ValueError("social fact instrument identity mismatch")

    def fact_catalog(self):
        return dict(self._catalog)

    def resolve_fact(self, fact_id):
        return self._catalog.get(fact_id) if type(fact_id) is str else None

    def statement(self, fact_id, number, *, vi=False):
        """Own the count's vendor/unit/label meaning, not a market inference."""
        count = self.resolve_fact(fact_id)
        try:
            if type(number) is not str or count is None or Decimal(number) != count:
                raise ValueError()
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError("unsupported social sample count") from None
        vendor = "StockTwits" if self.collection.vendor == "stocktwits" else "Reddit"
        key = fact_id.rsplit(".", 1)[-1]
        if key == "posts":
            return (f"Mẫu bài đăng {vendor} được cung cấp có {count} bài; đây không phải phạm vi thảo luận đầy đủ của thị trường." if vi
                    else f"The supplied {vendor} sample contains {count} {'post' if count == 1 else 'posts'}; it is not exhaustive market coverage.")
        if key == "unlabeled":
            return (f"Trong mẫu StockTwits được cung cấp, {count} bài không có nhãn cảm xúc do người đăng chọn; không có nhãn không có nghĩa là trung lập." if vi
                    else f"In the supplied StockTwits sample, {count} {'post has' if count == 1 else 'posts have'} no user sentiment label; unlabeled does not mean neutral.")
        label = "Bullish" if key == "bullish" else "Bearish"
        return (f"Trong mẫu StockTwits được cung cấp, {count} bài có nhãn {label} do người đăng chọn; đây là ý kiến, không phải xác suất thị trường." if vi
                else f"In the supplied StockTwits sample, {count} {'post has' if count == 1 else 'posts have'} a user-provided {label} label; this is opinion, not a market probability.")

    def summary(self):
        # The original Sentiment Analyst consumes prefetched text, not tools.
        # Keep every eligible returned post/body, no preview/table truncation.
        return {"snapshot_id": self.snapshot_id, "provenance": self.provenance,
            "coverage": self.collection.coverage, "vendor": self.collection.vendor,
            "sample_window_start": self.collection.window_start.isoformat(),
            "sample_window_end": self.collection.requested_at.isoformat(),
            "received_posts": self.collection.received_posts,
            "excluded_out_of_window": self.collection.excluded_out_of_window,
            "fact_catalog": self.fact_catalog(),
            "posts": [post.model_dump(mode="json") for post in self.collection.posts],
            "limitations": "A recent non-exhaustive sample, not a market poll, calibrated probability, historical archive or evidence of missing discussion. Reddit has no sentiment labels/vote/comment counts. StockTwits labels are user opinions, not verified events; unlabeled is not Neutral. No author/account profile, score or engagement inferred."}
