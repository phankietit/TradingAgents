"""Add immutable artifact manifests.

Revision ID: 0002_artifact_manifests
Revises: 0001_platform_foundation
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002_artifact_manifests"
down_revision = "0001_platform_foundation"
branch_labels = None
depends_on = None

JSON_VALUE = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "artifacts",
        sa.Column("artifact_id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=True),
        sa.Column("instrument_id", sa.Uuid(), nullable=True),
        sa.Column("snapshot_id", sa.Uuid(), nullable=True),
        sa.Column("schema_version", sa.String(length=16), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("media_type", sa.String(length=128), nullable=False),
        sa.Column("content_hash", sa.String(length=71), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("storage_key", sa.String(length=160), nullable=False),
        sa.Column("payload", JSON_VALUE, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["instrument_id"],
            ["instruments.instrument_id"],
            name="fk_artifacts_instrument_id_instruments",
        ),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["analysis_runs.run_id"],
            name="fk_artifacts_run_id_analysis_runs",
        ),
        sa.ForeignKeyConstraint(
            ["snapshot_id"],
            ["snapshots.snapshot_id"],
            name="fk_artifacts_snapshot_id_snapshots",
        ),
        sa.PrimaryKeyConstraint("artifact_id", name="pk_artifacts"),
    )
    op.create_index("ix_artifacts_content_hash", "artifacts", ["content_hash"])
    op.create_index("ix_artifacts_kind", "artifacts", ["kind"])
    op.create_index("ix_artifacts_owner_id", "artifacts", ["owner_id"])
    op.create_index("ix_artifacts_owner_created", "artifacts", ["owner_id", "created_at"])
    op.create_index("ix_artifacts_owner_run", "artifacts", ["owner_id", "run_id"])


def downgrade() -> None:
    op.drop_index("ix_artifacts_owner_run", table_name="artifacts")
    op.drop_index("ix_artifacts_owner_created", table_name="artifacts")
    op.drop_index("ix_artifacts_owner_id", table_name="artifacts")
    op.drop_index("ix_artifacts_kind", table_name="artifacts")
    op.drop_index("ix_artifacts_content_hash", table_name="artifacts")
    op.drop_table("artifacts")
