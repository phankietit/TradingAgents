"""Replay risk correlations from owner-scoped, hash-verified snapshot bytes."""

import hashlib
import statistics

from tradingagents.contracts import DataQualityStatus, NormalizedTimeSeries, PriceInterval
from tradingagents.platform.artifacts.store import ArtifactIntegrityError, StoredBlob

from .engine import RiskLimits


def replay_correlations(repository, decision, portfolio, policy):
    required = {p.instrument_id for p in portfolio.positions
                if p.weight > 0 and p.instrument_id != decision.instrument_id
                and decision.target_weight > 0}
    if not required:
        return {}
    limits = RiskLimits.model_validate(policy.parameters)
    if (repository.artifact_store is None or limits.correlation_periods is None
            or limits.correlation_max_age_seconds is None):
        raise ValueError("correlation replay requires storage and explicit policy window/freshness")
    ids = decision.risk_snapshot_ids
    run = repository.get_run(decision.run_id, decision.owner_id)
    if len(ids) != len(set(ids)) or not set(ids).issubset(run.snapshot_ids):
        raise ValueError("risk snapshots must be unique and bound to the run")
    series_by_instrument = {}
    for snapshot_id in ids:
        snapshot = repository.get_snapshot(snapshot_id)
        artifact = repository.get_snapshot_artifact(snapshot_id, decision.owner_id)
        if (snapshot is None or artifact is None
                or artifact.content_hash != snapshot.content_hash
                or artifact.instrument_id != snapshot.instrument_id
                or snapshot.quality_status is not DataQualityStatus.OK
                or snapshot.as_of > decision.as_of or snapshot.retrieved_at > decision.as_of):
            raise ValueError("risk snapshot provenance is unavailable or ineligible")
        try:
            payload = repository.artifact_store.get_bytes(StoredBlob(
                artifact.content_hash, artifact.byte_size, artifact.storage_key))
        except (ArtifactIntegrityError, OSError) as error:
            raise ValueError("risk snapshot storage integrity failure") from error
        if "sha256:" + hashlib.sha256(payload).hexdigest() != snapshot.content_hash:
            raise ValueError("risk snapshot hash mismatch")
        series = NormalizedTimeSeries.model_validate_json(payload)
        if (series.instrument_id != snapshot.instrument_id or series.dataset != snapshot.dataset
                or series.as_of != snapshot.as_of or series.interval is not PriceInterval.ONE_DAY
                or series.quote_currency != portfolio.base_currency
                or snapshot.source_start != series.bars[0].timestamp
                or snapshot.source_end != series.bars[-1].timestamp
                or snapshot.retrieved_at < series.bars[-1].timestamp):
            raise ValueError("risk snapshot identity or time window mismatch")
        age = (decision.as_of - series.bars[-1].timestamp).total_seconds()
        if age < 0 or age > limits.correlation_max_age_seconds:
            raise ValueError("risk snapshot is stale")
        if series.instrument_id in series_by_instrument:
            raise ValueError("duplicate risk instrument")
        series_by_instrument[series.instrument_id] = series
    if set(series_by_instrument) != required | {decision.instrument_id}:
        raise ValueError("risk snapshot coverage does not match held instruments")
    base = series_by_instrument[decision.instrument_id]
    count = limits.correlation_periods + 1
    if len(base.bars) < count:
        raise ValueError("insufficient correlation history")
    base_bars = base.bars[-count:]
    dates = tuple(bar.timestamp for bar in base_bars)

    def returns(bars):
        prices = [bar.adjusted_close if bar.adjusted_close is not None else bar.close for bar in bars]
        return [b / a - 1 for a, b in zip(prices, prices[1:], strict=False)]

    left = returns(base_bars)
    result = {}
    for instrument_id in sorted(required, key=str):
        other = series_by_instrument[instrument_id]
        bars = other.bars[-count:]
        if (other.price_basis != base.price_basis
                or tuple(bar.timestamp for bar in bars) != dates):
            raise ValueError("correlation requires matching price bases and session coverage")
        right = returns(bars)
        if statistics.pstdev(left) == 0 or statistics.pstdev(right) == 0:
            raise ValueError("correlation is undefined for constant returns")
        result[instrument_id] = statistics.correlation(left, right)
    return result
