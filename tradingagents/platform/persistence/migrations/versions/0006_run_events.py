"""Add append-only run events.

Revision ID: 0006_run_events
Revises: 0005_session_csrf
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0006_run_events"
down_revision = "0005_session_csrf"
branch_labels = None
depends_on = None

JSON_VALUE = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "run_events",
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("schema_version", sa.String(length=16), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", JSON_VALUE, nullable=False),
        sa.ForeignKeyConstraint(
            ["run_id"], ["analysis_runs.run_id"], name="fk_run_events_run_id_analysis_runs"
        ),
        sa.PrimaryKeyConstraint("event_id", name="pk_run_events"),
        sa.UniqueConstraint("run_id", "sequence", name="uq_run_events_run_id"),
    )
    op.create_index("ix_run_events_event_type", "run_events", ["event_type"])
    op.create_index("ix_run_events_owner_id", "run_events", ["owner_id"])
    op.create_index(
        "ix_run_events_owner_run_sequence",
        "run_events",
        ["owner_id", "run_id", "sequence"],
    )


def downgrade() -> None:
    op.drop_index("ix_run_events_owner_run_sequence", table_name="run_events")
    op.drop_index("ix_run_events_owner_id", table_name="run_events")
    op.drop_index("ix_run_events_event_type", table_name="run_events")
    op.drop_table("run_events")
