from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.emotional_journal import EmotionalJournalEntry, JournalPromptType


class EmotionalJournalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        user_id: UUID,
        log_date: date,
        text_encrypted: str | None,
        prompt_type: JournalPromptType = JournalPromptType.free,
        prompt_text_encrypted: str | None = None,
        mood_score_at_entry: int | None = None,
    ) -> EmotionalJournalEntry:
        entry = EmotionalJournalEntry(
            user_id=user_id,
            log_date=log_date,
            text_encrypted=text_encrypted,
            prompt_type=prompt_type,
            prompt_text_encrypted=prompt_text_encrypted,
            mood_score_at_entry=mood_score_at_entry,
        )
        self.session.add(entry)
        return entry

    async def list_by_user(
        self,
        user_id: UUID,
        limit: int = 30,
        offset: int = 0,
    ) -> list[EmotionalJournalEntry]:
        result = await self.session.execute(
            select(EmotionalJournalEntry)
            .where(EmotionalJournalEntry.user_id == user_id)
            .order_by(EmotionalJournalEntry.log_date.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_recent_mood_scores(self, user_id: UUID, days: int = 7) -> list[int]:
        from datetime import timedelta
        from sqlalchemy import and_
        cutoff = date.today() - timedelta(days=days)
        result = await self.session.execute(
            select(EmotionalJournalEntry.mood_score_at_entry)
            .where(
                and_(
                    EmotionalJournalEntry.user_id == user_id,
                    EmotionalJournalEntry.log_date >= cutoff,
                    EmotionalJournalEntry.mood_score_at_entry.isnot(None),
                )
            )
            .order_by(EmotionalJournalEntry.log_date.desc())
        )
        return [r for r in result.scalars().all() if r is not None]
