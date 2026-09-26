"""Explicit server-side settings for the private API."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

from tradingagents._compat import UTC


@dataclass(frozen=True, slots=True)
class ApiSettings:
    database_url: str = field(repr=False)
    artifact_root: Path
    allowed_origin: str
    secure_cookies: bool = True
    session_ttl: timedelta = timedelta(hours=12)
    llm_provider: str = "openai"
    quick_model: str = "gpt-4o-mini"
    deep_model: str = "gpt-4o"
    prompt_version: str = "1"
    max_job_attempts: int = 3
    allowed_analysts: tuple[str, ...] = ("market", "social", "news", "fundamentals")
    event_poll_interval: float = 0.5
    event_keepalive_interval: float = 15.0
    event_retry_milliseconds: int = 2000
    clock: Callable[[], datetime] = lambda: datetime.now(UTC)

    def __post_init__(self) -> None:
        if not self.database_url or "://" not in self.database_url:
            raise ValueError("database_url must be explicit")
        parsed = urlparse(self.allowed_origin)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.netloc
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path not in {"", "/"}
            or parsed.params
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("allowed_origin must be one exact HTTP(S) origin")
        if self.secure_cookies and parsed.scheme != "https":
            raise ValueError("secure cookies require an HTTPS allowed_origin")
        if not 1 <= self.max_job_attempts <= 20:
            raise ValueError("max_job_attempts must be between 1 and 20")
        if not self.allowed_analysts or len(self.allowed_analysts) != len(
            set(self.allowed_analysts)
        ):
            raise ValueError("allowed_analysts must be non-empty and unique")
        if self.event_poll_interval <= 0:
            raise ValueError("event_poll_interval must be positive")
        if self.event_keepalive_interval < self.event_poll_interval:
            raise ValueError("event_keepalive_interval must not be shorter than polling")
        if not 100 <= self.event_retry_milliseconds <= 60_000:
            raise ValueError("event_retry_milliseconds must be between 100 and 60000")
