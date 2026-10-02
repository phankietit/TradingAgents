"""Private append-only recovery records, separate from report artifacts."""

import sqlalchemy as sa
from alembic import op

revision = "0011_research_checkpoints"
down_revision = "0010_owner_watchlist"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "research_checkpoints",
        sa.Column("record_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("checkpoint_id", sa.Uuid(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("payload", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["analysis_runs.run_id"]),
        sa.ForeignKeyConstraint(["job_id"], ["analysis_jobs.job_id"]),
        sa.PrimaryKeyConstraint("record_id"),
        sa.UniqueConstraint("run_id", "sequence", name="uq_research_checkpoints_run_sequence"),
        sa.UniqueConstraint("run_id", "content_hash", name="uq_research_checkpoints_run_content_hash"),
    )
    op.create_index("ix_research_checkpoints_owner_run", "research_checkpoints",
                    ["owner_id", "run_id", "sequence"])


def downgrade() -> None:
    op.drop_index("ix_research_checkpoints_owner_run", table_name="research_checkpoints")
    op.drop_table("research_checkpoints")
