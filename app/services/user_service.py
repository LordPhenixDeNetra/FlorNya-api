from sqlalchemy.ext.asyncio import AsyncSession

from app.models.female_profile import FemaleProfile, ReproductiveStage
from app.models.user import User
from app.repositories.female_profile_repository import FemaleProfileRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import FemaleProfilePublic, FemaleProfileUpsert, ReproductiveStage as StageSchema
from app.schemas.user import UserPlan as PlanSchema
from app.schemas.user import UserPublic, UserUpdate


class UserService:
    def __init__(
        self,
        session: AsyncSession,
        users: UserRepository,
        profiles: FemaleProfileRepository,
    ):
        self.session = session
        self.users = users
        self.profiles = profiles

    async def get_me(self, user: User) -> UserPublic:
        return UserPublic(
            id=user.id,
            email=user.email,
            date_of_birth=user.date_of_birth,
            language=user.language,
            plan=PlanSchema(user.plan.value),
            created_at=user.created_at,
        )

    async def update_me(self, user: User, data: UserUpdate) -> UserPublic:
        if data.language is not None:
            user.language = data.language
        await self.session.commit()
        await self.session.refresh(user)
        return await self.get_me(user)

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
