from datetime import date
from uuid import UUID

from pydantic import BaseModel


class DashboardCycleInfo(BaseModel):
    current_phase: str | None
    cycle_day: int | None
    days_until_next_period: int | None
    next_period_date: date | None
    is_fertile_window: bool


class DashboardMoodInfo(BaseModel):
    today_mood: int | None
    average_mood_7d: float | None
    trend: str


class DashboardReminderInfo(BaseModel):
    reminder_type: str
    time_of_day: str
    label: str | None


class DashboardPregnancyInfo(BaseModel):
    current_week: int
    trimester: int
    due_date: date | None


class DashboardResponse(BaseModel):
    user_id: UUID
    first_name: str | None
    plan: str
    beta_access: bool
    cycle: DashboardCycleInfo | None
    pregnancy: DashboardPregnancyInfo | None
    mood: DashboardMoodInfo
    upcoming_reminders: list[DashboardReminderInfo]
    active_challenges: list[str]
    weekly_goal: str | None
