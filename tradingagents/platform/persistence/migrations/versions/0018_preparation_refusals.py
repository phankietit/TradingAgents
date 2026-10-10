"""Append-only preclaim refusal; no original history or execution rewrite."""

import sqlalchemy as sa
from alembic import op

revision = "0018_preparation_refusals"
down_revision = "0017_linked_stops"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("research_preparation_refusals",
        sa.Column("execution_id", sa.Uuid(), nullable=False),
        sa.Column("observation_hash", sa.String(64), nullable=False),
        sa.Column("worker_id", sa.String(128), nullable=False),
        sa.Column("refused_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(["execution_id"], ["research_executions.execution_id"]),
        sa.PrimaryKeyConstraint("execution_id"))


def downgrade():
    # Explicit operator/disposable-test migration, never automatic recovery.
    op.drop_table("research_preparation_refusals")
