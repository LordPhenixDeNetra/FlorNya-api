from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.female_profile import FemaleProfile
from app.repositories.base import BaseRepository


class FemaleProfileRepository(BaseRepository[FemaleProfile]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=FemaleProfile)

    async def get_by_user_id(self, user_id) -> FemaleProfile | None:
        result = await self.session.execute(select(FemaleProfile).where(FemaleProfile.user_id == user_id))
        return result.scalar_one_or_none()
