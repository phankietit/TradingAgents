"""Explicit database construction and transaction boundaries."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


class Database:
    """Own an engine and produce commit-or-rollback sessions."""

    def __init__(self, url: str, *, echo: bool = False):
        if not url or "://" not in url:
            raise ValueError("an explicit SQLAlchemy database URL is required")
        self.engine: Engine = create_engine(url, echo=echo, pool_pre_ping=True)
        self._sessions = sessionmaker(bind=self.engine, expire_on_commit=False)

    @contextmanager
    def session(self) -> Iterator[Session]:
        session = self._sessions()
        try:
            with session.begin():
                yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def dispose(self) -> None:
        self.engine.dispose()
