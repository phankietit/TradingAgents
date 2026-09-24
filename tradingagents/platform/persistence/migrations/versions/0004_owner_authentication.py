"""Add single-owner credentials and opaque sessions.

Revision ID: 0004_owner_authentication
Revises: 0003_analysis_jobs
"""

import sqlalchemy as sa
from alembic import op

revision = "0004_owner_authentication"
down_revision = "0003_analysis_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "owner_accounts",
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("singleton_key", sa.String(length=16), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("password_hash", sa.String(length=256), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("owner_id", name="pk_owner_accounts"),
        sa.UniqueConstraint("email", name="uq_owner_accounts_email"),
        sa.UniqueConstraint("singleton_key", name="uq_owner_accounts_singleton_key"),
    )
    op.create_index("ix_owner_accounts_status", "owner_accounts", ["status"])

    op.create_table(
        "owner_sessions",
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["owner_accounts.owner_id"],
            name="fk_owner_sessions_owner_id_owner_accounts",
        ),
        sa.PrimaryKeyConstraint("session_id", name="pk_owner_sessions"),
        sa.UniqueConstraint("token_hash", name="uq_owner_sessions_token_hash"),
    )
    op.create_index("ix_owner_sessions_expires_at", "owner_sessions", ["expires_at"])
    op.create_index("ix_owner_sessions_owner_id", "owner_sessions", ["owner_id"])
    op.create_index("ix_owner_sessions_owner_expiry", "owner_sessions", ["owner_id", "expires_at"])


def downgrade() -> None:
    op.drop_index("ix_owner_sessions_owner_expiry", table_name="owner_sessions")
    op.drop_index("ix_owner_sessions_owner_id", table_name="owner_sessions")
    op.drop_index("ix_owner_sessions_expires_at", table_name="owner_sessions")
    op.drop_table("owner_sessions")
    op.drop_index("ix_owner_accounts_status", table_name="owner_accounts")
    op.drop_table("owner_accounts")
