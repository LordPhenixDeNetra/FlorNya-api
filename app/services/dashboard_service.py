from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cycle_record import CycleRecord
from app.models.female_profile import FemaleProfile
from app.models.mood_log import MoodLog
from app.models.pregnancy_profile import PregnancyProfile, PregnancyStatus
from app.models.reminder_config import ReminderConfig
from app.models.user import User
from app.repositories.challenge_repository import UserChallengeRepository
from app.schemas.dashboard import (
    DashboardCycleInfo,
    DashboardMoodInfo,
    DashboardPregnancyInfo,
    DashboardReminderInfo,
    DashboardResponse,
)


class DashboardService:
    def __init__(
        self,
        session: AsyncSession,
        user_challenges_repo: UserChallengeRepository,
    ):
        self.session = session
        self.user_challenges_repo = user_challenges_repo

    async def get_dashboard(self, user: User) -> DashboardResponse:
        cycle_info = await self._get_cycle_info(user)
        pregnancy_info = await self._get_pregnancy_info(user)
        mood_info = await self._get_mood_info(user)
        reminders = await self._get_reminders(user)
        active_challenges = await self._get_active_challenges(user)

        weekly_goal = self._compute_weekly_goal(cycle_info, mood_info)

        return DashboardResponse(
            user_id=user.id,
            first_name=user.first_name,
            plan=user.plan.value,
            beta_access=user.beta_access,
            cycle=cycle_info,
            pregnancy=pregnancy_info,
            mood=mood_info,
            upcoming_reminders=reminders,
            active_challenges=active_challenges,
            weekly_goal=weekly_goal,
        )

    async def _get_cycle_info(self, user: User) -> DashboardCycleInfo | None:
        result = await self.session.execute(
            select(CycleRecord)
            .where(CycleRecord.user_id == user.id)
            .order_by(CycleRecord.period_start.desc())
            .limit(1)
        )
        cycle = result.scalar_one_or_none()
        if not cycle:
            return None

        today = date.today()
        cycle_day = (today - cycle.period_start).days + 1
        cycle_len = cycle.cycle_length or 28
        next_period = cycle.period_start + timedelta(days=cycle_len)
        days_until = (next_period - today).days

        ovulation_day = cycle_len - 14
        is_fertile = ovulation_day - 3 <= cycle_day <= ovulation_day + 1

        if cycle_day <= 5:
            phase = "menstrual"
        elif cycle_day <= 13:
            phase = "follicular"
        elif cycle_day <= 16:
            phase = "ovulatory"
        else:
            phase = "luteal"

        return DashboardCycleInfo(
            current_phase=phase,
            cycle_day=cycle_day,
            days_until_next_period=max(0, days_until),
            next_period_date=next_period,
            is_fertile_window=is_fertile,
        )

    async def _get_pregnancy_info(self, user: User) -> DashboardPregnancyInfo | None:
        result = await self.session.execute(
            select(PregnancyProfile).where(
                PregnancyProfile.user_id == user.id,
                PregnancyProfile.status == PregnancyStatus.active,
            )
        )
        profile = result.scalar_one_or_none()
        if not profile:
            return None

        today = date.today()
        if profile.lmp_date:
            current_week = (today - profile.lmp_date).days // 7
        else:
            current_week = profile.weeks_at_activation or 0

        trimester = 1 if current_week < 13 else (2 if current_week < 27 else 3)

        return DashboardPregnancyInfo(
            current_week=current_week,
            trimester=trimester,
            due_date=profile.due_date,
        )

    async def _get_mood_info(self, user: User) -> DashboardMoodInfo:
        today = date.today()

        today_result = await self.session.execute(
            select(MoodLog.mood_score).where(MoodLog.user_id == user.id, MoodLog.log_date == today)
        )
        today_mood = today_result.scalar_one_or_none()

        cutoff = today - timedelta(days=7)
        week_result = await self.session.execute(
            select(MoodLog.mood_score).where(MoodLog.user_id == user.id, MoodLog.log_date >= cutoff)
        )
        week_scores = list(week_result.scalars().all())
        avg_7d = round(sum(week_scores) / len(week_scores), 1) if week_scores else None

        trend = "stable"
        if len(week_scores) >= 4:
            recent = sum(week_scores[-3:]) / 3
            older = sum(week_scores[:-3]) / max(len(week_scores) - 3, 1)
            trend = "improving" if recent > older + 0.3 else ("declining" if recent < older - 0.3 else "stable")

        return DashboardMoodInfo(today_mood=today_mood, average_mood_7d=avg_7d, trend=trend)

    async def _get_reminders(self, user: User) -> list[DashboardReminderInfo]:
        from app.core.security import decrypt_sensitive
        result = await self.session.execute(
            select(ReminderConfig).where(ReminderConfig.user_id == user.id, ReminderConfig.is_enabled == True)  # noqa: E712
        )
        reminders = list(result.scalars().all())
        return [
            DashboardReminderInfo(
                reminder_type=r.reminder_type.value,
                time_of_day=r.time_of_day,
                label=decrypt_sensitive(r.label_encrypted),
            )
            for r in reminders[:3]
        ]

    async def _get_active_challenges(self, user: User) -> list[str]:
        from app.repositories.challenge_repository import ChallengeRepository
        user_challenges = await self.user_challenges_repo.list_user_challenges(user.id)
        active = [uc for uc in user_challenges if not uc.is_completed]
        result = await self.session.execute(
            select(CycleRecord.period_start).where(CycleRecord.user_id == user.id).limit(1)
        )
        return [str(uc.challenge_id)[:8] for uc in active[:3]]

    def _compute_weekly_goal(self, cycle: DashboardCycleInfo | None, mood: DashboardMoodInfo) -> str | None:
        if not cycle:
            return "Enregistrez votre premier cycle"
        if mood.today_mood is None:
            return "Check-in émotionnel du jour"
        if cycle.current_phase == "luteal":
            return "Phase lutéale : privilégiez le magnésium et le repos"
        if cycle.current_phase == "follicular":
            return "Phase folliculaire : énergie au top, objectif exercice !"
        if cycle.current_phase == "ovulatory":
            return "Phase ovulatoire : communication et créativité à leur meilleur"
        return "Phase menstruelle : douceur et nutrition anti-inflammatoire"
