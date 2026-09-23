"""Structured JSON logging that fails closed around private and secret values."""

from __future__ import annotations

import json
import logging
import re
import sys
from datetime import UTC, datetime
from typing import Any, TextIO

from .context import get_request_id

REDACTED = "<redacted>"
SENSITIVE_KEY_PARTS = {
    "account",
    "authorization",
    "cookie",
    "credential",
    "database_url",
    "holdings",
    "owner",
    "password",
    "portfolio",
    "secret",
    "session",
    "token",
}
URL_CREDENTIAL_PATTERN = re.compile(r"(://[^:/\s]+:)[^@/\s]+(@)")
BEARER_PATTERN = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+\-/]+=*")
SESSION_PATTERN = re.compile(r"\bta_session_[A-Za-z0-9_-]+")
API_KEY_PATTERN = re.compile(r"\bsk-[A-Za-z0-9_-]{12,}")
STANDARD_LOG_RECORD_FIELDS = set(logging.makeLogRecord({}).__dict__) | {
    "message",
    "asctime",
}


def _sensitive_key(key: str) -> bool:
    normalized = key.casefold()
    return any(part in normalized for part in SENSITIVE_KEY_PARTS)


def _redact_text(value: str) -> str:
    value = URL_CREDENTIAL_PATTERN.sub(r"\1<redacted>\2", value)
    value = BEARER_PATTERN.sub("Bearer <redacted>", value)
    value = SESSION_PATTERN.sub(REDACTED, value)
    return API_KEY_PATTERN.sub(REDACTED, value)


def redact_value(value: Any, *, key: str | None = None) -> Any:
    if key is not None and _sensitive_key(key):
        return REDACTED
    if isinstance(value, dict):
        return {
            str(item_key): redact_value(item, key=str(item_key)) for item_key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [redact_value(item) for item in value]
    if isinstance(value, str):
        return _redact_text(value)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return _redact_text(str(value))


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": _redact_text(record.getMessage()),
        }
        request_id = getattr(record, "request_id", None) or get_request_id()
        if request_id:
            payload["request_id"] = request_id
        for key, value in record.__dict__.items():
            if key not in STANDARD_LOG_RECORD_FIELDS and key != "request_id":
                payload[key] = redact_value(value, key=key)
        if record.exc_info:
            payload["exception_type"] = record.exc_info[0].__name__
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def configure_platform_logging(
    *, level: int = logging.INFO, stream: TextIO | None = None
) -> logging.Logger:
    handler = logging.StreamHandler(stream or sys.stderr)
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("tradingagents.platform")
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    return logger
