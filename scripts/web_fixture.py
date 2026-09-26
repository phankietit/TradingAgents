"""Explicit synthetic local web QA server; never opens an existing owner database.

Run: python -m scripts.web_fixture --synthetic-local-only
Login: fixture@example.com / synthetic-local-web-password
No worker is started and no vendor/model is called. Not an investment dataset.
"""

import argparse
import math
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import uvicorn

from tradingagents._compat import UTC
from tradingagents.contracts import PriceInterval
from tradingagents.platform.api import ApiSettings, create_app
from tradingagents.platform.artifacts import ArtifactService, LocalArtifactStore
from tradingagents.platform.auth import OwnerAuth
from tradingagents.platform.instruments import InstrumentMaster
from tradingagents.platform.market_data import TimeSeriesSnapshotService, normalize_time_series
from tradingagents.platform.persistence import Database, PlatformRepository, upgrade_database


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthetic-local-only", action="store_true", required=True)
    parser.parse_args()
    cache = Path(__file__).resolve().parents[1] / ".cache"
    cache.mkdir(exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="web-fixture-", dir=cache))
    url = f"sqlite:///{directory / 'fixture.db'}"
    upgrade_database(url)
    now = datetime.now(UTC).replace(microsecond=0)
    database = Database(url)
    with database.session() as session:
        owner = OwnerAuth(session).bootstrap_owner("fixture@example.com", "synthetic-local-web-password", now=now)
        repository = PlatformRepository(session)
        master = InstrumentMaster(repository)
        master.bootstrap()
        instrument = next(item for item in master.list() if item.canonical_symbol == "AAPL")
        bars = []
        for index in range(60):
            close = round(180 + index * .25 + math.sin(index / 4) * 4, 2)
            bars.append({"timestamp": now - timedelta(days=60-index), "open": close - .3,
                         "high": close + 1, "low": close - 1, "close": close,
                         "volume": 1_000_000 + index * 1000})
        series = normalize_time_series(instrument=instrument, dataset="ohlcv.daily",
            interval=PriceInterval.ONE_DAY, as_of=now, annualization_periods=252, bars=bars)
        artifacts = ArtifactService(LocalArtifactStore(directory / "artifacts"), repository)
        TimeSeriesSnapshotService(repository, artifacts).persist(
            owner_id=owner.owner_id, series=series, vendor="SYNTHETIC LOCAL QA — NOT MARKET DATA", retrieved_at=now)
    database.dispose()
    print("Synthetic-only API on 127.0.0.1:8000; no worker or provider calls.")
    uvicorn.run(create_app(ApiSettings(database_url=url, artifact_root=directory / "artifacts",
        allowed_origin="http://127.0.0.1:5173", secure_cookies=False)),
        host="127.0.0.1", port=8000, access_log=False)


if __name__ == "__main__":
    main()
