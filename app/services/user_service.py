import csv
import io
import json
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_sensitive, encrypt_sensitive
from app.models.female_profile import FemaleProfile, ReproductiveStage
from app.models.user import User
from app.repositories.cycle_repository import CycleRepository
from app.repositories.female_profile_repository import FemaleProfileRepository
from app.repositories.mood_repository import MoodRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import (
    ExtendedProfileUpdate,
    FemaleProfilePublic,
    FemaleProfileUpsert,
    OnboardingRequest,
    ReproductiveStage as StageSchema,
    UserPlan as PlanSchema,
    UserPublic,
    UserUpdate,
)


class UserService:
    def __init__(
        self,
        session: AsyncSession,
        users: UserRepository,
        profiles: FemaleProfileRepository,
        cycles: CycleRepository | None = None,
        moods: MoodRepository | None = None,
    ):
        self.session = session
        self.users = users
        self.profiles = profiles
        self.cycles = cycles
        self.moods = moods

    # ── Read ──────────────────────────────────────────────────────────────

    async def get_me(self, user: User) -> UserPublic:
        return UserPublic(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            photo_url=user.photo_url,
            date_of_birth=user.date_of_birth,
            language=user.language,
            plan=PlanSchema(user.plan.value),
            is_2fa_enabled=user.is_2fa_enabled,
            onboarding_completed=user.onboarding_completed,
            created_at=user.created_at,
        )

    # ── Update ────────────────────────────────────────────────────────────

    async def update_me(self, user: User, data: UserUpdate) -> UserPublic:
        if data.language is not None:
            user.language = data.language
        if data.first_name is not None:
            user.first_name = data.first_name
        await self.session.commit()
        await self.session.refresh(user)
        return await self.get_me(user)

    async def update_extended_profile(self, user: User, data: ExtendedProfileUpdate) -> UserPublic:
        if data.first_name is not None:
            user.first_name = data.first_name
        if data.photo_url is not None:
            user.photo_url = data.photo_url
        if data.language is not None:
            user.language = data.language

        profile = await self.profiles.get_by_user_id(user.id)
        if profile is not None:
            if data.allergies is not None:
                profile.allergies_encrypted = encrypt_sensitive(json.dumps(data.allergies))
            if data.health_conditions is not None:
                profile.health_conditions_encrypted = encrypt_sensitive(
                    json.dumps([c.value for c in data.health_conditions])
                )

        await self.session.commit()
        await self.session.refresh(user)
        return await self.get_me(user)

    # ── Onboarding ────────────────────────────────────────────────────────

    async def complete_onboarding(self, user: User, data: OnboardingRequest) -> UserPublic:
        if data.first_name is not None:
            user.first_name = data.first_name
        user.onboarding_completed = True

        stage = ReproductiveStage(data.reproductive_stage.value)
        existing = await self.profiles.get_by_user_id(user.id)

        health_enc = encrypt_sensitive(json.dumps([c.value for c in data.health_conditions]))
        cuisine = data.cuisine_preference

        if existing is None:
            profile = FemaleProfile(
                user_id=user.id,
                reproductive_stage=stage,
                cycle_length=data.cycle_length,
                period_length=data.period_length,
                timezone=data.timezone,
                health_conditions_encrypted=health_enc,
                cuisine_preference=cuisine,
            )
            await self.profiles.add(profile)
        else:
            existing.reproductive_stage = stage
            existing.cycle_length = data.cycle_length
            existing.period_length = data.period_length
            existing.timezone = data.timezone
            existing.health_conditions_encrypted = health_enc
            existing.cuisine_preference = cuisine

        await self.session.commit()
        await self.session.refresh(user)
        return await self.get_me(user)

    # ── Female profile ────────────────────────────────────────────────────

    async def upsert_female_profile(self, user: User, data: FemaleProfileUpsert) -> FemaleProfilePublic:
        existing = await self.profiles.get_by_user_id(user.id)
        stage = ReproductiveStage(data.reproductive_stage.value)
        if existing is None:
            entity = FemaleProfile(
                user_id=user.id,
                reproductive_stage=stage,
                cycle_length=data.cycle_length,
                period_length=data.period_length,
                timezone=data.timezone,
            )
            await self.profiles.add(entity)
            await self.session.commit()
            await self.session.refresh(entity)
        else:
            existing.reproductive_stage = stage
            existing.cycle_length = data.cycle_length
            existing.period_length = data.period_length
            existing.timezone = data.timezone
            await self.session.commit()
            entity = existing

        return FemaleProfilePublic(
            id=entity.id,
            user_id=entity.user_id,
            reproductive_stage=StageSchema(entity.reproductive_stage.value),
            cycle_length=entity.cycle_length,
            period_length=entity.period_length,
            timezone=entity.timezone,
            created_at=entity.created_at,
        )

    async def get_female_profile(self, user: User) -> FemaleProfilePublic | None:
        entity = await self.profiles.get_by_user_id(user.id)
        if entity is None:
            return None
        return FemaleProfilePublic(
            id=entity.id,
            user_id=entity.user_id,
            reproductive_stage=StageSchema(entity.reproductive_stage.value),
            cycle_length=entity.cycle_length,
            period_length=entity.period_length,
            timezone=entity.timezone,
            created_at=entity.created_at,
        )

    # ── RGPD export ───────────────────────────────────────────────────────

    async def export_data(self, user: User, format: str = "json") -> bytes:
        profile = await self.profiles.get_by_user_id(user.id)

        allergies: list[str] = []
        health_conditions: list[str] = []
        if profile is not None:
            if profile.allergies_encrypted:
                raw = decrypt_sensitive(profile.allergies_encrypted)
                allergies = json.loads(raw) if raw else []
            if profile.health_conditions_encrypted:
                raw = decrypt_sensitive(profile.health_conditions_encrypted)
                health_conditions = json.loads(raw) if raw else []

        cycle_records = []
        if self.cycles:
            items, _ = await self.cycles.list(
                user_id=user.id, date_from=None, date_to=None,
                skip=0, limit=1000, sort_by="period_start", order="desc"
            )
            for r in items:
                cycle_records.append({
                    "period_start": str(r.period_start),
                    "period_end": str(r.period_end) if r.period_end else None,
                    "cycle_length": r.cycle_length,
                    "flow_intensity": r.flow_intensity.value if r.flow_intensity else None,
                    "notes": decrypt_sensitive(r.notes_encrypted),
                })

        mood_logs = []
        if self.moods:
            items_m, _, _ = await self.moods.list_cursor(
                user_id=user.id, date_from=None, min_score=None, cursor=None, limit=1000
            )
            for m in items_m:
                mood_logs.append({
                    "log_date": str(m.log_date),
                    "mood_score": m.mood_score,
                    "journal_text": decrypt_sensitive(m.journal_text_encrypted),
                })

        data = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "user": {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "date_of_birth": str(user.date_of_birth),
                "language": user.language,
                "plan": user.plan.value,
                "created_at": user.created_at.isoformat(),
            },
            "female_profile": {
                "reproductive_stage": profile.reproductive_stage.value if profile else None,
                "cycle_length": profile.cycle_length if profile else None,
                "period_length": profile.period_length if profile else None,
                "timezone": profile.timezone if profile else None,
                "allergies": allergies,
                "health_conditions": health_conditions,
                "cuisine_preference": profile.cuisine_preference if profile else None,
            },
            "cycle_records": cycle_records,
            "mood_logs": mood_logs,
        }

        if format == "json":
            return json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")

        # CSV: zip-like flat output (single CSV for simplicity)
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["type", "field", "value"])
        for k, v in data["user"].items():
            writer.writerow(["user", k, v])
        for r in cycle_records:
            for k, v in r.items():
                writer.writerow(["cycle_record", k, v])
        return buf.getvalue().encode("utf-8")

    # ── Avatar upload ─────────────────────────────────────────────────────

    async def upload_avatar(self, user: User, content: bytes, content_type: str) -> UserPublic:
        from app.config import get_settings

        settings = get_settings()

        if settings.S3_BUCKET_NAME and settings.AWS_ACCESS_KEY_ID:
            import aiobotocore.session as aio_session

            key = f"avatars/{user.id}.jpg"
            session = aio_session.get_session()
            async with session.create_client(
                "s3",
                region_name=settings.S3_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            ) as client:
                await client.put_object(
                    Bucket=settings.S3_BUCKET_NAME,
                    Key=key,
                    Body=content,
                    ContentType=content_type,
                )
                url = f"https://{settings.S3_BUCKET_NAME}.s3.{settings.S3_REGION}.amazonaws.com/{key}"
        else:
            import base64

            b64 = base64.b64encode(content).decode()
            url = f"data:{content_type};base64,{b64[:200]}…"

        user.photo_url = url
        await self.session.commit()
        await self.session.refresh(user)
        return await self.get_me(user)

    # ── Beta access ───────────────────────────────────────────────────────

    async def activate_beta(self, user: User) -> UserPublic:
        user.beta_access = True
        await self.session.commit()
        await self.session.refresh(user)
        return await self.get_me(user)

    # ── Account deletion ──────────────────────────────────────────────────

    async def delete_account(self, user: User) -> None:
        user.is_active = False
        user.deleted_at = datetime.now(timezone.utc)
        user.email = f"deleted_{user.id}@deleted.invalid"
        user.token_version += 1
        await self.session.commit()
