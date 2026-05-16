from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.challenge import Challenge, UserChallenge


class ChallengeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_active(self, category: str | None = None, limit: int = 20) -> list[Challenge]:
        q = select(Challenge).where(Challenge.is_active == True)  # noqa: E712
        if category:
            q = q.where(Challenge.category == category)
        q = q.order_by(Challenge.created_at.desc()).limit(limit)
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def get_by_id(self, challenge_id: UUID) -> Challenge | None:
        result = await self.session.execute(select(Challenge).where(Challenge.id == challenge_id))
        return result.scalar_one_or_none()

    async def increment_participants(self, challenge_id: UUID) -> None:
        challenge = await self.get_by_id(challenge_id)
        if challenge:
            challenge.participants_count += 1

    async def seed_default_challenges(self) -> list[Challenge]:
        import uuid
        defaults = [
            Challenge(id=uuid.uuid4(), title="7 jours de journaling", description="Écris dans ton journal émotionnel 7 jours de suite", category="mental_health", duration_days=7, badge_icon="📓", is_active=True),
            Challenge(id=uuid.uuid4(), title="Hydratation parfaite", description="Bois 8 verres d'eau par jour pendant 14 jours", category="nutrition", duration_days=14, badge_icon="💧", is_active=True),
            Challenge(id=uuid.uuid4(), title="Cycle sans sucre", description="Évite le sucre raffiné pendant toute la phase lutéale", category="nutrition", duration_days=14, badge_icon="🌿", is_active=True),
            Challenge(id=uuid.uuid4(), title="Méditation quotidienne", description="5 minutes de cohérence cardiaque chaque matin pendant 21 jours", category="mental_health", duration_days=21, badge_icon="🧘", is_active=True),
            Challenge(id=uuid.uuid4(), title="Suivre mon cycle", description="Enregistre tes symptômes chaque jour pendant 30 jours", category="cycle", duration_days=30, badge_icon="🌸", is_active=True),
        ]
        for c in defaults:
            self.session.add(c)
        return defaults


class UserChallengeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def enroll(self, user_id: UUID, challenge_id: UUID) -> UserChallenge:
        existing = await self.get_enrollment(user_id, challenge_id)
        if existing:
            return existing
        uc = UserChallenge(
            user_id=user_id,
            challenge_id=challenge_id,
            enrolled_at=datetime.now(timezone.utc),
        )
        self.session.add(uc)
        return uc

    async def get_enrollment(self, user_id: UUID, challenge_id: UUID) -> UserChallenge | None:
        result = await self.session.execute(
            select(UserChallenge).where(
                UserChallenge.user_id == user_id, UserChallenge.challenge_id == challenge_id
            )
        )
        return result.scalar_one_or_none()

    async def list_user_challenges(self, user_id: UUID) -> list[UserChallenge]:
        result = await self.session.execute(
            select(UserChallenge)
            .where(UserChallenge.user_id == user_id)
            .order_by(UserChallenge.enrolled_at.desc())
        )
        return list(result.scalars().all())

    async def update_progress(self, user_id: UUID, challenge_id: UUID, progress_days: int) -> UserChallenge | None:
        uc = await self.get_enrollment(user_id, challenge_id)
        if uc:
            uc.progress_days = progress_days
            if progress_days >= (await self._get_duration(challenge_id)):
                uc.is_completed = True
                uc.completed_at = datetime.now(timezone.utc)
        return uc

    async def _get_duration(self, challenge_id: UUID) -> int:
        result = await self.session.execute(select(Challenge.duration_days).where(Challenge.id == challenge_id))
        return result.scalar_one_or_none() or 0
