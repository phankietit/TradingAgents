"""Deterministic filed-date facts over an immutable SEC snapshot."""

from __future__ import annotations

import re
from datetime import datetime

from tradingagents.dataflows.platform_sec import SecCollection, SecFact


class SnapshotFundamentalFacts:
    def __init__(self, source: dict):
        self.snapshot_id = source["snapshot_id"]
        self.provenance = source["provenance"]
        self.collection = SecCollection.model_validate(source["data"])
        if (self.provenance["dataset"] != "fundamentals"
                or self.provenance["vendor"] != "sec_edgar"
                or str(self.collection.instrument_id) != self.provenance["instrument_id"]
                or self.collection.retrieved_at != datetime.fromisoformat(
                    self.provenance["retrieved_at"].replace("Z", "+00:00"))):
            raise ValueError("SEC fact payload differs from snapshot provenance")
        self.facts = self.collection.facts
        self._catalog = {self.fact_id(fact): self._display_value(fact) for fact in self.facts}
        if len(self._catalog) != len(self.facts):
            raise ValueError("SEC fact IDs are not unique")

    @staticmethod
    def fact_id(fact: SecFact) -> str:
        metric = re.sub(r"[^a-z0-9]+", "_", fact.metric.lower()).strip("_")
        unit = "usd_millions" if fact.unit == "USD" else "usd_per_share"
        return f"sec.{metric}.{fact.frequency}.{fact.period_end.isoformat()}.{unit}"

    @staticmethod
    def _display_value(fact: SecFact) -> float:
        return fact.value / 1_000_000 if fact.unit == "USD" else fact.value

    def fact_catalog(self) -> dict[str, float]:
        return dict(self._catalog)

    def resolve_fact(self, fact_id: str) -> float | None:
        return self._catalog.get(fact_id)

    def page(self, *, offset: int = 0, limit: int = 50) -> dict:
        if not 0 <= offset < len(self.facts) or not 1 <= limit <= 100:
            raise ValueError("invalid SEC fact page")
        end = min(offset + limit, len(self.facts))
        return {"snapshot_id": self.snapshot_id, "offset": offset,
                "total_facts": len(self.facts),
                "next_offset": end if end < len(self.facts) else None,
                "facts": [self._view(fact) for fact in self.facts[offset:end]]}

    def _view(self, fact: SecFact) -> dict:
        return {"fact_id": self.fact_id(fact), "metric": fact.metric,
                "frequency": fact.frequency,
                "period_start": fact.period_start.isoformat() if fact.period_start else None,
                "period_end": fact.period_end.isoformat(), "filed_at": fact.filed_at.isoformat(),
                "form": fact.form, "accession": fact.accession, "tag": fact.tag,
                "unit": "USD millions" if fact.unit == "USD" else "USD per share",
                "value": self._display_value(fact)}

    def summary(self) -> dict:
        latest = {}
        for fact in self.facts:
            key = (fact.metric, fact.frequency)
            if key not in latest or fact.period_end > latest[key].period_end:
                latest[key] = fact
        return {"snapshot_id": self.snapshot_id, "provenance": self.provenance,
                "coverage": "reported_us_gaap_tags_only_not_a_complete_company_profile",
                "total_facts": len(self.facts),
                "latest_by_metric_and_frequency": [self._view(fact) for fact in latest.values()],
                "full_history_tool": "get_snapshot_fundamentals"}
