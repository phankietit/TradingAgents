"""Synthetic, quiesced SQLite/artifact restore through the authenticated API.

This is not an operator backup tool, encrypted transfer, active-job recovery,
PostgreSQL restore, or permission to copy/replace a private database.
"""

from __future__ import annotations

import hashlib
import shutil
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from tradingagents._compat import UTC
from tradingagents.contracts import (
    ArtifactKind,
    AssetClass,
    InstrumentContract,
    RunManifest,
    RunStatus,
    Tradability,
)
from tradingagents.platform.api import ApiSettings, create_app
from tradingagents.platform.artifacts import ArtifactService, LocalArtifactStore
from tradingagents.platform.auth import OwnerAuth
from tradingagents.platform.persistence import Database, PlatformRepository, upgrade_database

NOW = datetime(2026, 10, 8, tzinfo=UTC)
ORIGIN = "http://testserver"
PASSWORD = "synthetic-restore-only-password"
EMAIL = "restore-fixture@example.com"


def _dump(path):
    with closing(sqlite3.connect(f"file:{path}?mode=ro", uri=True)) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        return tuple(connection.iterdump())


@pytest.mark.unit
@pytest.mark.parametrize("artifact_state", ["paired", "missing", "tampered"])
def test_authenticated_paired_restore_preserves_bytes_and_refuses_incomplete_copy(
    tmp_path, artifact_state,
):
    source_path = tmp_path / "source.db"
    source_root = tmp_path / "source-artifacts"
    source_url = f"sqlite:///{source_path}"
    upgrade_database(source_url)
    database = Database(source_url)
    owner_id = uuid4()
    instrument = InstrumentContract(
        instrument_id=uuid4(), symbol="AAPL", canonical_symbol="AAPL",
        display_name="Synthetic restore fixture", asset_class=AssetClass.EQUITY,
        tradability=Tradability.INVESTABLE, venue="NASDAQ", quote_currency="USD",
        timezone="America/New_York", session_calendar="XNAS", benchmark_symbol="SPY",
    )
    run = RunManifest(
        run_id=uuid4(), owner_id=owner_id, instrument_id=instrument.instrument_id,
        analysis_as_of=NOW, status=RunStatus.SUCCEEDED,
        created_at=NOW - timedelta(minutes=3), started_at=NOW - timedelta(minutes=2),
        completed_at=NOW - timedelta(minutes=1), selected_analysts=("market",),
        llm_provider="openai", quick_model="synthetic", deep_model="synthetic",
        config_hash="sha256:" + "a" * 64, prompt_version="fixture", report_language="en-vi",
    )
    contents = [b"# EN\nSynthetic only: 100.00 USD.",
                "# VI\nChỉ là dữ liệu giả lập: 100.00 USD.".encode()]
    with database.session() as session:
        OwnerAuth(session).bootstrap_owner(EMAIL, PASSWORD, owner_id=owner_id, now=NOW)
        repository = PlatformRepository(session)
        repository.add_instrument(instrument)
        repository.save_run(run)
        service = ArtifactService(LocalArtifactStore(source_root), repository)
        reports = [service.create(
            owner_id=owner_id, run_id=run.run_id, kind=ArtifactKind.ANALYSIS_REPORT,
            media_type="text/markdown", content=content, created_at=NOW,
        ) for content in contents]
        foreign = service.create(owner_id=uuid4(), kind=ArtifactKind.ANALYSIS_REPORT,
            media_type="text/plain", content=b"foreign synthetic report", created_at=NOW)
    # No live writers/worker/API are running during this paired copy.
    database.dispose()
    original_dump = _dump(source_path)
    original_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    original_blobs = {path.relative_to(source_root): path.read_bytes()
                      for path in source_root.rglob("*") if path.is_file()}
    restored_path = tmp_path / "restored.db"
    with closing(sqlite3.connect(f"file:{source_path}?mode=ro", uri=True)) as source, closing(
        sqlite3.connect(restored_path)
    ) as restored:
        source.backup(restored)
    assert _dump(restored_path) == original_dump
    restored_root = tmp_path / "restored-artifacts"
    if artifact_state == "missing":
        restored_root.mkdir()
    else:
        shutil.copytree(source_root, restored_root)
        if artifact_state == "tampered":
            restored_root.joinpath(*reports[0].storage_key.split("/")).write_bytes(b"tampered")
    restored_url = f"sqlite:///{restored_path}"
    app = create_app(ApiSettings(database_url=restored_url, artifact_root=restored_root,
        allowed_origin=ORIGIN, secure_cookies=False, clock=lambda: NOW))
    with TestClient(app) as client:
        path = f"/api/v1/runs/{run.run_id}/artifacts"
        assert client.get(path).status_code == 401
        login = client.post("/api/v1/auth/login", headers={"Origin": ORIGIN},
                            json={"email": EMAIL, "password": PASSWORD})
        assert login.status_code == 200
        restored_run = client.get(f"/api/v1/runs/{run.run_id}")
        assert restored_run.status_code == 200
        assert restored_run.json() == run.model_dump(mode="json")
        metadata = client.get(path)
        assert metadata.status_code == 200
        assert {row["artifact_id"] for row in metadata.json()} == {
            str(report.artifact_id) for report in reports}
        assert "storage_key" not in metadata.text and "owner_id" not in metadata.text
        assert client.get(f"/api/v1/artifacts/{foreign.artifact_id}").status_code == 404
        for index, (report, content) in enumerate(zip(reports, contents, strict=True)):
            response = client.get(f"/api/v1/artifacts/{report.artifact_id}")
            valid = artifact_state == "paired" or (artifact_state == "tampered" and index == 1)
            if valid:
                assert response.status_code == 200
                assert response.content == content
                assert "sha256:" + hashlib.sha256(response.content).hexdigest() == report.content_hash
            else:
                assert response.status_code == 409
                assert response.json()["detail"] == "artifact integrity check failed"
                assert content not in response.content
    # Login writes only to the new restored DB. Source history/blobs stay intact.
    assert _dump(source_path) == original_dump
    assert hashlib.sha256(source_path.read_bytes()).hexdigest() == original_hash
    assert {path.relative_to(source_root): path.read_bytes()
            for path in source_root.rglob("*") if path.is_file()} == original_blobs
