"""Append-only linked reader artifacts and atomic output receipt."""

import sqlalchemy as sa
from alembic import op

revision = "0016_linked_results"
down_revision = "0015_linked_dispatch"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("research_execution_artifacts",
        sa.Column("artifact_id", sa.Uuid(), nullable=False),
        sa.Column("execution_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["artifact_id"], ["artifacts.artifact_id"]),
        sa.ForeignKeyConstraint(["execution_id"], ["research_executions.execution_id"]),
        sa.PrimaryKeyConstraint("artifact_id"))
    op.create_index("ix_research_execution_artifacts_execution_id", "research_execution_artifacts", ["execution_id"])
    op.create_table("research_execution_completions",
        sa.Column("execution_id", sa.Uuid(), nullable=False),
        sa.Column("checkpoint_record_id", sa.Uuid(), nullable=False),
        sa.Column("checkpoint_hash", sa.String(64), nullable=False),
        sa.Column("report_artifact_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_artifact_id", sa.Uuid(), nullable=True),
        sa.Column("decision_id", sa.Uuid(), nullable=False),
        sa.Column("result_hash", sa.String(64), nullable=False),
        sa.Column("accounting_hash", sa.String(64), nullable=False),
        sa.Column("report_hash", sa.String(71), nullable=False),
        sa.Column("decision_hash", sa.String(64), nullable=False),
        sa.Column("evidence_hash", sa.String(71), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["execution_id"], ["research_executions.execution_id"]),
        sa.ForeignKeyConstraint(["checkpoint_record_id"], ["research_checkpoints.record_id"]),
        sa.ForeignKeyConstraint(["report_artifact_id"], ["artifacts.artifact_id"]),
        sa.ForeignKeyConstraint(["evidence_artifact_id"], ["artifacts.artifact_id"]),
        sa.ForeignKeyConstraint(["decision_id"], ["decisions.decision_id"]),
        sa.PrimaryKeyConstraint("execution_id"),
        sa.UniqueConstraint("report_artifact_id", name="uq_linked_completion_report"),
        sa.UniqueConstraint("decision_id", name="uq_linked_completion_decision"))


def downgrade() -> None:
    # Disposable empty-schema tests only; never automatic private-history cleanup.
    op.drop_table("research_execution_completions")
    op.drop_index("ix_research_execution_artifacts_execution_id", table_name="research_execution_artifacts")
    op.drop_table("research_execution_artifacts")
