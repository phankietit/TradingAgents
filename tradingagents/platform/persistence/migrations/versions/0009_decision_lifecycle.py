"""Add immutable decision lifecycle audit events.

Revision ID: 0009_decision_lifecycle
Revises: 0008_portfolio_ledger
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0009_decision_lifecycle"
down_revision = "0008_portfolio_ledger"
branch_labels = None
depends_on = None

JSON_VALUE = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "decision_lifecycle_events",
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("decision_id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("schema_version", sa.String(length=16), nullable=False),
        sa.Column("from_status", sa.String(length=32), nullable=False),
        sa.Column("to_status", sa.String(length=32), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", JSON_VALUE, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["decision_id"], ["decisions.decision_id"],
            name="fk_decision_lifecycle_events_decision_id_decisions",
        ),
        sa.PrimaryKeyConstraint("event_id", name="pk_decision_lifecycle_events"),
    )
    op.create_index(
        "ix_decision_lifecycle_events_owner_id",
        "decision_lifecycle_events",
        ["owner_id"],
    )
    op.create_index(
        "ix_decision_events_owner_decision_time",
        "decision_lifecycle_events",
        ["owner_id", "decision_id", "occurred_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_decision_events_owner_decision_time", table_name="decision_lifecycle_events")
    op.drop_index("ix_decision_lifecycle_events_owner_id", table_name="decision_lifecycle_events")
    op.drop_table("decision_lifecycle_events")
