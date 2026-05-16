from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class NutritionLogCreate(BaseModel):
    log_date: date
    meals: list[str] = Field(default_factory=list, max_length=20)
    water_glasses: int | None = Field(default=None, ge=0, le=30)
    notes: str | None = Field(default=None, max_length=5000)


class NutritionLogPublic(BaseModel):
    id: UUID
    user_id: UUID
    log_date: date
    meals: list[str]
    hormonal_impact_score: int | None
    ai_analysis: str | None
    water_glasses: int | None
    notes: str | None
    created_at: datetime


class NutritionalPlanResponse(BaseModel):
    phase: str
    phase_description: str
    key_nutrients: list[str]
    recommended_foods: list[str]
    foods_to_limit: list[str]
    sample_meal_plan: str
    supplements: list[str]


class RecipePublic(BaseModel):
    title: str
    phase: str
    prep_time_minutes: int
    ingredients: list[str]
    instructions: str
    nutritional_benefits: str
    cultural_style: str | None


class SupplementRecommendation(BaseModel):
    name: str
    benefit: str
    dosage_suggestion: str
    phases_recommended: list[str]
    caution: str | None


class ShoppingListResponse(BaseModel):
    week_start: date
    phase: str
    items_by_category: dict[str, list[str]]
    estimated_servings: int


class NutritionCoachRequest(BaseModel):
    question: str = Field(max_length=1000)


class NutritionCoachResponse(BaseModel):
    answer: str
    disclaimer: str = "Ces informations sont indicatives et ne remplacent pas un avis d'un professionnel de santé."
