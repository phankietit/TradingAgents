from threading import Event

import pytest

from tradingagents.platform.jobs.runtime import WorkerSettings, load_worker_settings, run_worker
from tradingagents.platform.persistence import upgrade_database


def test_worker_environment_requires_explicit_private_storage():
    with pytest.raises(ValueError, match="DATABASE_URL"):
        load_worker_settings({})
    with pytest.raises(ValueError, match="ARTIFACT_ROOT"):
        load_worker_settings({"TRADINGAGENTS_DATABASE_URL": "sqlite:///private.db"})


def test_worker_once_exits_cleanly_on_empty_migrated_queue(tmp_path):
    url = f"sqlite:///{tmp_path / 'worker.db'}"
    upgrade_database(url)
    settings = WorkerSettings(url, tmp_path / "artifacts")
    assert run_worker(settings, once=True) is None
    assert url not in repr(settings)


def test_worker_stops_before_claim_when_shutdown_requested(tmp_path):
    url = f"sqlite:///{tmp_path / 'worker.db'}"
    stopped = Event()
    stopped.set()
    assert run_worker(WorkerSettings(url, tmp_path / "artifacts"), stopped=stopped) is None
    assert not (tmp_path / "worker.db").exists()  # No connection/migration/claim.


@pytest.mark.parametrize("poll", [0, -1, float("nan"), float("inf")])
def test_invalid_poll_interval_is_rejected(tmp_path, poll):
    with pytest.raises(ValueError, match="finite"):
        run_worker(WorkerSettings("sqlite://", tmp_path), once=True, poll_seconds=poll)
