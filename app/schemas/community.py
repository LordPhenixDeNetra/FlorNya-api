from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import PaginationParams


class CommunityPostCreate(BaseModel):
    title: str = Field(min_length=5, max_length=200)
    body: str = Field(min_length=10, max_length=5000)
    category: str
    anonymous_display_name: str | None = Field(default=None, max_length=64)


class CommunityPostPublic(BaseModel):
    id: UUID
    category: str
    title: str
    body: str
    anonymous_display_name: str | None
    is_pinned: bool
    likes_count: int
    comments_count: int
    created_at: datetime
    is_own: bool = False


class CommunityRecipeCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    ingredients: list[str] = Field(min_length=1)
    instructions: str | None = Field(default=None, max_length=5000)
    phase: str | None = None
    cultural_cuisine: str | None = Field(default=None, max_length=100)
    prep_time_minutes: int | None = Field(default=None, ge=1, le=480)


class CommunityRecipePublic(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    description: str | None
    ingredients: list[str]
    instructions: str | None
    phase: str | None
    cultural_cuisine: str | None
    prep_time_minutes: int | None
    nutrition_score: int | None
    likes_count: int
    created_at: datetime
    is_own: bool = False


class ChallengePublic(BaseModel):
    id: UUID
    title: str
    description: str | None
    category: str
    duration_days: int
    badge_icon: str | None
    is_active: bool
    participants_count: int
    start_date: str | None
    end_date: str | None


class UserChallengePublic(BaseModel):
    id: UUID
    challenge_id: UUID
    challenge_title: str
    enrolled_at: datetime
    completed_at: datetime | None
    progress_days: int
    is_completed: bool
    progress_pct: float


class ChallengeFilterParams(PaginationParams):
    category: str | None = None
    active_only: bool = True
