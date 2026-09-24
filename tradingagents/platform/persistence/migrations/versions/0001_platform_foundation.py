"""Create platform foundation tables.

Revision ID: 0001_platform_foundation
Revises: None
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001_platform_foundation"
down_revision = None
branch_labels = None
depends_on = None

JSON_VALUE = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    """Create the frozen v1 persistence schema."""

    op.create_table(
        "instruments",
        sa.Column("instrument_id", sa.Uuid(), nullable=False),
        sa.Column("schema_version", sa.String(length=16), nullable=False),
        sa.Column("symbol", sa.String(length=64), nullable=False),
        sa.Column("canonical_symbol", sa.String(length=64), nullable=False),
        sa.Column("asset_class", sa.String(length=32), nullable=False),
        sa.Column("tradability", sa.String(length=32), nullable=False),
        sa.Column("payload", JSON_VALUE, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("instrument_id", name="pk_instruments"),
        sa.UniqueConstraint("canonical_symbol", name="uq_instruments_canonical_symbol"),
    )
    op.create_index("ix_instruments_asset_class", "instruments", ["asset_class"])

    op.create_table(
        "snapshots",
        sa.Column("snapshot_id", sa.Uuid(), nullable=False),
        sa.Column("instrument_id", sa.Uuid(), nullable=False),
        sa.Column("schema_version", sa.String(length=16), nullable=False),
        sa.Column("dataset", sa.String(length=128), nullable=False),
        sa.Column("vendor", sa.String(length=64), nullable=False),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("content_hash", sa.String(length=71), nullable=False),
        sa.Column("quality_status", sa.String(length=32), nullable=False),
        sa.Column("payload", JSON_VALUE, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["instrument_id"],
            ["instruments.instrument_id"],
            name="fk_snapshots_instrument_id_instruments",
        ),
        sa.PrimaryKeyConstraint("snapshot_id", name="pk_snapshots"),
        sa.UniqueConstraint(
            "instrument_id",
            "dataset",
            "content_hash",
            name="uq_snapshots_instrument_id",
        ),
    )
    op.create_index("ix_snapshots_instrument_as_of", "snapshots", ["instrument_id", "as_of"])
    op.create_index("ix_snapshots_quality_status", "snapshots", ["quality_status"])

    op.create_table(
        "analysis_runs",
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("instrument_id", sa.Uuid(), nullable=False),
        sa.Column("schema_version", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("analysis_as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", JSON_VALUE, nullable=False),
        sa.ForeignKeyConstraint(
            ["instrument_id"],
            ["instruments.instrument_id"],
            name="fk_analysis_runs_instrument_id_instruments",
        ),
        sa.PrimaryKeyConstraint("run_id", name="pk_analysis_runs"),
    )
    op.create_index("ix_analysis_runs_owner_id", "analysis_runs", ["owner_id"])
    op.create_index("ix_analysis_runs_status", "analysis_runs", ["status"])
    op.create_index("ix_runs_owner_created", "analysis_runs", ["owner_id", "created_at"])

    op.create_table(
        "decisions",
        sa.Column("decision_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("instrument_id", sa.Uuid(), nullable=False),
        sa.Column("schema_version", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("rating", sa.String(length=32), nullable=False),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", JSON_VALUE, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["instrument_id"],
            ["instruments.instrument_id"],
            name="fk_decisions_instrument_id_instruments",
        ),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["analysis_runs.run_id"],
            name="fk_decisions_run_id_analysis_runs",
        ),
        sa.PrimaryKeyConstraint("decision_id", name="pk_decisions"),
        sa.UniqueConstraint("run_id", name="uq_decisions_run_id"),
    )
    op.create_index("ix_decisions_owner_id", "decisions", ["owner_id"])
    op.create_index("ix_decisions_status", "decisions", ["status"])
    op.create_index("ix_decisions_owner_as_of", "decisions", ["owner_id", "as_of"])

    op.create_table(
        "portfolio_snapshots",
        sa.Column("portfolio_id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("schema_version", sa.String(length=16), nullable=False),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("content_hash", sa.String(length=71), nullable=False),
        sa.Column("payload", JSON_VALUE, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("portfolio_id", name="pk_portfolio_snapshots"),
    )
    op.create_index("ix_portfolio_snapshots_owner_id", "portfolio_snapshots", ["owner_id"])
    op.create_index("ix_portfolios_owner_as_of", "portfolio_snapshots", ["owner_id", "as_of"])

    op.create_table(
        "policies",
        sa.Column("policy_id", sa.Uuid(), nullable=False),
        sa.Column("policy_version", sa.String(length=64), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("schema_version", sa.String(length=16), nullable=False),
        sa.Column("asset_class", sa.String(length=32), nullable=False),
        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", JSON_VALUE, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("policy_id", "policy_version", name="pk_policies"),
    )
    op.create_index("ix_policies_owner_id", "policies", ["owner_id"])
    op.create_index("ix_policies_owner_effective", "policies", ["owner_id", "effective_at"])


def downgrade() -> None:
    op.drop_index("ix_policies_owner_effective", table_name="policies")
    op.drop_index("ix_policies_owner_id", table_name="policies")
    op.drop_table("policies")
    op.drop_index("ix_portfolios_owner_as_of", table_name="portfolio_snapshots")
    op.drop_index("ix_portfolio_snapshots_owner_id", table_name="portfolio_snapshots")
    op.drop_table("portfolio_snapshots")
    op.drop_index("ix_decisions_owner_as_of", table_name="decisions")
    op.drop_index("ix_decisions_status", table_name="decisions")
    op.drop_index("ix_decisions_owner_id", table_name="decisions")
    op.drop_table("decisions")
    op.drop_index("ix_runs_owner_created", table_name="analysis_runs")
    op.drop_index("ix_analysis_runs_status", table_name="analysis_runs")
    op.drop_index("ix_analysis_runs_owner_id", table_name="analysis_runs")
    op.drop_table("analysis_runs")
    op.drop_index("ix_snapshots_quality_status", table_name="snapshots")
    op.drop_index("ix_snapshots_instrument_as_of", table_name="snapshots")
    op.drop_table("snapshots")
    op.drop_index("ix_instruments_asset_class", table_name="instruments")
    op.drop_table("instruments")
