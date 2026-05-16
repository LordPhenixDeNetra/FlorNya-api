"""Phase 2 — Fertilité, Grossesse, Santé Hormonale, Ménopause, Nutrition"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_phase2"
down_revision: Union[str, None] = "0002_phase1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    cervical_mucus = sa.Enum("dry", "creamy", "watery", "egg_white", name="cervicalmucustype")
    lh_test_result = sa.Enum("negative", "positive", "peak", name="lhtestresult")
    pregnancy_status = sa.Enum("active", "postpartum", "ended", name="pregnancystatus")
    appointment_type = sa.Enum("prenatal_visit", "ultrasound", "blood_test", "other", name="appointmenttype")
    breast_side = sa.Enum("left", "right", "both", name="breastside")
    treatment_type = sa.Enum("pill", "patch", "iud", "implant", "injection", "ring", "other", name="treatmenttype")

    for enum in (cervical_mucus, lh_test_result, pregnancy_status, appointment_type, breast_side, treatment_type):
        enum.create(op.get_bind(), checkfirst=True)

    # ── fertility_logs ────────────────────────────────────────────────────
    op.create_table(
        "fertility_logs",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("log_date", sa.Date(), nullable=False),
        sa.Column("bbt_celsius", sa.Numeric(4, 2), nullable=True),
        sa.Column("cervical_mucus", cervical_mucus, nullable=True),
        sa.Column("lh_test_result", lh_test_result, nullable=True),
        sa.Column("notes_encrypted", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "bbt_celsius IS NULL OR (bbt_celsius >= 35.0 AND bbt_celsius <= 40.0)",
            name="ck_fertility_logs_bbt",
        ),
    )
    op.create_index("ix_fertility_logs_user_date", "fertility_logs", ["user_id", "log_date"], unique=True)

    # ── conception_attempts ───────────────────────────────────────────────
    op.create_table(
        "conception_attempts",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("attempt_date", sa.Date(), nullable=False),
        sa.Column("notes_encrypted", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_conception_attempts_user_date", "conception_attempts", ["user_id", "attempt_date"])

    # ── pregnancy_profiles ────────────────────────────────────────────────
    op.create_table(
        "pregnancy_profiles",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("status", pregnancy_status, nullable=False, server_default="active"),
        sa.Column("lmp_date", sa.Date(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("delivery_date", sa.Date(), nullable=True),
        sa.Column("is_breastfeeding", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("weeks_at_activation", sa.Integer(), nullable=True),
        sa.Column("notes_encrypted", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_pregnancy_profiles_user"),
    )

    # ── pregnancy_symptom_logs ────────────────────────────────────────────
    op.create_table(
        "pregnancy_symptom_logs",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("log_date", sa.Date(), nullable=False),
        sa.Column("nausea", sa.Boolean(), nullable=True),
        sa.Column("vomiting", sa.Boolean(), nullable=True),
        sa.Column("fatigue", sa.Boolean(), nullable=True),
        sa.Column("back_pain", sa.Boolean(), nullable=True),
        sa.Column("swelling", sa.Boolean(), nullable=True),
        sa.Column("heartburn", sa.Boolean(), nullable=True),
        sa.Column("headache", sa.Boolean(), nullable=True),
        sa.Column("fetal_movement_count", sa.Integer(), nullable=True),
        sa.Column("severity", sa.Integer(), nullable=True),
        sa.Column("is_alarm_symptom", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("notes_encrypted", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "fetal_movement_count IS NULL OR fetal_movement_count >= 0",
            name="ck_preg_sym_fetal_movement",
        ),
        sa.CheckConstraint(
            "severity IS NULL OR (severity >= 1 AND severity <= 5)",
            name="ck_preg_sym_severity",
        ),
    )
    op.create_index("ix_pregnancy_symptom_logs_user_date", "pregnancy_symptom_logs", ["user_id", "log_date"])

    # ── pregnancy_appointments ────────────────────────────────────────────
    op.create_table(
        "pregnancy_appointments",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("appointment_date", sa.Date(), nullable=False),
        sa.Column("appointment_type", appointment_type, nullable=False, server_default="prenatal_visit"),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("location", sa.String(300), nullable=True),
        sa.Column("reminder_sent_7d", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("reminder_sent_1d", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("notes_encrypted", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_preg_appointments_user_date", "pregnancy_appointments", ["user_id", "appointment_date"])

    # ── breastfeeding_sessions ────────────────────────────────────────────
    op.create_table(
        "breastfeeding_sessions",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("session_date", sa.Date(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("breast_side", breast_side, nullable=True),
        sa.Column("quantity_ml", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "duration_minutes IS NULL OR duration_minutes > 0",
            name="ck_breastfeeding_duration",
        ),
    )
    op.create_index("ix_breastfeeding_sessions_user_date", "breastfeeding_sessions", ["user_id", "session_date"])

    # ── epds_assessments ──────────────────────────────────────────────────
    op.create_table(
        "epds_assessments",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("assessment_date", sa.Date(), nullable=False),
        sa.Column("total_score", sa.Integer(), nullable=False),
        sa.Column("answers_encrypted", sa.Text(), nullable=True),
        sa.Column("alert_sent", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "total_score >= 0 AND total_score <= 30",
            name="ck_epds_score_range",
        ),
    )
    op.create_index("ix_epds_assessments_user_date", "epds_assessments", ["user_id", "assessment_date"])

    # ── pain_logs ─────────────────────────────────────────────────────────
    op.create_table(
        "pain_logs",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("log_date", sa.Date(), nullable=False),
        sa.Column("pain_intensity", sa.Integer(), nullable=True),
        sa.Column("pelvic", sa.Boolean(), nullable=True),
        sa.Column("lower_back", sa.Boolean(), nullable=True),
        sa.Column("dysmenorrhea", sa.Boolean(), nullable=True),
        sa.Column("dyspareunia", sa.Boolean(), nullable=True),
        sa.Column("bloating", sa.Boolean(), nullable=True),
        sa.Column("body_zones", sa.Text(), nullable=True),
        sa.Column("notes_encrypted", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "pain_intensity IS NULL OR (pain_intensity >= 1 AND pain_intensity <= 10)",
            name="ck_pain_logs_intensity",
        ),
    )
    op.create_index("ix_pain_logs_user_date", "pain_logs", ["user_id", "log_date"])

    # ── hormonal_treatments ───────────────────────────────────────────────
    op.create_table(
        "hormonal_treatments",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("treatment_type", treatment_type, nullable=False),
        sa.Column("brand_name", sa.String(200), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("reminder_time", sa.String(5), nullable=True),
        sa.Column("side_effects_encrypted", sa.Text(), nullable=True),
        sa.Column("notes_encrypted", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_hormonal_treatments_user", "hormonal_treatments", ["user_id"])

    # ── menopause_logs ────────────────────────────────────────────────────
    op.create_table(
        "menopause_logs",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("log_date", sa.Date(), nullable=False),
        sa.Column("hot_flash_count", sa.Integer(), nullable=True),
        sa.Column("night_sweats", sa.Boolean(), nullable=True),
        sa.Column("vaginal_dryness", sa.Boolean(), nullable=True),
        sa.Column("insomnia", sa.Boolean(), nullable=True),
        sa.Column("mood_swings", sa.Boolean(), nullable=True),
        sa.Column("weight_gain", sa.Boolean(), nullable=True),
        sa.Column("brain_fog", sa.Boolean(), nullable=True),
        sa.Column("joint_pain", sa.Boolean(), nullable=True),
        sa.Column("severity", sa.Integer(), nullable=True),
        sa.Column("notes_encrypted", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "severity IS NULL OR (severity >= 1 AND severity <= 5)",
            name="ck_menopause_logs_severity",
        ),
    )
    op.create_index("ix_menopause_logs_user_date", "menopause_logs", ["user_id", "log_date"])

    # ── nutrition_logs ────────────────────────────────────────────────────
    op.create_table(
        "nutrition_logs",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("log_date", sa.Date(), nullable=False),
        sa.Column("meals_encrypted", sa.Text(), nullable=True),
        sa.Column("hormonal_impact_score", sa.Integer(), nullable=True),
        sa.Column("ai_analysis_encrypted", sa.Text(), nullable=True),
        sa.Column("water_glasses", sa.Integer(), nullable=True),
        sa.Column("notes_encrypted", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "hormonal_impact_score IS NULL OR (hormonal_impact_score >= 1 AND hormonal_impact_score <= 10)",
            name="ck_nutrition_logs_impact",
        ),
    )
    op.create_index("ix_nutrition_logs_user_date", "nutrition_logs", ["user_id", "log_date"])


def downgrade() -> None:
    for table in (
        "nutrition_logs", "menopause_logs", "hormonal_treatments", "pain_logs",
        "epds_assessments", "breastfeeding_sessions", "pregnancy_appointments",
        "pregnancy_symptom_logs", "pregnancy_profiles", "conception_attempts", "fertility_logs",
    ):
        for idx in [f"ix_{table.replace('_logs', '').replace('_sessions', '').replace('_profiles', '').replace('_appointments', '').replace('_treatments', '').replace('_assessments', '').replace('_attempts', '')}_user_date",
                    f"ix_{table}_user_date", f"ix_{table}_user"]:
            try:
                op.drop_index(idx, table_name=table)
            except Exception:
                pass
        op.drop_table(table)

    for t in ("treatmenttype", "breastside", "appointmenttype", "pregnancystatus", "lhtestresult", "cervicalmucustype"):
        op.execute(f"DROP TYPE IF EXISTS {t}")
