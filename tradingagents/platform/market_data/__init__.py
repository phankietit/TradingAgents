"""Normalized market-data services with point-in-time-safe snapshot access."""

from .equity_etf import EquityETFSnapshotPipeline, SourceBatch
from .timeseries import (
    InsufficientBenchmarkCoverage,
    TimeSeriesSnapshotService,
    TimeSeriesUnavailable,
    build_time_series_view,
    normalize_time_series,
    slice_time_series,
)

__all__ = [
    "InsufficientBenchmarkCoverage",
    "EquityETFSnapshotPipeline",
    "SourceBatch",
    "TimeSeriesSnapshotService",
    "TimeSeriesUnavailable",
    "build_time_series_view",
    "normalize_time_series",
    "slice_time_series",
]
