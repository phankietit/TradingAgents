from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy

import tradingagents.default_config as default_config

# Use default config but allow it to be overridden
_config: dict | None = None
_run_config: ContextVar[dict | None] = ContextVar(
    "tradingagents_run_config",
    default=None,
)


def _merge_config(base: dict, incoming: dict) -> dict:
    """Return an isolated one-level merge of ``incoming`` onto ``base``."""
    merged = deepcopy(base)
    for key, value in deepcopy(incoming).items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key].update(value)
        else:
            merged[key] = value
    return merged


def initialize_config():
    """Initialize the configuration with default values."""
    global _config
    if _config is None:
        _config = deepcopy(default_config.DEFAULT_CONFIG)


def set_config(config: dict):
    """Update the process-default configuration with custom values.

    Dict-valued keys (e.g. ``data_vendors``) are merged one level deep so a
    partial update like ``{"data_vendors": {"core_stock_apis": "alpha_vantage"}}``
    keeps the other nested keys from the default; scalar keys are replaced.

    This compatibility API is intended for CLI startup and direct dataflow use.
    Concurrent analysis runs must use :func:`config_scope` instead so one run
    cannot replace another run's provider, language, or cache configuration.
    """
    global _config
    initialize_config()
    _config = _merge_config(_config, config)


def get_config() -> dict:
    """Get an isolated copy of the active run or process-default config."""
    scoped = _run_config.get()
    if scoped is not None:
        return deepcopy(scoped)
    if _config is None:
        initialize_config()
    return deepcopy(_config)


@contextmanager
def config_scope(config: dict) -> Iterator[dict]:
    """Activate an immutable-by-copy configuration for the current run.

    ``ContextVar`` keeps concurrent threads and async tasks isolated when each
    worker enters its own scope. Nested scopes restore the previous run config
    on exit, including exceptional exits. Missing keys inherit package defaults
    rather than mutable process state, keeping runs reproducible when legacy
    callers use :func:`set_config` elsewhere in the process.
    """
    scoped = _merge_config(default_config.DEFAULT_CONFIG, config)
    token = _run_config.set(scoped)
    try:
        yield deepcopy(scoped)
    finally:
        _run_config.reset(token)


# Initialize with default config
initialize_config()
