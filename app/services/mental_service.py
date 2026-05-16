from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_sensitive, encrypt_sensitive
from app.models.user import User
from app.repositories.mood_repository import MoodRepository
from app.schemas.common import CursorPaginatedResponse
from app.schemas.mental import MoodFilterParams, MoodLogCreate, MoodLogPublic


def _period_to_timedelta(period: str) -> timedelta:
    value = int(period[:-1])
    unit = period[-1]
    if unit == "d":
        return timedelta(days=value)
    if unit == "w":
        return timedelta(weeks=value)
    if unit == "m":
        return timedelta(days=value * 30)
    raise ValueError("invalid_period")


class MentalService:
    def __init__(self, session: AsyncSession, moods: MoodRepository):
        self.session = session
        self.moods = moods

    async def create_mood(self, user: User, data: MoodLogCreate) -> MoodLogPublic:
        entity = await self.moods.create(
            user_id=user.id,
            log_date=data.log_date,
            mood_score=data.mood_score,
            journal_text_encrypted=encrypt_sensitive(data.journal_text),
        )
        await self.session.commit()
        await self.session.refresh(entity)
        return self._to_public(entity)

    async def list_moods(self, user: User, params: MoodFilterParams) -> CursorPaginatedResponse[MoodLogPublic]:
        date_from = None
        if params.period:
            date_from = date.today() - _period_to_timedelta(params.period)

        items, next_cursor, has_more = await self.moods.list_cursor(
            user_id=user.id,
            date_from=date_from,
            min_score=params.min_score,
            cursor=params.cursor,
            limit=params.limit,
        )
        public_items = [self._to_public(x) for x in items]
        return CursorPaginatedResponse(items=public_items, next_cursor=next_cursor, has_more=has_more)

    def _to_public(self, entity) -> MoodLogPublic:
        return MoodLogPublic(
            id=entity.id,
            user_id=entity.user_id,
            log_date=entity.log_date,
            mood_score=entity.mood_score,
            journal_text=decrypt_sensitive(entity.journal_text_encrypted),
            created_at=entity.created_at,
        )
