"""Add immutable owner-scoped portfolio ledger transactions.

Revision ID: 0008_portfolio_ledger
Revises: 0007_instrument_aliases
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0008_portfolio_ledger"
down_revision = "0007_instrument_aliases"
branch_labels = None
depends_on = None

JSON_VALUE = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "ledger_transactions",
        sa.Column("transaction_id", sa.Uuid(), nullable=False),
        sa.Column("ledger_id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("schema_version", sa.String(length=16), nullable=False),
        sa.Column("transaction_type", sa.String(length=32), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", JSON_VALUE, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("transaction_id", name="pk_ledger_transactions"),
    )
    op.create_index("ix_ledger_transactions_ledger_id", "ledger_transactions", ["ledger_id"])
    op.create_index("ix_ledger_transactions_owner_id", "ledger_transactions", ["owner_id"])
    op.create_index(
        "ix_ledger_transactions_owner_ledger_time",
        "ledger_transactions",
        ["owner_id", "ledger_id", "occurred_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_ledger_transactions_owner_ledger_time", table_name="ledger_transactions")
    op.drop_index("ix_ledger_transactions_owner_id", table_name="ledger_transactions")
    op.drop_index("ix_ledger_transactions_ledger_id", table_name="ledger_transactions")
    op.drop_table("ledger_transactions")
