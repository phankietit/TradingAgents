"""Explicit database construction and transaction boundaries."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from math import ceil, isfinite

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker


class Database:
    """Own an engine and produce commit-or-rollback sessions."""

    def __init__(self, url: str, *, echo: bool = False):
        if not url or "://" not in url:
            raise ValueError("an explicit SQLAlchemy database URL is required")
        self.engine: Engine = create_engine(url, echo=echo, pool_pre_ping=True)
        self._sessions = sessionmaker(bind=self.engine, expire_on_commit=False)

    @contextmanager
    def session(self, *, lock_timeout_seconds: float | None = None) -> Iterator[Session]:
        if lock_timeout_seconds is not None:
            if (type(lock_timeout_seconds) not in (int, float)
                    or not isfinite(lock_timeout_seconds) or not 0 < lock_timeout_seconds <= 60):
                raise ValueError("invalid transaction lock timeout")
            with self._bounded_lock_session(ceil(lock_timeout_seconds * 1000)) as session:
                yield session
            return
        session = self._sessions()
        try:
            with session.begin():
                yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @contextmanager
    def _bounded_lock_session(self, milliseconds: int) -> Iterator[Session]:
        dialect = self.engine.dialect.name
        if dialect not in {"sqlite", "postgresql"}:
            raise ValueError("transaction lock timeout unsupported for this database")
        # Dedicated checked-out connection lets SQLite settings be restored
        # before returning it to the pool. No engine/global default changes.
        with self.engine.connect() as connection:
            old_timeout = None
            try:
                if dialect == "sqlite":
                    old_timeout = connection.exec_driver_sql("PRAGMA busy_timeout").scalar_one()
                    connection.exec_driver_sql(f"PRAGMA busy_timeout = {milliseconds}")
                    connection.commit()
                with Session(bind=connection, expire_on_commit=False) as session, session.begin():
                    if dialect == "postgresql":
                        for setting in ("lock_timeout", "statement_timeout"):
                            session.execute(text("SELECT set_config(:setting, :value, true)"),
                                            {"setting": setting, "value": f"{milliseconds}ms"})
                    yield session
            finally:
                if old_timeout is not None:
                    try:
                        connection.rollback()
                        # SQLite can retain its transaction after a failed
                        # COMMIT even when SQLAlchemy's transaction is already
                        # deactivated. Explicitly roll back this context's own
                        # DBAPI connection before restoring the old busy wait;
                        # otherwise cleanup can retry the failed COMMIT using
                        # the original (longer) timeout.
                        connection.connection.driver_connection.rollback()
                        connection.exec_driver_sql(f"PRAGMA busy_timeout = {int(old_timeout)}")
                        connection.commit()
                    except Exception:
                        # A connection whose local setting cannot be restored
                        # must not leak that setting to the next pooled user.
                        connection.invalidate()

    def dispose(self) -> None:
        self.engine.dispose()
