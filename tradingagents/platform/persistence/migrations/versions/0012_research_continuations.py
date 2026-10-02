"""Append-only research consent identity, separate from historical jobs/runs."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0012_research_continuations"
down_revision = "0011_research_checkpoints"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "research_continuations",
        sa.Column("execution_id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("source_run_id", sa.Uuid(), nullable=False),
        sa.Column("source_job_id", sa.Uuid(), nullable=False),
        sa.Column("checkpoint_record_id", sa.Uuid(), nullable=False),
        sa.Column("source_event_sequence", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(36), nullable=False),
        sa.Column("observation_hash", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON().with_variant(JSONB(), "postgresql"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["owner_accounts.owner_id"]),
        sa.ForeignKeyConstraint(["source_run_id"], ["analysis_runs.run_id"]),
        sa.ForeignKeyConstraint(["source_job_id"], ["analysis_jobs.job_id"]),
        sa.ForeignKeyConstraint(["checkpoint_record_id"], ["research_checkpoints.record_id"]),
        sa.PrimaryKeyConstraint("execution_id"),
        sa.UniqueConstraint("owner_id", "idempotency_key"),
        sa.UniqueConstraint("source_run_id", "source_event_sequence", "checkpoint_record_id"),
    )
    op.create_index("ix_research_continuations_owner_run", "research_continuations", ["owner_id", "source_run_id"])


def downgrade() -> None:
    # Explicit operator migration only. Never called by runtime recovery.
    op.drop_index("ix_research_continuations_owner_run", table_name="research_continuations")
    op.drop_table("research_continuations")
