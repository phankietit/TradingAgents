"""Single-use linked spawn boundary; do not rewrite original research rows."""

import sqlalchemy as sa
from alembic import op

revision = "0015_linked_dispatch"
down_revision = "0014_linked_publication"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("research_execution_dispatches",
        sa.Column("execution_id", sa.Uuid(), nullable=False),
        sa.Column("checkpoint_record_id", sa.Uuid(), nullable=False),
        sa.Column("checkpoint_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["execution_id"], ["research_executions.execution_id"]),
        sa.ForeignKeyConstraint(["checkpoint_record_id"], ["research_checkpoints.record_id"]),
        sa.PrimaryKeyConstraint("execution_id"))


def downgrade() -> None:
    # Explicit disposable tests only; never automatically delete private evidence.
    op.drop_table("research_execution_dispatches")
