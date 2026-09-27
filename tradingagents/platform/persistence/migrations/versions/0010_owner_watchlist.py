"""Persist owner watchlists without modifying portfolio or decision history."""

import sqlalchemy as sa
from alembic import op

revision = "0010_owner_watchlist"
down_revision = "0009_decision_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "watchlist_entries",
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("instrument_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["owner_accounts.owner_id"],
                                name="fk_watchlist_entries_owner_id_owner_accounts"),
        sa.ForeignKeyConstraint(["instrument_id"], ["instruments.instrument_id"],
                                name="fk_watchlist_entries_instrument_id_instruments"),
        sa.PrimaryKeyConstraint("owner_id", "instrument_id", name="pk_watchlist_entries"),
    )


def downgrade() -> None:
    op.drop_table("watchlist_entries")
