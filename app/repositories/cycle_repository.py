from datetime import date
from uuid import UUID

from sqlalchemy import Select, asc, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cycle_record import CycleRecord, FlowIntensity
from app.repositories.base import BaseRepository


class CycleRepository(BaseRepository[CycleRecord]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=CycleRecord)

    async def create(
        self,
        *,
        user_id: UUID,
        period_start: date,
        period_end: date | None = None,
        cycle_length: int,
        flow_intensity: FlowIntensity | None = None,
        notes_encrypted: str | None,
    ) -> CycleRecord:
        entity = CycleRecord(
            user_id=user_id,
            period_start=period_start,
            period_end=period_end,
            cycle_length=cycle_length,
            flow_intensity=flow_intensity,
            notes_encrypted=notes_encrypted,
        )
        return await self.add(entity)

    async def get_latest(self, user_id: UUID) -> CycleRecord | None:
        stmt = select(CycleRecord).where(CycleRecord.user_id == user_id).order_by(desc(CycleRecord.period_start))
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list(
        self,
        *,
        user_id: UUID,
        date_from: date | None,
        date_to: date | None,
        skip: int,
        limit: int,
        sort_by: str,
        order: str,
    ) -> tuple[list[CycleRecord], int]:
        stmt: Select = select(CycleRecord).where(CycleRecord.user_id == user_id)
        if date_from is not None:
            stmt = stmt.where(CycleRecord.period_start >= date_from)
        if date_to is not None:
            stmt = stmt.where(CycleRecord.period_start <= date_to)

        sort_col = CycleRecord.period_start if sort_by == "period_start" else CycleRecord.cycle_length
        stmt = stmt.order_by(asc(sort_col) if order == "asc" else desc(sort_col))

        total = await self.count(stmt)
        result = await self.session.execute(stmt.offset(skip).limit(limit))
        return list(result.scalars().all()), total
