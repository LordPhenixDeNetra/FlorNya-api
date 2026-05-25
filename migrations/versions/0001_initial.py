from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    user_plan = postgresql.ENUM("free", "bloom", "bloom_pro", name="userplan", create_type=False)
    reproductive_stage = postgresql.ENUM(
        "menstruating",
        "trying_to_conceive",
        "pregnant",
        "postpartum",
        "perimenopause",
        "menopause",
        name="reproductivestage",
        create_type=False,
    )

    user_plan.create(op.get_bind(), checkfirst=True)
    reproductive_stage.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("language", sa.String(length=8), nullable=False),
        sa.Column("plan", user_plan, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("token_version", sa.Integer(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_active"), "users", ["is_active", "deleted_at"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "female_profiles",
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("reproductive_stage", reproductive_stage, nullable=False),
        sa.Column("cycle_length", sa.Integer(), nullable=False),
        sa.Column("period_length", sa.Integer(), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_female_profiles_user_id"),
    )

    op.create_table(
        "cycle_records",
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("cycle_length", sa.Integer(), nullable=False),
        sa.Column("notes_encrypted", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.CheckConstraint("cycle_length >= 15 AND cycle_length <= 60", name="ck_cycle_records_cycle_length"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cycle_records_user_date", "cycle_records", ["user_id", "period_start"], unique=False)

    op.create_table(
        "symptom_logs",
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("log_date", sa.Date(), nullable=False),
        sa.Column("cramps", sa.Boolean(), nullable=True),
        sa.Column("energy", sa.Integer(), nullable=True),
        sa.Column("notes_encrypted", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.CheckConstraint(
            "energy IS NULL OR (energy >= 1 AND energy <= 5)", name="ck_symptom_logs_energy"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_symptom_logs_user_date", "symptom_logs", ["user_id", "log_date"], unique=False)

    op.create_table(
        "mood_logs",
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("log_date", sa.Date(), nullable=False),
        sa.Column("mood_score", sa.Integer(), nullable=False),
        sa.Column("journal_text_encrypted", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.CheckConstraint("mood_score >= 1 AND mood_score <= 5", name="ck_mood_logs_mood_score"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mood_logs_user_date", "mood_logs", ["user_id", "log_date"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_mood_logs_user_date", table_name="mood_logs")
    op.drop_table("mood_logs")
    op.drop_index("ix_symptom_logs_user_date", table_name="symptom_logs")
    op.drop_table("symptom_logs")
    op.drop_index("ix_cycle_records_user_date", table_name="cycle_records")
    op.drop_table("cycle_records")
    op.drop_table("female_profiles")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_active"), table_name="users")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS reproductivestage")
    op.execute("DROP TYPE IF EXISTS userplan")
