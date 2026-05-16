"""Celery tasks for sending periodic reminders to users."""
import asyncio
from datetime import date, timedelta

from sqlalchemy import select, update

from app.celery_app import celery_app
from app.core.database import async_session_factory
from app.models.reminder_config import ReminderType
from app.repositories.cycle_repository import CycleRepository
from app.repositories.mood_repository import MoodRepository
from app.repositories.reminder_repository import ReminderRepository
from app.services.phase_calculator import PhaseCalculator


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@celery_app.task(name="app.tasks.reminder_tasks.send_period_reminders")
def send_period_reminders() -> None:
    _run(_async_send_period_reminders())


async def _async_send_period_reminders() -> None:
    from app.repositories.female_profile_repository import FemaleProfileRepository

    async with async_session_factory() as session:
        reminder_repo = ReminderRepository(session)
        cycle_repo = CycleRepository(session)
        profile_repo = FemaleProfileRepository(session)
        calculator = PhaseCalculator()

        configs = await reminder_repo.list_enabled_by_type(ReminderType.period)
        today = date.today()

        for config in configs:
            try:
                latest = await cycle_repo.get_latest(config.user_id)
                if latest is None:
                    continue

                profile = await profile_repo.get_by_user_id(config.user_id)
                days_before = profile.period_reminder_days_before if profile else 2

                next_period = calculator.predict_next_period(latest.period_start, latest.cycle_length)
                days_until = (next_period - today).days

                if days_until == days_before:
                    if profile and profile.last_period_reminder_sent == today:
                        continue
                    _log_notification(
                        str(config.user_id),
                        f"Votre prochaine période est dans {days_before} jours.",
                        "period_reminder",
                    )
                    if profile:
                        profile.last_period_reminder_sent = today

            except Exception as exc:
                print(f"[period_reminder] error for user {config.user_id}: {exc}")

        await session.commit()


@celery_app.task(name="app.tasks.reminder_tasks.send_medication_reminders")
def send_medication_reminders() -> None:
    _run(_async_send_medication_reminders())


async def _async_send_medication_reminders() -> None:
    from datetime import datetime, timezone

    async with async_session_factory() as session:
        reminder_repo = ReminderRepository(session)
        configs = await reminder_repo.list_enabled_by_type(ReminderType.medication)
        current_hour = datetime.now(timezone.utc).strftime("%H")

        for config in configs:
            reminder_hour = config.time_of_day[:2]
            if reminder_hour == current_hour:
                _log_notification(
                    str(config.user_id),
                    "N'oubliez pas votre médicament.",
                    "medication_reminder",
                )


@celery_app.task(name="app.tasks.reminder_tasks.send_hydration_reminders")
def send_hydration_reminders() -> None:
    _run(_async_send_hydration_reminders())


async def _async_send_hydration_reminders() -> None:
    async with async_session_factory() as session:
        reminder_repo = ReminderRepository(session)
        configs = await reminder_repo.list_enabled_by_type(ReminderType.hydration)

        for config in configs:
            _log_notification(
                str(config.user_id),
                "Pensez à boire de l'eau ! 💧",
                "hydration_reminder",
            )


@celery_app.task(name="app.tasks.reminder_tasks.send_mood_checkin_reminders")
def send_mood_checkin_reminders() -> None:
    _run(_async_send_mood_checkin_reminders())


async def _async_send_mood_checkin_reminders() -> None:
    async with async_session_factory() as session:
        reminder_repo = ReminderRepository(session)
        mood_repo = MoodRepository(session)
        configs = await reminder_repo.list_enabled_by_type(ReminderType.mood_checkin)
        today = date.today()

        for config in configs:
            try:
                items, _, _ = await mood_repo.list_cursor(
                    user_id=config.user_id,
                    date_from=today,
                    min_score=None,
                    cursor=None,
                    limit=1,
                )
                if items:
                    continue
                _log_notification(
                    str(config.user_id),
                    "Comment vous sentez-vous aujourd'hui ?",
                    "mood_checkin_reminder",
                )
            except Exception as exc:
                print(f"[mood_checkin] error for user {config.user_id}: {exc}")


@celery_app.task(name="app.tasks.reminder_tasks.send_pregnancy_appointment_reminders")
def send_pregnancy_appointment_reminders() -> None:
    _run(_async_send_pregnancy_appointment_reminders())


async def _async_send_pregnancy_appointment_reminders() -> None:
    from app.models.pregnancy_appointment import PregnancyAppointment

    async with async_session_factory() as session:
        today = date.today()
        in_7_days = today + timedelta(days=7)
        in_1_day = today + timedelta(days=1)

        result = await session.execute(
            select(PregnancyAppointment).where(
                PregnancyAppointment.appointment_date.in_([in_7_days, in_1_day])
            )
        )
        appointments = result.scalars().all()

        for appt in appointments:
            days_until = (appt.appointment_date - today).days
            if days_until == 7 and not appt.reminder_sent_7d:
                _log_notification(
                    str(appt.user_id),
                    f"Rappel : rendez-vous \"{appt.title}\" dans 7 jours ({appt.appointment_date}).",
                    "pregnancy_appointment_7d",
                )
                appt.reminder_sent_7d = True
            elif days_until == 1 and not appt.reminder_sent_1d:
                _log_notification(
                    str(appt.user_id),
                    f"Rappel : rendez-vous \"{appt.title}\" demain ({appt.appointment_date}).",
                    "pregnancy_appointment_1d",
                )
                appt.reminder_sent_1d = True

        await session.commit()


def _log_notification(user_id: str, message: str, notification_type: str) -> None:
    print(f"[NOTIFICATION] user={user_id} type={notification_type} message={message}")
