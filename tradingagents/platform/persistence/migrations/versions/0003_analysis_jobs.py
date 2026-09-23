"""Add durable analysis jobs.

Revision ID: 0003_analysis_jobs
Revises: 0002_artifact_manifests
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003_analysis_jobs"
down_revision = "0002_artifact_manifests"
branch_labels = None
depends_on = None

JSON_VALUE = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "analysis_jobs",
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("schema_version", sa.String(length=16), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("payload", JSON_VALUE, nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("lease_owner", sa.String(length=128), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("output_artifact_ids", JSON_VALUE, nullable=False),
        sa.Column("error_code", sa.String(length=128), nullable=True),
        sa.Column("error_message", sa.String(length=2048), nullable=True),
        sa.ForeignKeyConstraint(
            ["run_id"], ["analysis_runs.run_id"], name="fk_analysis_jobs_run_id_analysis_runs"
        ),
        sa.PrimaryKeyConstraint("job_id", name="pk_analysis_jobs"),
        sa.UniqueConstraint("owner_id", "idempotency_key", name="uq_analysis_jobs_owner_id"),
        sa.UniqueConstraint("run_id", name="uq_analysis_jobs_run_id"),
    )
    op.create_index("ix_analysis_jobs_owner_id", "analysis_jobs", ["owner_id"])
    op.create_index("ix_analysis_jobs_status", "analysis_jobs", ["status"])
    op.create_index("ix_jobs_claim", "analysis_jobs", ["status", "available_at", "created_at"])
    op.create_index("ix_jobs_expired_lease", "analysis_jobs", ["status", "lease_expires_at"])
    op.create_index("ix_jobs_owner_created", "analysis_jobs", ["owner_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_jobs_owner_created", table_name="analysis_jobs")
    op.drop_index("ix_jobs_expired_lease", table_name="analysis_jobs")
    op.drop_index("ix_jobs_claim", table_name="analysis_jobs")
    op.drop_index("ix_analysis_jobs_status", table_name="analysis_jobs")
    op.drop_index("ix_analysis_jobs_owner_id", table_name="analysis_jobs")
    op.drop_table("analysis_jobs")
