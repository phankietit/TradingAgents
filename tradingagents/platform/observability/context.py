"""Request correlation context that propagates across async tasks."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar

_request_id: ContextVar[str | None] = ContextVar("platform_request_id", default=None)


def get_request_id() -> str | None:
    return _request_id.get()


@contextmanager
def request_id_scope(request_id: str):
    token = _request_id.set(request_id)
    try:
        yield
    finally:
        _request_id.reset(token)
