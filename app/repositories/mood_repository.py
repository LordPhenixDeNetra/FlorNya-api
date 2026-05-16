import base64
from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Select, desc, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mood_log import MoodLog
from app.repositories.base import BaseRepository


def _encode_cursor(created_at: datetime, entity_id: UUID) -> str:
    raw = f"{created_at.isoformat()}|{entity_id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def _decode_cursor(cursor: str) -> tuple[datetime, UUID]:
    raw = base64.urlsafe_b64decode(cursor.encode()).decode()
    created_at_s, entity_id_s = raw.split("|", 1)
    return datetime.fromisoformat(created_at_s), UUID(entity_id_s)


class MoodRepository(BaseRepository[MoodLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=MoodLog)

    async def create(
        self,
        *,
        user_id: UUID,
        log_date: date,
        mood_score: int,
        journal_text_encrypted: str | None,
    ) -> MoodLog:
        entity = MoodLog(
            user_id=user_id,
            log_date=log_date,
            mood_score=mood_score,
            journal_text_encrypted=journal_text_encrypted,
        )
        return await self.add(entity)

    async def list_cursor(
        self,
        *,
        user_id: UUID,
        date_from: date | None,
        min_score: int | None,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[MoodLog], str | None, bool]:
        stmt: Select = select(MoodLog).where(MoodLog.user_id == user_id)
        if date_from is not None:
            stmt = stmt.where(MoodLog.log_date >= date_from)
        if min_score is not None:
            stmt = stmt.where(MoodLog.mood_score >= min_score)

        stmt = stmt.order_by(desc(MoodLog.created_at), desc(MoodLog.id))

        if cursor:
            cursor_created_at, cursor_id = _decode_cursor(cursor)
            stmt = stmt.where(tuple_(MoodLog.created_at, MoodLog.id) < tuple_(cursor_created_at, cursor_id))

        result = await self.session.execute(stmt.limit(limit + 1))
        items = list(result.scalars().all())
        has_more = len(items) > limit
        items = items[:limit]

        next_cursor = None
        if has_more and items:
            last = items[-1]
            next_cursor = _encode_cursor(last.created_at, last.id)

        return items, next_cursor, has_more
