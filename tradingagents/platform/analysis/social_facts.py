"""Source sample counts, not calibrated market sentiment or probabilities."""

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
