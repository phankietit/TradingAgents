"""Value an owner ledger using persisted immutable price payloads, never raw quotes."""

import hashlib
from decimal import Decimal

from tradingagents.contracts import LedgerTransactionType, NormalizedTimeSeries
from tradingagents.contracts.ledger import ValuationQuote
from tradingagents.platform.analysis.profiles import resolve_analysis_profile

from .ledger import PortfolioLedger


class PortfolioLedgerService:
    def __init__(self, artifacts):
        self.artifacts = artifacts
        self.repository = artifacts.repository

    def replay(self, *, ledger_id, owner_id, base_currency, price_snapshot_ids, as_of, max_price_age):
        if as_of.tzinfo is None or as_of.utcoffset() is None:
            raise ValueError("valuation clock requires timezone")
        transactions = tuple(item for item in self.repository.list_ledger_transactions(ledger_id, owner_id)
                             if item.occurred_at <= as_of)
        if not transactions:
            raise ValueError("owner ledger has no eligible history")
        quantities = {}
        for entry in transactions:
            if entry.instrument_id is not None:
                instrument = self.repository.get_instrument(entry.instrument_id)
                if instrument is None or not resolve_analysis_profile(instrument).investable:
                    raise ValueError("ledger instrument is not investable in supported scope")
                if entry.transaction_type in {LedgerTransactionType.BUY, LedgerTransactionType.SELL}:
                    sign = 1 if entry.transaction_type is LedgerTransactionType.BUY else -1
                    quantities[entry.instrument_id] = quantities.get(entry.instrument_id, Decimal(0)) + sign * entry.quantity
        held = {key for key, value in quantities.items() if value > 0}
        if set(price_snapshot_ids) != held:
            raise ValueError("valuation snapshots must exactly cover open holdings")
        quotes = {}
        for instrument_id, snapshot_id in price_snapshot_ids.items():
            manifest = self.repository.get_snapshot(snapshot_id)
            artifact = self.repository.get_snapshot_artifact(snapshot_id, owner_id)
            if (manifest is None or artifact is None or manifest.instrument_id != instrument_id
                    or artifact.instrument_id != instrument_id or artifact.content_hash != manifest.content_hash
                    or manifest.retrieved_at > as_of or manifest.as_of > as_of):
                raise ValueError("eligible owner valuation snapshot is unavailable")
            loaded = self.artifacts.read(artifact.artifact_id, owner_id)
            if loaded is None:
                raise ValueError("valuation snapshot payload is unavailable")
            if "sha256:" + hashlib.sha256(loaded[1]).hexdigest() != manifest.content_hash:
                raise ValueError("valuation snapshot hash mismatch")
            series = NormalizedTimeSeries.model_validate_json(loaded[1])
            instrument = self.repository.get_instrument(instrument_id)
            if (series.instrument_id != instrument_id or series.dataset != manifest.dataset
                    or series.quote_currency != instrument.quote_currency
                    or series.as_of != manifest.as_of or manifest.source_start != series.bars[0].timestamp
                    or manifest.source_end != series.bars[-1].timestamp):
                raise ValueError("valuation payload does not match snapshot provenance")
            bar = series.bars[-1]
            # Actual units are valued at raw close, never split-adjusted history.
            quotes[instrument_id] = ValuationQuote(
                instrument_id=instrument_id, currency=series.quote_currency,
                price=Decimal(str(bar.close)), source_at=bar.timestamp, observed_at=manifest.retrieved_at,
                snapshot_id=snapshot_id, content_hash=manifest.content_hash, quality_status=manifest.quality_status,
            )
        snapshot = PortfolioLedger().replay(ledger_id=ledger_id, owner_id=owner_id,
            base_currency=base_currency, transactions=transactions, prices=quotes,
            as_of=as_of, max_price_age=max_price_age)
        return self.repository.add_portfolio_snapshot(snapshot)
