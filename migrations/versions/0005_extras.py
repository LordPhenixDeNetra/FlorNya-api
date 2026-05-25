"""Extras — plan essential, device_tokens, pregnancy appointment reminders task"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_extras"
down_revision: Union[str, None] = "0004_phase3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Add 'essential' to userplan enum (PostgreSQL) ──────────────────────
    # In SQLite (tests) enums are stored as VARCHAR so no ALTER needed.
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE userplan ADD VALUE IF NOT EXISTS 'essential' AFTER 'free'")

    # ── device_tokens ─────────────────────────────────────────────────────
    device_platform = postgresql.ENUM("ios", "android", "web", name="deviceplatform", create_type=False)
    device_platform.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "device_tokens",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("token", sa.String(512), nullable=False),
        sa.Column("platform", device_platform, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "token", name="uq_device_tokens_user_token"),
    )
    op.create_index("ix_device_tokens_user", "device_tokens", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_device_tokens_user", table_name="device_tokens")
    op.drop_table("device_tokens")
    op.execute("DROP TYPE IF EXISTS deviceplatform")
    # Note: removing enum values from PostgreSQL requires a full recreation
    # which is destructive — left as a manual operation.
