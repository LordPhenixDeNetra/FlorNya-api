"""Celery tasks for account lifecycle management."""
import asyncio
from datetime import datetime, timedelta, timezone

from app.celery_app import celery_app
from app.core.database import async_session_factory


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@celery_app.task(name="app.tasks.account_tasks.anonymize_pending_deletions")
def anonymize_pending_deletions() -> None:
    _run(_async_anonymize_pending_deletions())


async def _async_anonymize_pending_deletions() -> None:
    from sqlalchemy import select, update

    from app.models.user import User

    cutoff = datetime.now(timezone.utc) - timedelta(days=30)

    async with async_session_factory() as session:
        stmt = (
            select(User)
            .where(
                User.deleted_at.isnot(None),
                User.deleted_at <= cutoff,
                User.anonymized_at.is_(None),
            )
        )
        result = await session.execute(stmt)
        users = result.scalars().all()

        now = datetime.now(timezone.utc)
        for user in users:
            user.first_name = None
            user.photo_url = None
            user.date_of_birth = user.date_of_birth.replace(month=1, day=1)
            user.anonymized_at = now
            print(f"[anonymize] anonymized user {user.id}")

        await session.commit()
