"""Separate lease records; original research job/run/evidence stay immutable."""

import sqlalchemy as sa
from alembic import op

revision = "0013_research_executions"
down_revision = "0012_research_continuations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "research_executions",
        sa.Column("execution_id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("source_run_id", sa.Uuid(), nullable=False),
        sa.Column("source_job_id", sa.Uuid(), nullable=False),
        sa.Column("observation_hash", sa.String(64), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("worker_id", sa.String(128)),
        sa.Column("lease_token_hash", sa.String(64)),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("deadline_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["execution_id"], ["research_continuations.execution_id"]),
        sa.ForeignKeyConstraint(["owner_id"], ["owner_accounts.owner_id"]),
        sa.ForeignKeyConstraint(["source_run_id"], ["analysis_runs.run_id"]),
        sa.ForeignKeyConstraint(["source_job_id"], ["analysis_jobs.job_id"]),
        sa.PrimaryKeyConstraint("execution_id"),
        sa.UniqueConstraint("source_run_id", "attempt", name="uq_research_executions_run_attempt"),
        sa.CheckConstraint("attempt >= 2 AND attempt <= 1000000", name="attempt"),
        sa.CheckConstraint("status IN ('reserved', 'leased', 'cancel_requested', 'cancelled', 'review_required')",
                           name="status"),
    )
    op.create_index("ix_research_executions_owner_run", "research_executions", ["owner_id", "source_run_id"])


def downgrade() -> None:
    # Explicit disposable verification/operator action, never automatic recovery.
    op.drop_index("ix_research_executions_owner_run", table_name="research_executions")
    op.drop_table("research_executions")
