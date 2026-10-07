"""Local-only API process entrypoint with explicit environment configuration."""

from __future__ import annotations

import argparse
import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from urllib.parse import urlparse

import uvicorn

from tradingagents.platform.observability import configure_platform_logging

from .app import create_app
from .settings import ApiSettings


def _required(environ: Mapping[str, str], name: str) -> str:
    value = environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"required API setting is missing: {name}")
    return value


def _boolean(environ: Mapping[str, str], name: str, *, default: bool) -> bool:
    value = environ.get(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized not in {"true", "false"}:
        raise RuntimeError(f"{name} must be true or false")
    return normalized == "true"


def load_api_settings(environ: Mapping[str, str] | None = None) -> ApiSettings:
    source = environ if environ is not None else os.environ
    # Persist the operator's model selection on each run; the worker consumes
    # that manifest rather than substituting its own model environment.
    model_settings = {
        field: source[name].strip()
        for field, name in (
            ("llm_provider", "TRADINGAGENTS_LLM_PROVIDER"),
            ("quick_model", "TRADINGAGENTS_QUICK_THINK_LLM"),
            ("deep_model", "TRADINGAGENTS_DEEP_THINK_LLM"),
        )
        if source.get(name, "").strip()
    }
    return ApiSettings(
        database_url=_required(source, "TRADINGAGENTS_DATABASE_URL"),
        artifact_root=Path(_required(source, "TRADINGAGENTS_ARTIFACT_ROOT")),
        allowed_origin=_required(source, "TRADINGAGENTS_ALLOWED_ORIGIN"),
        secure_cookies=_boolean(source, "TRADINGAGENTS_SECURE_COOKIES", default=True),
        web_root=Path(source["TRADINGAGENTS_WEB_ROOT"]) if source.get("TRADINGAGENTS_WEB_ROOT", "").strip() else None,
        **model_settings,
    )


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="tradingagents-api",
        description="Serve the private TradingAgents API on local loopback only.",
        epilog=("Configure TRADINGAGENTS_DATABASE_URL, TRADINGAGENTS_ARTIFACT_ROOT and "
                "TRADINGAGENTS_ALLOWED_ORIGIN before starting. Optional settings include "
                "TRADINGAGENTS_API_PORT, TRADINGAGENTS_SECURE_COOKIES and TRADINGAGENTS_WEB_ROOT. "
                "Credentials remain in server environment variables, never command-line options."),
        allow_abbrev=False,
    )
    _, unknown = parser.parse_known_args(argv)
    if unknown:
        # Refuse before configuration/DB/logging/server admission. Do not echo
        # argument values: an operator may have pasted a private value here.
        parser.error("unrecognized command-line options; use --help")
    settings = load_api_settings()
    configure_platform_logging()
    try:
        port = int(os.environ.get("TRADINGAGENTS_API_PORT", "8000"))
    except ValueError as error:
        raise RuntimeError("TRADINGAGENTS_API_PORT must be an integer") from error
    if not 1 <= port <= 65535:
        raise RuntimeError("TRADINGAGENTS_API_PORT must be between 1 and 65535")
    if settings.web_root is not None and urlparse(settings.allowed_origin).port != port:
        raise RuntimeError("built web origin port must equal TRADINGAGENTS_API_PORT")
    # Binding stays local until a separately reviewed deployment exposes the service.
    uvicorn.run(
        create_app(settings),
        host="127.0.0.1",
        port=port,
        log_config=None,
        access_log=False,
    )
