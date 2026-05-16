from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import BaseModel

TModel = TypeVar("TModel", bound=BaseModel)


class BaseRepository(Generic[TModel]):
    def __init__(self, session: AsyncSession, model: type[TModel]):
        self.session = session
        self.model = model

    async def get(self, entity_id: UUID) -> TModel | None:
        result = await self.session.execute(select(self.model).where(self.model.id == entity_id))
        return result.scalar_one_or_none()

    async def add(self, entity: TModel) -> TModel:
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def count(self, stmt: Select) -> int:
        count_stmt = select(func.count()).select_from(stmt.subquery())
        result = await self.session.execute(count_stmt)
        return int(result.scalar_one())
