"""Bind a CSRF token to every owner session.

Revision ID: 0005_session_csrf
Revises: 0004_owner_authentication
"""

import sqlalchemy as sa
from alembic import op

revision = "0005_session_csrf"
down_revision = "0004_owner_authentication"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "owner_sessions",
        sa.Column("csrf_token_hash", sa.String(length=64), nullable=True),
    )
    # Existing sessions cannot prove a CSRF secret, so force a safe re-login.
    op.execute(
        sa.text(
            "UPDATE owner_sessions "
            "SET csrf_token_hash = :invalid_hash, "
            "revoked_at = COALESCE(revoked_at, CURRENT_TIMESTAMP)"
        ).bindparams(invalid_hash="0" * 64)
    )
    with op.batch_alter_table("owner_sessions") as batch_op:
        batch_op.alter_column("csrf_token_hash", existing_type=sa.String(length=64), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("owner_sessions") as batch_op:
        batch_op.drop_column("csrf_token_hash")
