from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.intimate_health_log import IntimateHealthLog
from app.models.libido_log import LibidoLog


class LibidoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert(
        self,
        user_id: UUID,
        log_date: date,
        score: int,
        notes_encrypted: str | None = None,
    ) -> LibidoLog:
        result = await self.session.execute(
            select(LibidoLog).where(LibidoLog.user_id == user_id, LibidoLog.log_date == log_date)
        )
        entity = result.scalar_one_or_none()
        if entity is None:
            entity = LibidoLog(user_id=user_id, log_date=log_date, score=score, notes_encrypted=notes_encrypted)
            self.session.add(entity)
        else:
            entity.score = score
            entity.notes_encrypted = notes_encrypted
        return entity

    async def list_by_user(self, user_id: UUID, limit: int = 30) -> list[LibidoLog]:
        result = await self.session.execute(
            select(LibidoLog)
            .where(LibidoLog.user_id == user_id)
            .order_by(LibidoLog.log_date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class IntimateHealthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert(
        self,
        user_id: UUID,
        log_date: date,
        **kwargs,
    ) -> IntimateHealthLog:
        result = await self.session.execute(
            select(IntimateHealthLog).where(
                IntimateHealthLog.user_id == user_id, IntimateHealthLog.log_date == log_date
            )
        )
        entity = result.scalar_one_or_none()
        if entity is None:
            entity = IntimateHealthLog(user_id=user_id, log_date=log_date, **kwargs)
            self.session.add(entity)
        else:
            for key, value in kwargs.items():
                setattr(entity, key, value)
        return entity

    async def list_by_user(self, user_id: UUID, limit: int = 30) -> list[IntimateHealthLog]:
        result = await self.session.execute(
            select(IntimateHealthLog)
            .where(IntimateHealthLog.user_id == user_id)
            .order_by(IntimateHealthLog.log_date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
