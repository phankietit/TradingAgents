"""Add namespaced aliases for deterministic instrument resolution.

Revision ID: 0007_instrument_aliases
Revises: 0006_run_events
"""

import unicodedata
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision = "0007_instrument_aliases"
down_revision = "0006_run_events"
branch_labels = None
depends_on = None


def _normalize_alias(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).strip().casefold()
    if not normalized or any(
        unicodedata.category(character).startswith("C") for character in normalized
    ):
        raise ValueError("existing canonical symbol cannot be normalized safely")
    return normalized


def upgrade() -> None:
    op.create_table(
        "instrument_aliases",
        sa.Column("namespace", sa.String(length=32), nullable=False),
        sa.Column("normalized_alias", sa.String(length=128), nullable=False),
        sa.Column("instrument_id", sa.Uuid(), nullable=False),
        sa.Column("schema_version", sa.String(length=16), nullable=False),
        sa.Column("alias", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["instrument_id"],
            ["instruments.instrument_id"],
            name="fk_instrument_aliases_instrument_id_instruments",
        ),
        sa.PrimaryKeyConstraint(
            "namespace",
            "normalized_alias",
            name="pk_instrument_aliases",
        ),
    )
    op.create_index(
        "ix_instrument_aliases_instrument",
        "instrument_aliases",
        ["instrument_id"],
    )
    op.create_index(
        "ix_instrument_aliases_lookup",
        "instrument_aliases",
        ["normalized_alias"],
    )

    instruments = sa.table(
        "instruments",
        sa.column("instrument_id", sa.Uuid()),
        sa.column("schema_version", sa.String()),
        sa.column("canonical_symbol", sa.String()),
    )
    aliases = sa.table(
        "instrument_aliases",
        sa.column("namespace", sa.String()),
        sa.column("normalized_alias", sa.String()),
        sa.column("instrument_id", sa.Uuid()),
        sa.column("schema_version", sa.String()),
        sa.column("alias", sa.String()),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )
    rows = op.get_bind().execute(
        sa.select(
            instruments.c.instrument_id,
            instruments.c.schema_version,
            instruments.c.canonical_symbol,
        ).order_by(instruments.c.canonical_symbol)
    )
    created_at = datetime.now(UTC)
    for row in rows.mappings():
        op.execute(
            aliases.insert().values(
                namespace="canonical",
                normalized_alias=_normalize_alias(row["canonical_symbol"]),
                instrument_id=row["instrument_id"],
                schema_version=row["schema_version"],
                alias=row["canonical_symbol"],
                created_at=created_at,
            )
        )


def downgrade() -> None:
    op.drop_index("ix_instrument_aliases_lookup", table_name="instrument_aliases")
    op.drop_index("ix_instrument_aliases_instrument", table_name="instrument_aliases")
    op.drop_table("instrument_aliases")
