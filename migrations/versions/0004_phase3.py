"""Phase 3 — Santé Mentale, Bien-être Intime, Communauté, Consultations, Chat, Dashboard"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_phase3"
down_revision: Union[str, None] = "0003_phase2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── New enums ──────────────────────────────────────────────────────────
    journal_prompt_type = postgresql.ENUM(
        "free", "gratitude", "challenge", "reflection", "ai_generated",
        name="journalprompttype",
        create_type=False,
    )
    mental_alert_type = postgresql.ENUM("distress", "spm", "tdpm", name="mentalalerttype", create_type=False)
    discharge_type = postgresql.ENUM(
        "none", "normal_clear", "normal_white",
        "abnormal_yellow", "abnormal_green", "abnormal_gray", "other",
        name="dischargetype",
        create_type=False,
    )
    post_category = postgresql.ENUM(
        "cycle", "fertility", "pregnancy", "hormonal_health", "menopause",
        "nutrition", "mental_health", "intimate_health", "general",
        name="postcategory",
        create_type=False,
    )
    consultation_status = postgresql.ENUM(
        "pending", "confirmed", "completed", "cancelled",
        name="consultationstatus",
        create_type=False,
    )
    chat_role = postgresql.ENUM("user", "assistant", name="chatrole", create_type=False)

    for enum in (journal_prompt_type, mental_alert_type, discharge_type, post_category, consultation_status, chat_role):
        enum.create(op.get_bind(), checkfirst=True)

    # ── users — beta_access ──────────────────────────────────────────────
    op.add_column("users", sa.Column("beta_access", sa.Boolean(), nullable=False, server_default="false"))

    # ── emotional_journal_entries ─────────────────────────────────────────
    op.create_table(
        "emotional_journal_entries",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("log_date", sa.Date(), nullable=False),
        sa.Column("prompt_type", journal_prompt_type, nullable=False, server_default="free"),
        sa.Column("prompt_text_encrypted", sa.Text(), nullable=True),
        sa.Column("text_encrypted", sa.Text(), nullable=True),
        sa.Column("mood_score_at_entry", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "mood_score_at_entry IS NULL OR (mood_score_at_entry >= 1 AND mood_score_at_entry <= 5)",
            name="ck_emotional_journal_mood_score",
        ),
    )
    op.create_index("ix_emotional_journal_user_date", "emotional_journal_entries", ["user_id", "log_date"])

    # ── mental_alerts ─────────────────────────────────────────────────────
    op.create_table(
        "mental_alerts",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("alert_type", mental_alert_type, nullable=False),
        sa.Column("is_resolved", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resources_sent", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mental_alerts_user", "mental_alerts", ["user_id", "created_at"])

    # ── libido_logs ───────────────────────────────────────────────────────
    op.create_table(
        "libido_logs",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("log_date", sa.Date(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("notes_encrypted", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "log_date", name="uq_libido_logs_user_date"),
        sa.CheckConstraint("score >= 1 AND score <= 5", name="ck_libido_logs_score"),
    )
    op.create_index("ix_libido_logs_user_date", "libido_logs", ["user_id", "log_date"])

    # ── intimate_health_logs ──────────────────────────────────────────────
    op.create_table(
        "intimate_health_logs",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("log_date", sa.Date(), nullable=False),
        sa.Column("vaginal_dryness_severity", sa.Integer(), nullable=True),
        sa.Column("discharge_type", discharge_type, nullable=True),
        sa.Column("pain_during_intercourse", sa.Boolean(), nullable=True),
        sa.Column("pain_intensity", sa.Integer(), nullable=True),
        sa.Column("itching", sa.Boolean(), nullable=True),
        sa.Column("notes_encrypted", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "log_date", name="uq_intimate_health_logs_user_date"),
        sa.CheckConstraint(
            "vaginal_dryness_severity IS NULL OR (vaginal_dryness_severity >= 1 AND vaginal_dryness_severity <= 5)",
            name="ck_intimate_health_dryness",
        ),
        sa.CheckConstraint(
            "pain_intensity IS NULL OR (pain_intensity >= 1 AND pain_intensity <= 10)",
            name="ck_intimate_health_pain",
        ),
    )
    op.create_index("ix_intimate_health_logs_user_date", "intimate_health_logs", ["user_id", "log_date"])

    # ── community_posts ───────────────────────────────────────────────────
    op.create_table(
        "community_posts",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("title_encrypted", sa.Text(), nullable=False),
        sa.Column("body_encrypted", sa.Text(), nullable=False),
        sa.Column("category", post_category, nullable=False),
        sa.Column("is_moderated", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_approved", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("likes_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("comments_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("anonymous_display_name", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_community_posts_category", "community_posts", ["category", "created_at"])

    # ── community_recipes ─────────────────────────────────────────────────
    op.create_table(
        "community_recipes",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description_encrypted", sa.Text(), nullable=True),
        sa.Column("ingredients_encrypted", sa.Text(), nullable=True),
        sa.Column("instructions_encrypted", sa.Text(), nullable=True),
        sa.Column("phase", sa.String(20), nullable=True),
        sa.Column("cultural_cuisine", sa.String(100), nullable=True),
        sa.Column("prep_time_minutes", sa.Integer(), nullable=True),
        sa.Column("nutrition_score", sa.Integer(), nullable=True),
        sa.Column("likes_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_approved", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "nutrition_score IS NULL OR (nutrition_score >= 1 AND nutrition_score <= 10)",
            name="ck_community_recipes_score",
        ),
    )
    op.create_index("ix_community_recipes_phase", "community_recipes", ["phase", "created_at"])

    # ── challenges ────────────────────────────────────────────────────────
    op.create_table(
        "challenges",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(50), nullable=False, server_default="general"),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("badge_icon", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("participants_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── user_challenges ───────────────────────────────────────────────────
    op.create_table(
        "user_challenges",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("challenge_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("enrolled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("progress_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_completed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["challenge_id"], ["challenges.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "challenge_id", name="uq_user_challenges"),
        sa.CheckConstraint("progress_days >= 0", name="ck_user_challenges_progress"),
    )
    op.create_index("ix_user_challenges_user", "user_challenges", ["user_id"])

    # ── consultation_bookings ─────────────────────────────────────────────
    op.create_table(
        "consultation_bookings",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", consultation_status, nullable=False, server_default="pending"),
        sa.Column("video_url_encrypted", sa.Text(), nullable=True),
        sa.Column("preparation_notes_encrypted", sa.Text(), nullable=True),
        sa.Column("summary_encrypted", sa.Text(), nullable=True),
        sa.Column("practitioner_name", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_consultation_bookings_user", "consultation_bookings", ["user_id", "scheduled_at"])

    # ── chat_messages ─────────────────────────────────────────────────────
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("session_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("role", chat_role, nullable=False),
        sa.Column("content_encrypted", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_chat_messages_user_session", "chat_messages", ["user_id", "session_id", "created_at"])


def downgrade() -> None:
    for table in (
        "chat_messages", "consultation_bookings", "user_challenges", "challenges",
        "community_recipes", "community_posts", "intimate_health_logs",
        "libido_logs", "mental_alerts", "emotional_journal_entries",
    ):
        try:
            op.drop_table(table)
        except Exception:
            pass

    op.drop_column("users", "beta_access")

    for t in ("chatrole", "consultationstatus", "postcategory", "dischargetype", "mentalalerttype", "journalprompttype"):
        op.execute(f"DROP TYPE IF EXISTS {t}")
