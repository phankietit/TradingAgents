"""Append-only linked provenance; no historical table rebuild or backfill."""

import sqlalchemy as sa
from alembic import op

revision = "0014_linked_publication"
down_revision = "0013_research_executions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("research_execution_entries",
        sa.Column("execution_id", sa.Uuid(), nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["execution_id"], ["research_executions.execution_id"]),
        sa.ForeignKeyConstraint(["event_id"], ["run_events.event_id"]),
        sa.PrimaryKeyConstraint("execution_id"), sa.UniqueConstraint("event_id"))
    for table, key, target in (
        ("research_execution_events", "event_id", "run_events.event_id"),
        ("research_checkpoint_executions", "record_id", "research_checkpoints.record_id"),
    ):
        op.create_table(table,
            sa.Column(key, sa.Uuid(), nullable=False),
            sa.Column("execution_id", sa.Uuid(), nullable=False),
            sa.ForeignKeyConstraint([key], [target]),
            sa.ForeignKeyConstraint(["execution_id"], ["research_executions.execution_id"]),
            sa.PrimaryKeyConstraint(key))
        op.create_index(f"ix_{table}_execution_id", table, ["execution_id"])


def downgrade() -> None:
    # Explicit disposable verification only; never automatically delete evidence.
    for table in ("research_checkpoint_executions", "research_execution_events"):
        op.drop_index(f"ix_{table}_execution_id", table_name=table)
        op.drop_table(table)
    op.drop_table("research_execution_entries")
