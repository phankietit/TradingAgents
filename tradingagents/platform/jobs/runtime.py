"""Explicit local worker entrypoint; no schema migration or network listener."""

import argparse
import logging
import math
import os
import signal
from dataclasses import dataclass, field
from pathlib import Path
from threading import Event
from uuid import uuid4

from tradingagents.contracts import JobKind
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.platform.analysis import AnalysisEngine
from tradingagents.platform.artifacts import LocalArtifactStore
from tradingagents.platform.observability import configure_platform_logging
from tradingagents.platform.persistence import Database

from .analysis import AnalysisJobHandler
from .worker import JobWorker


@dataclass(frozen=True)
class WorkerSettings:
    database_url: str = field(repr=False)
    artifact_root: Path
    prompt_version: str = "1"


def load_worker_settings(environ=None):
    source = os.environ if environ is None else environ
    required = ("TRADINGAGENTS_DATABASE_URL", "TRADINGAGENTS_ARTIFACT_ROOT")
    for name in required:
        if not source.get(name, "").strip():
            raise ValueError(f"required worker setting is missing: {name}")
    return WorkerSettings(database_url=source[required[0]], artifact_root=Path(source[required[1]]))


def run_worker(settings, *, once=False, stopped=None, poll_seconds=1.0, worker_id=None, engine=None):
    if not math.isfinite(poll_seconds) or poll_seconds <= 0:
        raise ValueError("poll_seconds must be positive and finite")
    stopped = stopped or Event()
    database = Database(settings.database_url)
    try:
        store = LocalArtifactStore(settings.artifact_root)
        config = {**DEFAULT_CONFIG, "data_cache_dir": str(store.root / "worker-runtime" / "cache"),
                  "results_dir": str(store.root / "worker-runtime" / "reports")}
        handler = AnalysisJobHandler(database, store, engine=engine or AnalysisEngine(base_config=config),
                                     prompt_version=settings.prompt_version)
        worker = JobWorker(database, worker_id=worker_id or f"worker-{uuid4()}",
                           handlers={JobKind.ANALYSIS_RUN: handler})
        while not stopped.is_set():
            result = worker.run_once()
            if once:
                return result
            if result is None:
                stopped.wait(poll_seconds)
    finally:
        database.dispose()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Process private TradingAgents analysis jobs.")
    parser.add_argument("--once", action="store_true", help="Process at most one eligible job, then exit.")
    parser.add_argument("--poll-seconds", type=float, default=1.0, help="Idle queue poll interval.")
    args = parser.parse_args(argv)
    stopped = Event()
    previous = {}
    configure_platform_logging()
    try:
        for signum in (signal.SIGINT, signal.SIGTERM):
            previous[signum] = signal.signal(signum, lambda *_: stopped.set())
        run_worker(load_worker_settings(), once=args.once, stopped=stopped, poll_seconds=args.poll_seconds)
    except Exception as error:
        # Provider/database exceptions can contain credentials or source content.
        logging.getLogger("tradingagents.platform.jobs").error("worker stopped: %s", type(error).__name__)
        raise SystemExit(1) from None
    finally:
        for signum, handler in previous.items():
            signal.signal(signum, handler)


if __name__ == "__main__":
    main()
