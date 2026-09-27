"""Immutable source receipt for newly valued portfolios; never backfill history."""

from uuid import UUID, uuid5

from pydantic import BaseModel, ConfigDict

from tradingagents.contracts import ArtifactKind
from tradingagents.contracts.ledger import ValuationQuote


class ValuationSource(BaseModel):
    model_config = ConfigDict(extra="forbid")
    quote: ValuationQuote
    vendor: str
    dataset: str


class ValuationEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    portfolio_id: UUID
    portfolio_content_hash: str
    sources: tuple[ValuationSource, ...]


def evidence_id(portfolio_id):
    return uuid5(portfolio_id, "portfolio-valuation-evidence-v1")


def load_valuation_evidence(artifacts, portfolio, owner_id):
    loaded = artifacts.read(evidence_id(portfolio.portfolio_id), owner_id)
    if loaded is None:
        return None
    manifest, content = loaded
    evidence = ValuationEvidence.model_validate_json(content)
    if (manifest.kind is not ArtifactKind.PORTFOLIO_VALUATION_EVIDENCE
            or evidence.portfolio_id != portfolio.portfolio_id
            or evidence.portfolio_content_hash != portfolio.content_hash):
        raise ValueError("valuation evidence identity mismatch")
    positions = {item.instrument_id: item for item in portfolio.positions}
    if (len(evidence.sources) != len(positions)
            or {item.quote.instrument_id for item in evidence.sources} != set(positions)):
        raise ValueError("valuation evidence coverage mismatch")
    for source in evidence.sources:
        quote = source.quote
        if (quote.price != positions[quote.instrument_id].market_price
                or quote.currency != portfolio.base_currency
                or quote.source_at > quote.observed_at or quote.observed_at > portfolio.as_of
                or quote.quality_status.value != "OK"):
            raise ValueError("valuation evidence quote mismatch")
    return evidence
