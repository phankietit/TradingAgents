"""Recovery identity binds immutable inputs, not a permission to spend or approve."""

import hashlib
import json
from copy import deepcopy
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from tests.test_analysis_engine import _instrument
from tests.test_risk_engine import NOW, _policy, _portfolio
from tests.test_snapshot_analysis import context
from tradingagents.contracts import RunManifest
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.platform.analysis import AnalysisRequest
from tradingagents.platform.analysis.checkpoint_codec import (
    CheckpointCodecError,
    SnapshotCheckpointCodec,
)
from tradingagents.platform.analysis.recovery_fingerprint import (
    RecoveryFingerprintError,
    ResolvedClientBinding,
    build_recovery_fingerprint,
    installed_runtime_digest,
)
from tradingagents.platform.analysis.snapshots import AnalysisSnapshot
from tradingagents.portfolio import PortfolioContext


def inputs():
    instrument = _instrument()
    sources = context(instrument)
    owner = uuid4()
    config = deepcopy(DEFAULT_CONFIG)
    config.update(llm_provider="openai", quick_think_llm="quick", deep_think_llm="deep",
                  backend_url="https://example.test/v1", output_language="English")
    run = RunManifest(run_id=uuid4(), owner_id=owner, instrument_id=instrument.instrument_id,
        analysis_as_of=NOW, status="queued", created_at=NOW, selected_analysts=("market",),
        llm_provider="openai", quick_model="quick", deep_model="deep", config_hash="sha256:" + "a" * 64,
        prompt_version="1", report_language="en", execution_limits={"wall_seconds": 1800, "model_calls": 128},
        snapshot_ids=tuple(s.manifest.snapshot_id for s in sources.by_analyst["market"]),
        decision_inputs={"snapshots_by_analyst": {"market": tuple(s.manifest.snapshot_id for s in sources.by_analyst["market"])},
                         "source_max_age_seconds": {"market": 0}})
    request = AnalysisRequest(instrument=instrument, analysis_date=NOW.date(), selected_analysts=("market",),
                              snapshot_context=sources)
    clients = ResolvedClientBinding(quick_endpoint=config["backend_url"], deep_endpoint=config["backend_url"],
        quick_client_class="fixture.Client", deep_client_class="fixture.Client",
        quick_options_hash="sha256:" + "b" * 64, deep_options_hash="sha256:" + "b" * 64)
    return {"owner_id": owner, "run": run, "request": request, "base_config": config, "client_binding": clients}


def test_digest_stable_portable_and_runtime_derived():
    args = inputs()
    original = build_recovery_fingerprint(**args)
    assert len(original) == 64 and original == build_recovery_fingerprint(**args)
    moved = deepcopy(args)
    for key in ("project_dir", "results_dir", "data_cache_dir", "memory_log_path"):
        moved["base_config"][key] = "/different-machine/private-storage"
    assert build_recovery_fingerprint(**moved) == original
    assert installed_runtime_digest().startswith("sha256:")
    assert "private-storage" not in original


@pytest.mark.parametrize("field,value", [("max_debate_rounds", 3), ("max_risk_discuss_rounds", 3),
    ("max_recur_limit", 101), ("temperature", .2), ("llm_max_retries", 2), ("max_tokens", 9000),
    ("openai_reasoning_effort", "high"), ("output_language", "Vietnamese")])
def test_effective_configuration_changes_invalidate_identity(field, value):
    args = inputs()
    original = build_recovery_fingerprint(**args)
    args["base_config"][field] = value
    if field == "output_language":
        args["run"] = args["run"].model_copy(update={"report_language": "vi"})
    assert build_recovery_fingerprint(**args) != original


@pytest.mark.parametrize("field,value", [("prompt_version", "2"), ("config_hash", "sha256:" + "c" * 64),
    ("run_id", None), ("execution_limits", None)])
def test_original_run_identity_and_allowance_bind(field, value):
    args = inputs()
    original = build_recovery_fingerprint(**args)
    args["run"] = args["run"].model_copy(update={field: uuid4() if field == "run_id" else value})
    assert build_recovery_fingerprint(**args) != original


def test_changed_valid_source_bytes_invalidate_even_with_same_snapshot_id():
    args = inputs()
    original = build_recovery_fingerprint(**args)
    source = args["request"].snapshot_context.by_analyst["market"][0]
    payload = json.dumps({"close": 101})
    changed = AnalysisSnapshot(manifest=source.manifest.model_copy(update={
        "content_hash": "sha256:" + hashlib.sha256(payload.encode()).hexdigest()}), payload=payload)
    args["request"].snapshot_context.by_analyst["market"] = (changed,)
    assert build_recovery_fingerprint(**args) != original


@pytest.mark.parametrize("field", ["quick_options_hash", "deep_options_hash", "quick_client_class", "deep_client_class"])
def test_resolved_client_options_and_implementation_bind(field):
    args = inputs()
    original = build_recovery_fingerprint(**args)
    value = "sha256:" + "d" * 64 if field.endswith("hash") else "fixture.ChangedClient"
    args["client_binding"] = args["client_binding"].model_copy(update={field: value})
    assert build_recovery_fingerprint(**args) != original


@pytest.mark.parametrize("mutation", ["owner", "instrument", "date", "roles", "model", "provider", "endpoint",
    "secret_url", "secret_field", "nested_secret", "corrupt_source", "future_source", "missing_clients"])
def test_unbound_or_secret_bearing_context_fails_before_any_model(mutation):
    args = inputs()
    if mutation == "owner":
        args["owner_id"] = uuid4()
    elif mutation == "instrument":
        args["request"] = args["request"].model_copy(update={"instrument": _instrument()})
    elif mutation == "date":
        args["request"] = args["request"].model_copy(update={"analysis_date": (NOW + timedelta(days=1)).date()})
    elif mutation == "roles":
        args["request"] = args["request"].model_copy(update={"selected_analysts": ("news",)})
    elif mutation in {"model", "provider", "endpoint", "secret_url", "secret_field", "nested_secret"}:
        key, value = {"model": ("deep_think_llm", "changed"), "provider": ("llm_provider", "changed"),
            "endpoint": ("backend_url", "https://other.test/v1"),
            "secret_url": ("backend_url", "https://user:NEVER_ECHO@example.test/v1"),
            "secret_field": ("api_key", "NEVER_ECHO"),
            "nested_secret": ("tool_vendors", {"api_key": "NEVER_ECHO"})}[mutation]
        args["base_config"][key] = value
    elif mutation in {"corrupt_source", "future_source"}:
        ctx = args["request"].snapshot_context
        source = ctx.by_analyst["market"][0]
        source = source.model_copy(update={"payload": '{"close":0}'}) if mutation == "corrupt_source" else source.model_copy(
            update={"manifest": source.manifest.model_copy(update={"retrieved_at": NOW + timedelta(days=1)})})
        ctx.by_analyst["market"] = (source,)
    else:
        args["client_binding"] = None
    with pytest.raises(RecoveryFingerprintError) as raised:
        build_recovery_fingerprint(**args)
    assert str(raised.value) == "recovery inputs are invalid or incompatible"
    assert raised.value.__cause__ is None


def test_full_portfolio_and_policy_content_bind_not_only_declared_hash():
    args = inputs()
    book = _portfolio(args["owner_id"], args["run"].instrument_id)
    policy = _policy(args["owner_id"])
    declared = args["run"].decision_inputs.model_copy(update={"portfolio_snapshot_id": book.portfolio_id,
        "policy_id": policy.policy_id, "policy_version": policy.policy_version, "requested_target_weight": .4})
    args["run"] = args["run"].model_copy(update={"decision_inputs": declared})
    args["portfolio_snapshot"], args["policy"] = book, policy
    args["request"] = args["request"].model_copy(update={"portfolio": PortfolioContext(cash=600, currency="USD")})
    original = build_recovery_fingerprint(**args)
    args["policy"].parameters["max_position_weight"] = .45
    assert build_recovery_fingerprint(**args) != original
    args["policy"] = policy.model_copy(update={"owner_id": uuid4()})
    with pytest.raises(RecoveryFingerprintError):
        build_recovery_fingerprint(**args)


def test_runtime_identity_changes_invalidate_without_git_sha_change(monkeypatch):
    args = inputs()
    original = build_recovery_fingerprint(**args)
    monkeypatch.setattr("tradingagents.platform.analysis.recovery_fingerprint.installed_runtime_digest",
                        lambda: "sha256:" + "f" * 64)
    assert build_recovery_fingerprint(**args) != original


def test_runtime_digest_uses_source_bytes_not_only_package_version(monkeypatch):
    original = installed_runtime_digest()
    read = Path.read_bytes

    def changed(path):
        data = read(path)
        return data + b"\n# fixture change" if path.name == "snapshot_analysis.py" else data

    monkeypatch.setattr(Path, "read_bytes", changed)
    assert installed_runtime_digest() != original


@pytest.mark.parametrize("endpoint", ["https://example.test/v1?api_key=NEVER_ECHO",
    "https://@example.test/v1", "https://example.test/v1#NEVER_ECHO", "https://example.test:invalid/v1",
    "\nhttps://example.test/v1"])
def test_resolved_endpoint_cannot_smuggle_credentials_or_invalid_transport(endpoint):
    args = inputs()
    args["client_binding"] = args["client_binding"].model_copy(update={"deep_endpoint": endpoint})
    with pytest.raises(RecoveryFingerprintError):
        build_recovery_fingerprint(**args)


def test_risk_source_content_is_hash_bound_when_declared():
    args = inputs()
    source = args["request"].snapshot_context.by_analyst["market"][0]
    risk = source.model_copy(update={"manifest": source.manifest.model_copy(update={"snapshot_id": uuid4()})})
    args["run"] = args["run"].model_copy(update={
        "snapshot_ids": args["run"].snapshot_ids + (risk.manifest.snapshot_id,),
        "decision_inputs": args["run"].decision_inputs.model_copy(update={"risk_snapshot_ids": (risk.manifest.snapshot_id,)})})
    args["risk_snapshots"] = (risk,)
    original = build_recovery_fingerprint(**args)
    payload = '{"close":102}'
    args["risk_snapshots"] = (AnalysisSnapshot(manifest=risk.manifest.model_copy(update={
        "content_hash": "sha256:" + hashlib.sha256(payload.encode()).hexdigest()}), payload=payload),)
    assert build_recovery_fingerprint(**args) != original
    args["risk_snapshots"] = (risk.model_copy(update={"payload": payload}),)
    with pytest.raises(RecoveryFingerprintError):
        build_recovery_fingerprint(**args)


def test_changed_identity_rejects_checkpoint_before_model_reentry(monkeypatch):
    from tests.test_snapshot_checkpoint_codec import checkpoint

    def forbidden(*args, **kwargs):
        raise AssertionError("fingerprint construction called a model")

    monkeypatch.setattr("tradingagents.graph.trading_graph.create_llm_client", forbidden)
    args = inputs()
    original = build_recovery_fingerprint(**args)
    raw = SnapshotCheckpointCodec(fingerprint=original, nodes={"Market Analyst"}).encode(checkpoint())
    args["base_config"]["max_risk_discuss_rounds"] = 2
    changed = build_recovery_fingerprint(**args)
    with pytest.raises(CheckpointCodecError):
        SnapshotCheckpointCodec(fingerprint=changed, nodes={"Market Analyst"}).decode(raw)


def test_no_portfolio_and_flat_book_cannot_be_interchanged():
    args = inputs()
    args["request"] = args["request"].model_copy(update={"portfolio": PortfolioContext(cash=0, positions=[])})
    with pytest.raises(RecoveryFingerprintError):
        build_recovery_fingerprint(**args)


def test_mutated_risk_snapshot_hash_and_declared_source_identity_rejected():
    args = inputs()
    source = args["request"].snapshot_context.by_analyst["market"][0]
    args["risk_snapshots"] = (source,)
    with pytest.raises(RecoveryFingerprintError):
        build_recovery_fingerprint(**args)


def test_portfolio_cash_changes_bind_even_when_content_hash_label_unchanged():
    args = inputs()
    book = _portfolio(args["owner_id"], args["run"].instrument_id)
    policy = _policy(args["owner_id"])
    declared = args["run"].decision_inputs.model_copy(update={"portfolio_snapshot_id": book.portfolio_id,
        "policy_id": policy.policy_id, "policy_version": policy.policy_version, "requested_target_weight": .4})
    args["run"] = args["run"].model_copy(update={"decision_inputs": declared})
    args["portfolio_snapshot"], args["policy"] = book, policy
    args["request"] = args["request"].model_copy(update={"portfolio": PortfolioContext(cash=600, currency="USD")})
    original = build_recovery_fingerprint(**args)
    args["portfolio_snapshot"] = book.model_copy(update={"cash": ({"currency": "USD", "amount": "601"},)})
    assert build_recovery_fingerprint(**args) != original
