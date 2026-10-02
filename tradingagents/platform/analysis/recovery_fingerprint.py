"""Private recovery identity; neither consent nor a source/owner authorization.

This prerequisite is not wired to the worker. Resolved client endpoint bindings
must eventually come from trusted client initialization, never a model/browser.
Only hashes are returned; raw portfolio, config, prompts and credentials are not
persisted or logged. Existing RunManifest.config_hash semantics are untouched.
"""

import hashlib
import json
import platform
from copy import deepcopy
from dataclasses import asdict
from importlib.metadata import distributions
from pathlib import Path
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field

from tradingagents.contracts import PolicyContract, PortfolioSnapshot, RunManifest
from tradingagents.contracts.base import ContentHash
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.analyst_execution import build_analyst_execution_plan
from tradingagents.graph.trading_graph import TradingAgentsGraph

from .engine import AnalysisRequest
from .profiles import resolve_analysis_profile, select_analysts
from .snapshots import AnalysisSnapshot, SnapshotAnalysisContext


class RecoveryFingerprintError(ValueError):
    """Fixed diagnostic: never expose an input or source exception."""


def _reject():
    raise RecoveryFingerprintError("recovery inputs are invalid or incompatible")


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")


def _hash(value):
    return hashlib.sha256(_json(value)).hexdigest()


def _endpoint(value):
    if type(value) is not str or len(value) > 2048 or any(ch.isspace() for ch in value):
        _reject()
    parsed = urlsplit(value)
    _ = parsed.port  # Validate malformed port values without normalizing the identity.
    if (parsed.scheme not in {"https", "http"} or not parsed.hostname or parsed.username is not None
            or parsed.password is not None or parsed.query or parsed.fragment):
        _reject()
    # Identity checking is not network destination approval; never contact it.
    return value


def _no_credentials(value, depth=0):
    if depth > 32:
        _reject()
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str or key.lower() in {
                "api_key", "password", "secret", "token", "authorization", "headers", "credentials"}:
                _reject()
            _no_credentials(item, depth + 1)
    elif isinstance(value, (tuple, list)):
        for item in value:
            _no_credentials(item, depth + 1)


class ResolvedClientBinding(BaseModel):
    """Required effective transport identity, no credential/header fields."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    quick_endpoint: str = Field(min_length=1, max_length=2048)
    deep_endpoint: str = Field(min_length=1, max_length=2048)
    quick_client_class: str = Field(min_length=1, max_length=200)
    deep_client_class: str = Field(min_length=1, max_length=200)
    # Hash of additional effective non-secret client options/defaults. No
    # default allows silently treating unknown SDK settings as "unchanged".
    quick_options_hash: ContentHash
    deep_options_hash: ContentHash


def installed_runtime_digest():
    """Actual package-source bytes + Python + installed distribution versions.

    Includes uncommitted source edits, not Git HEAD alone. No files outside the
    installed tradingagents Python package and no environment values are read.
    Broad invalidation is intentional until a narrower runtime contract exists.
    """
    try:
        package = Path(__file__).resolve().parents[2]
        paths = sorted(package.rglob("*.py"))
        if any(path.is_symlink() or not path.resolve().is_relative_to(package) for path in paths):
            _reject()
        sources = [(path.relative_to(package).as_posix(), hashlib.sha256(path.read_bytes()).hexdigest())
                   for path in paths]
        if not sources:
            _reject()
        versions = sorted((dist.metadata["Name"], dist.version) for dist in distributions())
        return "sha256:" + _hash({"sources": sources, "python": platform.python_version(),
                                   "distributions": versions})
    except (OSError, ValueError, TypeError, KeyError):
        raise RecoveryFingerprintError("recovery inputs are invalid or incompatible") from None


def build_recovery_fingerprint(*, owner_id, run: RunManifest, request: AnalysisRequest,
                               base_config, client_binding: ResolvedClientBinding,
                               portfolio_snapshot: PortfolioSnapshot | None = None,
                               policy: PolicyContract | None = None,
                               risk_snapshots: tuple[AnalysisSnapshot, ...] = ()) -> str:
    """Hash validated exact original research inputs before any model admission.

    Authentication, owner-readable loading, resolved-client attestation, durable
    checkpoint integrity, lease and explicit continuation consent remain caller
    obligations. This function has no provider call or publication path.
    """
    try:
        run = RunManifest.model_validate(run.model_dump(warnings=False))
        request = AnalysisRequest.model_validate(request.model_dump(warnings=False))
        binding = ResolvedClientBinding.model_validate(client_binding.model_dump(warnings=False))
        for endpoint in (binding.quick_endpoint, binding.deep_endpoint):
            _endpoint(endpoint)
        if run.owner_id != owner_id or run.decision_inputs is None or request.snapshot_context is None:
            _reject()
        if run.instrument_id != request.instrument.instrument_id or run.analysis_as_of.date() != request.analysis_date:
            _reject()
        profile = resolve_analysis_profile(request.instrument)
        analysts = select_analysts(profile, request.selected_analysts)
        if analysts != run.selected_analysts:
            _reject()
        inputs = SnapshotAnalysisContext.model_validate(request.snapshot_context.model_dump(warnings=False))
        inputs.reports(run.instrument_id, analysts)  # Recheck mutable nested dicts and payload hashes.
        declared = run.decision_inputs
        if (inputs.as_of != run.analysis_as_of
                or inputs.source_max_age_seconds != declared.source_max_age_seconds
                or {role: tuple(source.manifest.snapshot_id for source in sources)
                    for role, sources in inputs.by_analyst.items()} != declared.snapshots_by_analyst):
            _reject()
        config = deepcopy(dict(base_config))
        config.update(deepcopy(dict(request.config_overrides)))
        # Unknown keys might be credential-bearing or change future graph
        # behavior; reject rather than exclude them from identity silently.
        if set(config) != set(DEFAULT_CONFIG):
            _reject()
        _no_credentials(config)
        if (config["llm_provider"] != run.llm_provider or config["quick_think_llm"] != run.quick_model
                or config["deep_think_llm"] != run.deep_model):
            _reject()
        languages = {"en": "English", "vi": "Vietnamese", "en-vi": "English and Vietnamese"}
        if run.report_language and config["output_language"] != languages[run.report_language]:
            _reject()
        if config["backend_url"] is not None:
            endpoint = _endpoint(config["backend_url"])
            # OpenAI SDK enforces a trailing slash on base_url. Accept only
            # that precise normalization, not changed paths/hosts or removed
            # query/credential components. Original config still binds below.
            accepted_endpoints = {endpoint, endpoint if endpoint.endswith("/") else endpoint + "/"}
            if binding.quick_endpoint not in accepted_endpoints or binding.deep_endpoint not in accepted_endpoints:
                _reject()
        # Pure option calculation; never initialize an SDK or read a key.
        graph = object.__new__(TradingAgentsGraph)
        graph.config = config
        options = graph._get_provider_kwargs()
        options.setdefault("timeout", 600)
        options.setdefault("max_retries", 1)
        # Paths are relocated on another machine, not research semantics. No
        # memory context is used by snapshot mode; its knobs still bind below.
        for path_key in ("project_dir", "results_dir", "data_cache_dir", "memory_log_path"):
            del config[path_key]
        risk = [AnalysisSnapshot.model_validate(source.model_dump(warnings=False)) for source in risk_snapshots]
        if (len({source.manifest.snapshot_id for source in risk}) != len(risk)
                or {source.manifest.snapshot_id for source in risk} != set(declared.risk_snapshot_ids)):
            _reject()
        for source in risk:
            if (source.manifest.as_of > run.analysis_as_of or source.manifest.retrieved_at > run.analysis_as_of
                    or source.manifest.quality_status.value != "OK"):
                _reject()
        book = PortfolioSnapshot.model_validate(portfolio_snapshot.model_dump(warnings=False)) if portfolio_snapshot else None
        limits = PolicyContract.model_validate(policy.model_dump(warnings=False)) if policy else None
        if limits:
            _no_credentials(limits.parameters)
        if declared.portfolio_snapshot_id is None:
            if book is not None or limits is not None or request.portfolio is not None:
                _reject()  # Absent, flat and known book must remain different.
        elif (book is None or limits is None or request.portfolio is None
                or book.portfolio_id != declared.portfolio_snapshot_id or book.owner_id != owner_id
                or book.as_of != run.analysis_as_of or limits.owner_id != owner_id
                or limits.policy_id != declared.policy_id or limits.policy_version != declared.policy_version
                or limits.effective_at > run.analysis_as_of):
            _reject()
        plan = build_analyst_execution_plan(analysts)
        return _hash({"domain": "snapshot-recovery-fingerprint-v1", "owner_id": str(owner_id),
            "run_id": str(run.run_id), "instrument": request.instrument.model_dump(mode="json"),
            "as_of": run.analysis_as_of.isoformat(), "selected_analysts": analysts,
            "declared_config_hash": run.config_hash, "prompt_version": run.prompt_version,
            "report_language": run.report_language,
            "execution_limits": run.execution_limits.model_dump(mode="json") if run.execution_limits else None,
            "decision_inputs": declared.model_dump(mode="json"), "effective_config": config,
            "effective_graph_options": options, "resolved_clients": binding.model_dump(mode="json"),
            "runtime_digest": installed_runtime_digest(),
            "analyst_plan": [(spec.key, spec.agent_node, spec.clear_node) for spec in plan.specs],
            "profile": asdict(profile),
            "sources": {role: [source.manifest.model_dump(mode="json") for source in sources]
                        for role, sources in inputs.by_analyst.items()},
            "portfolio": book.model_dump(mode="json") if book else None,
            "rendered_portfolio": request.portfolio.model_dump(mode="json") if request.portfolio else None,
            "policy": limits.model_dump(mode="json") if limits else None,
            "risk_sources": [source.manifest.model_dump(mode="json") for source in risk]})
    except (ValueError, TypeError, KeyError, AttributeError, OSError, RecursionError):
        raise RecoveryFingerprintError("recovery inputs are invalid or incompatible") from None
