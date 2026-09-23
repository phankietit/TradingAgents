"""FastAPI application factory for the private platform API."""

from .app import create_app
from .settings import ApiSettings

__all__ = ["ApiSettings", "create_app"]
