from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=User)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_active(self, user_id: UUID) -> User | None:
        result = await self.session.execute(
            select(User).where(User.id == user_id, User.is_active.is_(True), User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()
