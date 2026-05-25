from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_phase1"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    flow_intensity = postgresql.ENUM(
        "spotting", "light", "medium", "heavy", name="flowintensity", create_type=False
    )
    reminder_type = postgresql.ENUM(
        "period", "medication", "hydration", "mood_checkin", name="remindertype", create_type=False
    )

    flow_intensity.create(op.get_bind(), checkfirst=True)
    reminder_type.create(op.get_bind(), checkfirst=True)

    # ── users ──────────────────────────────────────────────────────────────
    op.add_column("users", sa.Column("first_name", sa.String(100), nullable=True))
    op.add_column("users", sa.Column("photo_url", sa.String(500), nullable=True))
    op.add_column("users", sa.Column("onboarding_completed", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("users", sa.Column("anonymized_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("is_2fa_enabled", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("users", sa.Column("totp_secret_encrypted", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("password_reset_token", sa.String(128), nullable=True))
    op.add_column("users", sa.Column("password_reset_expires", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("stripe_customer_id", sa.String(64), nullable=True))
    op.add_column("users", sa.Column("stripe_subscription_id", sa.String(64), nullable=True))

    op.create_index("ix_users_password_reset_token", "users", ["password_reset_token"], unique=False)
    op.create_index("ix_users_stripe_customer_id", "users", ["stripe_customer_id"], unique=False)

    # ── female_profiles ───────────────────────────────────────────────────
    op.add_column("female_profiles", sa.Column("allergies_encrypted", sa.Text(), nullable=True))
    op.add_column("female_profiles", sa.Column("health_conditions_encrypted", sa.Text(), nullable=True))
    op.add_column("female_profiles", sa.Column("cuisine_preference", sa.String(100), nullable=True))
    op.add_column(
        "female_profiles",
        sa.Column("period_reminder_days_before", sa.Integer(), nullable=False, server_default="2"),
    )
    op.add_column("female_profiles", sa.Column("last_period_reminder_sent", sa.Date(), nullable=True))

    # ── cycle_records ─────────────────────────────────────────────────────
    op.add_column("cycle_records", sa.Column("period_end", sa.Date(), nullable=True))
    op.add_column("cycle_records", sa.Column("flow_intensity", flow_intensity, nullable=True))
    op.create_check_constraint(
        "ck_cycle_records_period_end",
        "cycle_records",
        "period_end IS NULL OR period_end >= period_start",
    )

    # ── symptom_logs ──────────────────────────────────────────────────────
    op.add_column("symptom_logs", sa.Column("bloating", sa.Boolean(), nullable=True))
    op.add_column("symptom_logs", sa.Column("breast_tenderness", sa.Boolean(), nullable=True))
    op.add_column("symptom_logs", sa.Column("headache", sa.Boolean(), nullable=True))
    op.add_column("symptom_logs", sa.Column("acne", sa.Boolean(), nullable=True))
    op.add_column("symptom_logs", sa.Column("fatigue", sa.Boolean(), nullable=True))
    op.add_column("symptom_logs", sa.Column("sleep_quality", sa.Integer(), nullable=True))
    op.add_column("symptom_logs", sa.Column("libido", sa.Integer(), nullable=True))
    op.add_column("symptom_logs", sa.Column("intensity", sa.Integer(), nullable=True))
    op.create_check_constraint(
        "ck_symptom_logs_sleep_quality",
        "symptom_logs",
        "sleep_quality IS NULL OR (sleep_quality >= 1 AND sleep_quality <= 5)",
    )
    op.create_check_constraint(
        "ck_symptom_logs_libido",
        "symptom_logs",
        "libido IS NULL OR (libido >= 1 AND libido <= 5)",
    )
    op.create_check_constraint(
        "ck_symptom_logs_intensity",
        "symptom_logs",
        "intensity IS NULL OR (intensity >= 1 AND intensity <= 3)",
    )

    # ── reminder_configs ──────────────────────────────────────────────────
    op.create_table(
        "reminder_configs",
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("reminder_type", reminder_type, nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("time_of_day", sa.String(5), nullable=False, server_default="20:00"),
        sa.Column("label_encrypted", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reminder_configs_user_type", "reminder_configs", ["user_id", "reminder_type"])

    # ── stripe_invoices ───────────────────────────────────────────────────
    op.create_table(
        "stripe_invoices",
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("stripe_invoice_id", sa.String(64), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("invoice_pdf_url", sa.String(500), nullable=True),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stripe_invoice_id", name="uq_stripe_invoices_stripe_id"),
    )
    op.create_index("ix_stripe_invoices_user", "stripe_invoices", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_stripe_invoices_user", table_name="stripe_invoices")
    op.drop_table("stripe_invoices")

    op.drop_index("ix_reminder_configs_user_type", table_name="reminder_configs")
    op.drop_table("reminder_configs")

    op.drop_constraint("ck_symptom_logs_intensity", "symptom_logs", type_="check")
    op.drop_constraint("ck_symptom_logs_libido", "symptom_logs", type_="check")
    op.drop_constraint("ck_symptom_logs_sleep_quality", "symptom_logs", type_="check")
    for col in ["intensity", "libido", "sleep_quality", "fatigue", "acne", "headache", "breast_tenderness", "bloating"]:
        op.drop_column("symptom_logs", col)

    op.drop_constraint("ck_cycle_records_period_end", "cycle_records", type_="check")
    op.drop_column("cycle_records", "flow_intensity")
    op.drop_column("cycle_records", "period_end")

    for col in ["last_period_reminder_sent", "period_reminder_days_before", "cuisine_preference",
                "health_conditions_encrypted", "allergies_encrypted"]:
        op.drop_column("female_profiles", col)

    op.drop_index("ix_users_stripe_customer_id", table_name="users")
    op.drop_index("ix_users_password_reset_token", table_name="users")
    for col in ["stripe_subscription_id", "stripe_customer_id", "password_reset_expires",
                "password_reset_token", "totp_secret_encrypted", "is_2fa_enabled",
                "anonymized_at", "onboarding_completed", "photo_url", "first_name"]:
        op.drop_column("users", col)

    op.execute("DROP TYPE IF EXISTS remindertype")
    op.execute("DROP TYPE IF EXISTS flowintensity")
