"""Separate append-only local supervision stop facts; no historical backfill."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0017_linked_stops"
down_revision = "0016_linked_results"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("research_execution_stops",
        sa.Column("execution_id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("source_run_id", sa.Uuid(), nullable=False),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON().with_variant(JSONB(), "postgresql"), nullable=False),
        sa.Column("stopped_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["execution_id"], ["research_executions.execution_id"]),
        sa.ForeignKeyConstraint(["owner_id"], ["owner_accounts.owner_id"]),
        sa.ForeignKeyConstraint(["source_run_id"], ["analysis_runs.run_id"]),
        sa.PrimaryKeyConstraint("execution_id"))


def downgrade() -> None:
    # Explicit disposable QA only; never automatically remove private receipts.
    op.drop_table("research_execution_stops")
