"""Local-only API process entrypoint with explicit environment configuration."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

import uvicorn

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
    return ApiSettings(
        database_url=_required(source, "TRADINGAGENTS_DATABASE_URL"),
        artifact_root=Path(_required(source, "TRADINGAGENTS_ARTIFACT_ROOT")),
        allowed_origin=_required(source, "TRADINGAGENTS_ALLOWED_ORIGIN"),
        secure_cookies=_boolean(source, "TRADINGAGENTS_SECURE_COOKIES", default=True),
    )


def main() -> None:
    settings = load_api_settings()
    try:
        port = int(os.environ.get("TRADINGAGENTS_API_PORT", "8000"))
    except ValueError as error:
        raise RuntimeError("TRADINGAGENTS_API_PORT must be an integer") from error
    if not 1 <= port <= 65535:
        raise RuntimeError("TRADINGAGENTS_API_PORT must be between 1 and 65535")
    # Binding stays local until a separately reviewed deployment exposes the service.
    uvicorn.run(create_app(settings), host="127.0.0.1", port=port, log_config=None)
