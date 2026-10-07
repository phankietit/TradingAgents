"""Loader contracts with synthetic repositories, no DB/live claims."""

import os
from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from tests.test_analysis_engine import _instrument
from tests.test_recovery_fingerprint import inputs
from tests.test_risk_engine import _policy, _portfolio
from tradingagents.contracts import ArtifactKind, DataQualityStatus
from tradingagents.platform.analysis import recording_sources as loader
from tradingagents.platform.artifacts import ArtifactService, LocalArtifactStore
from tradingagents.platform.persistence import Database, PlatformRepository, upgrade_database


@pytest.fixture
def setup():
    args = inputs()
    run = args["run"]
    source = args["request"].snapshot_context.by_analyst["market"][0]
    book = _portfolio(run.owner_id, run.instrument_id)
    balance = book.cash[0].model_copy(update={"amount": Decimal("600.000000000000000001")})
    book = book.model_copy(update={"cash": (balance, *book.cash[1:])})
    policy = _policy(run.owner_id)
    declared = run.decision_inputs.model_copy(update={"portfolio_snapshot_id": book.portfolio_id,
        "policy_id": policy.policy_id, "policy_version": policy.policy_version,
        "requested_target_weight": .4, "risk_snapshot_ids": (source.manifest.snapshot_id,)})
    run = run.model_copy(update={"decision_inputs": declared})
    blob = source.payload.encode()
    artifact = SimpleNamespace(artifact_id=uuid4(), owner_id=run.owner_id,
        snapshot_id=source.manifest.snapshot_id, instrument_id=source.manifest.instrument_id,
        kind=ArtifactKind.SNAPSHOT_PAYLOAD, media_type="application/json",
        content_hash=source.manifest.content_hash, byte_size=len(blob))
    data = {"book": book, "policy": policy, "manifest": source.manifest, "artifact": artifact, "blob": blob}
    reads = []

    def get_book(key, owner):
        assert key == declared.portfolio_snapshot_id and owner == run.owner_id
        return data["book"]

    def get_policy(key, version, owner):
        assert (key, version, owner) == (declared.policy_id, declared.policy_version, run.owner_id)
        return data["policy"]

    def get_artifact(key, owner):
        assert key == source.manifest.snapshot_id and owner == run.owner_id
        return data["artifact"]

    repo = SimpleNamespace(get_portfolio_snapshot=get_book, get_policy=get_policy,
        get_snapshot=lambda key: data["manifest"], get_snapshot_artifact=get_artifact)

    def read(key, owner):
        reads.append((key, owner))
        return (data["artifact"], data["blob"])

    artifacts = SimpleNamespace(repository=repo, read=read)
    return {"repository": repo, "artifacts": artifacts, "run": run}, data, reads


def test_original_decimal_book_policy_and_risk_bytes_survive_without_float(setup):
    args, data, reads = setup
    result = loader.load_original_recording_sources(**args)
    assert result.portfolio_snapshot == data["book"] and result.policy == data["policy"]
    assert result.portfolio_snapshot.cash[0].amount == Decimal("600.000000000000000001")
    assert result.risk_snapshots[0].payload.encode() == data["blob"]
    assert reads == [(data["artifact"].artifact_id, args["run"].owner_id)]


def test_no_portfolio_is_absent_not_a_fabricated_flat_book(setup):
    args, data, _ = setup
    declared = args["run"].decision_inputs.model_copy(update={"portfolio_snapshot_id": None,
        "policy_id": None, "policy_version": None, "requested_target_weight": None, "risk_snapshot_ids": ()})
    args["run"] = args["run"].model_copy(update={"decision_inputs": declared})
    result = loader.load_original_recording_sources(**args)
    assert result.portfolio_snapshot is None and result.policy is None and result.risk_snapshots == ()


@pytest.mark.parametrize("mutation", ["missing_book", "book_owner", "book_time", "missing_policy",
    "policy_owner", "policy_version", "future_policy", "artifact_owner", "artifact_kind",
    "artifact_snapshot", "artifact_instrument", "media", "manifest_future", "retrieval_future",
    "quality", "missing_source_time", "source_after_retrieval", "corrupt_bytes", "wrong_length",
    "foreign_repository"])
def test_original_loader_refuses_mismatch_without_private_error_text(setup, mutation):
    args, data, _ = setup
    if mutation == "missing_book":
        data["book"] = None
    elif mutation in {"book_owner", "book_time"}:
        field, value = ("owner_id", uuid4()) if mutation == "book_owner" else ("as_of", args["run"].analysis_as_of - timedelta(seconds=1))
        data["book"] = data["book"].model_copy(update={field: value})
    elif mutation == "missing_policy":
        data["policy"] = None
    elif mutation.startswith("policy_") or mutation == "future_policy":
        field, value = {"policy_owner": ("owner_id", uuid4()), "policy_version": ("policy_version", "other"),
            "future_policy": ("effective_at", args["run"].analysis_as_of + timedelta(seconds=1))}[mutation]
        data["policy"] = data["policy"].model_copy(update={field: value})
    elif mutation.startswith("artifact_") or mutation == "media":
        field, value = {"artifact_owner": ("owner_id", uuid4()), "artifact_kind": ("kind", ArtifactKind.ANALYSIS_REPORT),
            "artifact_snapshot": ("snapshot_id", uuid4()), "artifact_instrument": ("instrument_id", uuid4()),
            "media": ("media_type", "text/plain")}[mutation]
        setattr(data["artifact"], field, value)
    elif mutation in {"manifest_future", "retrieval_future", "quality", "missing_source_time", "source_after_retrieval"}:
        field, value = {"manifest_future": ("as_of", args["run"].analysis_as_of + timedelta(seconds=1)),
            "retrieval_future": ("retrieved_at", args["run"].analysis_as_of + timedelta(seconds=1)),
            "quality": ("quality_status", DataQualityStatus.STALE), "missing_source_time": ("source_end", None),
            "source_after_retrieval": ("source_end", data["manifest"].retrieved_at + timedelta(seconds=1))}[mutation]
        data["manifest"] = data["manifest"].model_copy(update={field: value})
    elif mutation == "corrupt_bytes":
        data["blob"] = b'{"close":999}'
        data["artifact"].byte_size = len(data["blob"])
    elif mutation == "wrong_length":
        data["artifact"].byte_size += 1
    else:
        args["artifacts"].repository = object()
    with pytest.raises(ValueError, match="^original recording sources require review$") as raised:
        loader.load_original_recording_sources(**args)
    assert raised.value.__cause__ is None


@pytest.mark.parametrize("foreign_owner", [False, True])
@pytest.mark.parametrize("backend", ["sqlite", "postgresql"])
def test_real_database_and_artifact_store_original_reads_keep_owner_and_decimal(setup, tmp_path, foreign_owner, backend):
    args, data, _ = setup
    if backend == "postgresql":
        url = os.environ.get("TEST_POSTGRES_URL")
        if not url or os.environ.get("TA_ALLOW_TEST_DB_RESET") != "1":
            pytest.skip("isolated PostgreSQL helper prerequisite absent")
    else:
        url = "sqlite:///" + str(tmp_path / "recording-sources.db")
    upgrade_database(url)
    database = Database(url)
    store = LocalArtifactStore(tmp_path / "artifacts")
    run = args["run"]
    # Both PG cases share the disposable database without resetting history.
    # Give each synthetic instrument its own canonical alias as well as UUID.
    symbol = "QA" + uuid4().hex[:8].upper()
    instrument = _instrument().model_copy(update={"instrument_id": run.instrument_id,
        "symbol": symbol, "canonical_symbol": symbol})
    try:
        with database.session() as session:
            repo = PlatformRepository(session, artifact_store=store)
            artifacts = ArtifactService(store, repo)
            repo.add_instrument(instrument)
            repo.add_snapshot(data["manifest"])
            repo.add_portfolio_snapshot(data["book"])
            repo.add_policy(data["policy"])
            repo.save_run(run)
            artifacts.create(owner_id=run.owner_id, kind=ArtifactKind.SNAPSHOT_PAYLOAD,
                media_type="application/json", content=data["blob"],
                instrument_id=instrument.instrument_id, snapshot_id=data["manifest"].snapshot_id,
                expected_hash=data["manifest"].content_hash)
        with database.session() as session:
            repo = PlatformRepository(session, artifact_store=store)
            artifacts = ArtifactService(store, repo)
            saved_run = repo.get_run(run.run_id, run.owner_id)
            if foreign_owner:
                assert repo.get_run(run.run_id, uuid4()) is None
                with pytest.raises(ValueError, match="^original recording sources require review$"):
                    loader.load_original_recording_sources(repository=repo, artifacts=artifacts,
                        run=saved_run.model_copy(update={"owner_id": uuid4()}))
            else:
                result = loader.load_original_recording_sources(repository=repo, artifacts=artifacts, run=saved_run)
                assert result.portfolio_snapshot.cash[0].amount == Decimal("600.000000000000000001")
                assert result.policy == data["policy"]
                assert result.risk_snapshots[0].payload.encode() == data["blob"]
                assert repo.get_run(run.run_id, run.owner_id) == saved_run
    finally:
        database.dispose()
