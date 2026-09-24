"""Programmatic Alembic entry points with an explicit database URL."""

from __future__ import annotations

from importlib.resources import files

from alembic import command
from alembic.config import Config


def migration_config(database_url: str) -> Config:
    if not database_url or "://" not in database_url:
        raise ValueError("an explicit database URL is required for migrations")
    config = Config()
    config.set_main_option(
        "script_location",
        str(files("tradingagents.platform.persistence.migrations")),
    )
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    return config


def upgrade_database(database_url: str, revision: str = "head") -> None:
    command.upgrade(migration_config(database_url), revision)


def downgrade_database(database_url: str, revision: str = "base") -> None:
    command.downgrade(migration_config(database_url), revision)
