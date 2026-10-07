"""Real PostgreSQL dump/restore, synthetic only, in the QA helper's owned container.

Not an operator backup command, active-job recovery, encrypted transfer or
permission to access/replace owner data. No existing database is restored over.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from collections import Counter
from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import MetaData, create_engine, select
from sqlalchemy.engine import make_url

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
EMAIL = "postgres-restore-fixture@example.com"
PASSWORD = "synthetic-postgres-restore-only"


def _docker(*arguments, content=None):
    result = subprocess.run(
        ["docker", *arguments], input=content, capture_output=True, timeout=60, check=False,
    )
    # Never expose raw subprocess diagnostics or a configured database URL.
    assert result.returncode == 0, "owned PostgreSQL restore command failed"
    return result.stdout


def _owned_container():
    container = os.environ.get("TA_TEST_POSTGRES_CONTAINER", "")
    owner = os.environ.get("TA_TEST_POSTGRES_OWNER", "")
    url_text = os.environ.get("TEST_POSTGRES_URL", "")
    if not container or not owner or not url_text:
        pytest.skip("run via acknowledged verify-postgres-local.sh for owned restore evidence")
    assert os.environ.get("TA_ALLOW_TEST_DB_RESET") == "1"
    assert re.fullmatch(r"ta-research-qa-\d+-\d+", container) and owner == container
    label = _docker("inspect", "--format",
                    '{{index .Config.Labels "tradingagents.qa.owner"}}', container).decode().strip()
    assert label == owner, "restore withheld: container ownership mismatch"
    port = _docker("inspect", "--format",
                   '{{(index (index .NetworkSettings.Ports "5432/tcp") 0).HostPort}}',
                   container).decode().strip()
    url = make_url(url_text)
    assert (url.drivername, url.username, url.host, url.database) == (
        "postgresql+psycopg", "ta_qa", "127.0.0.1", "ta_qa",
    ), "restore withheld: non-helper database endpoint"
    assert port.isdigit() and url.port == int(port), "restore withheld: endpoint mismatch"
    return container, url


def _logical_dump(container, name):
    dump = _docker("exec", container, "pg_dump", "-U", "ta_qa", "--no-owner",
                   "--no-privileges", name)
    # Patched pg_dump emits a fresh psql restriction nonce on every invocation.
    # Exclude only those two control lines, never SQL/schema/row/sequence data.
    return b"\n".join(line for line in dump.splitlines()
                      if not re.fullmatch(rb"\\(?:un)?restrict [A-Za-z0-9]+", line))


def _schema_lines(dump):
    # PG16 reparses this one IN predicate into element-wise casts on restore.
    # Both exact expressions compare status::text with the same five text
    # literals. Do not normalize any other predicate, literal or SQL line.
    values = ("reserved", "leased", "cancel_requested", "cancelled", "review_required")
    whole_cast = ", ".join(f"'{value}'::character varying" for value in values)
    element_cast = ", ".join(f"('{value}'::character varying)::text" for value in values)
    prefix = "    CONSTRAINT ck_research_executions_status CHECK (((status)::text = ANY ("
    before = (prefix + f"(ARRAY[{whole_cast}])::text[])))").encode()
    after = (prefix + f"ARRAY[{element_cast}])))").encode()
    return Counter(before if line == after else line for line in dump.splitlines())


def _table_rows(url):
    engine = create_engine(url)
    try:
        metadata = MetaData()
        metadata.reflect(bind=engine)
        with engine.connect() as connection:
            return {name: sorted(json.dumps(dict(row), sort_keys=True, default=str)
                                 for row in connection.execute(select(table)).mappings())
                    for name, table in metadata.tables.items()}
    finally:
        engine.dispose()


@pytest.mark.unit
@pytest.mark.parametrize("failure", ["ack", "label", "host", "port", "name"])
def test_restore_guard_refuses_unowned_or_nonhelper_endpoint(monkeypatch, failure):
    container = "ta-research-qa-123-456"
    monkeypatch.setenv("TA_ALLOW_TEST_DB_RESET", "0" if failure == "ack" else "1")
    monkeypatch.setenv("TA_TEST_POSTGRES_CONTAINER", "existing-db" if failure == "name" else container)
    monkeypatch.setenv("TA_TEST_POSTGRES_OWNER", container)
    host = "other-host" if failure == "host" else "127.0.0.1"
    port = 15433 if failure == "port" else 15432
    monkeypatch.setenv("TEST_POSTGRES_URL", f"postgresql+psycopg://ta_qa@{host}:{port}/ta_qa")
    commands = []

    def inspection_only(*arguments, **kwargs):
        commands.append(arguments)
        assert arguments[0] == "inspect", "guard must not allocate/mutate a DB"
        if "Labels" in arguments[2]:
            return b"foreign-task" if failure == "label" else container.encode()
        return b"15432"

    monkeypatch.setattr(f"{__name__}._docker", inspection_only)
    with pytest.raises(AssertionError):
        _owned_container()
    assert len(commands) <= 2


@pytest.mark.unit
def test_dump_comparison_preserves_unknown_constraint_changes():
    # It must not hide a literal/predicate change elsewhere or across table rows.
    original = b"CONSTRAINT another_check CHECK (status = 'reserved')\nrow one"
    changed = b"CONSTRAINT another_check CHECK (status = 'cancelled')\nrow one"
    assert _schema_lines(original) != _schema_lines(changed)


@pytest.mark.integration
@pytest.mark.parametrize("artifact_state", ["paired", "missing", "tampered"])
def test_postgres_paired_dump_restore_authenticated_readback(tmp_path, artifact_state):
    container, base_url = _owned_container()
    # Names cannot refer to any pre-existing DB; createdb must succeed, no --clean,
    # DROP, downgrade, overwrite or fallback to the helper's shared ta_qa DB.
    suffix = uuid4().hex
    source_name = "ta_restore_source_" + suffix
    restored_name = "ta_restore_target_" + suffix
    for name in (source_name, restored_name):
        _docker("exec", container, "createdb", "-U", "ta_qa", name)
    source_url = base_url.set(database=source_name).render_as_string(hide_password=False)
    restored_url = base_url.set(database=restored_name).render_as_string(hide_password=False)
    upgrade_database(source_url)
    database = Database(source_url)
    owner_id = uuid4()
    instrument = InstrumentContract(
        instrument_id=uuid4(), symbol="AAPL", canonical_symbol="AAPL",
        display_name="Synthetic PostgreSQL restore fixture", asset_class=AssetClass.EQUITY,
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
    source_root = tmp_path / "source-artifacts"
    contents = [b"# EN\nSynthetic only: 100.00 USD.",
                "# VI\nChỉ là dữ liệu giả lập: 100.00 USD.".encode()]
    try:
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
    finally:
        database.dispose()
    # No fixture API/worker/writers exist during this paired copy. Actual PG16
    # archive is streamed locally, not persisted as a repo/runtime artifact.
    original_dump = _logical_dump(container, source_name)
    original_rows = _table_rows(source_url)
    archive = _docker("exec", container, "pg_dump", "-U", "ta_qa", "--format=custom",
                      "--no-owner", "--no-privileges", source_name)
    assert archive.startswith(b"PGDMP")
    _docker("exec", "-i", container, "pg_restore", "-U", "ta_qa", "--exit-on-error",
            "--no-owner", "--no-privileges", "-d", restored_name, content=archive)
    restored_dump = _logical_dump(container, restored_name)
    assert _schema_lines(restored_dump) == _schema_lines(original_dump), (
        "restored dump differs beyond ordering and the exact known PG16 cast reformat"
    )
    assert _table_rows(restored_url) == original_rows, "restored per-table rows differ"
    original_blobs = {path.relative_to(source_root): path.read_bytes()
                      for path in source_root.rglob("*") if path.is_file()}
    restored_root = tmp_path / "restored-artifacts"
    if artifact_state == "missing":
        restored_root.mkdir()
    else:
        shutil.copytree(source_root, restored_root)
        if artifact_state == "tampered":
            restored_root.joinpath(*reports[0].storage_key.split("/")).write_bytes(b"tampered")
    app = create_app(ApiSettings(database_url=restored_url, artifact_root=restored_root,
        allowed_origin=ORIGIN, secure_cookies=False, clock=lambda: NOW))
    with TestClient(app) as client:
        path = f"/api/v1/runs/{run.run_id}/artifacts"
        assert client.get(path).status_code == 401
        assert client.post("/api/v1/auth/login", headers={"Origin": ORIGIN},
                           json={"email": EMAIL, "password": PASSWORD}).status_code == 200
        response = client.get(f"/api/v1/runs/{run.run_id}")
        assert response.status_code == 200 and response.json() == run.model_dump(mode="json")
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
                assert response.status_code == 200 and response.content == content
                assert "sha256:" + hashlib.sha256(response.content).hexdigest() == report.content_hash
            else:
                assert response.status_code == 409
                assert response.json()["detail"] == "artifact integrity check failed"
                assert content not in response.content
    assert _logical_dump(container, source_name) == original_dump
    assert _table_rows(source_url) == original_rows, "source rows changed during restore readback"
    assert {path.relative_to(source_root): path.read_bytes()
            for path in source_root.rglob("*") if path.is_file()} == original_blobs
    # The helper, not this test, removes its exact labelled container at exit.
