from datetime import date

from fastapi import APIRouter, Depends, Query, Request

from app.api.deps import get_current_user, get_cycle_service, get_nutrition_service, require_bloom
from app.core.middleware import limiter
from app.models.user import User
from app.schemas.cycle import CyclePhase
from app.schemas.nutrition import (
    NutritionCoachRequest,
    NutritionCoachResponse,
    NutritionLogCreate,
    NutritionLogPublic,
    NutritionalPlanResponse,
    RecipePublic,
    ShoppingListResponse,
    SupplementRecommendation,
)
from app.services.nutrition_service import NutritionService

router = APIRouter()


@router.post("/logs", response_model=NutritionLogPublic)
@limiter.limit("60/minute")
async def log_meals(
    request: Request,
    data: NutritionLogCreate,
    current_user: User = Depends(require_bloom),
    service: NutritionService = Depends(get_nutrition_service),
    cycle_service=Depends(get_cycle_service),
) -> NutritionLogPublic:
    current_phase = None
    try:
        current = await cycle_service.get_current(current_user)
        current_phase = current.phase
    except ValueError:
        pass
    return await service.log_meals(current_user, data, current_phase=current_phase)


@router.get("/logs", response_model=list[NutritionLogPublic])
@limiter.limit("60/minute")
async def list_logs(
    request: Request,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    current_user: User = Depends(require_bloom),
    service: NutritionService = Depends(get_nutrition_service),
) -> list[NutritionLogPublic]:
    return await service.list_logs(current_user, date_from=date_from, date_to=date_to)


@router.get("/plan", response_model=NutritionalPlanResponse)
@limiter.limit("30/minute")
async def get_nutritional_plan(
    request: Request,
    phase: CyclePhase | None = Query(default=None),
    current_user: User = Depends(require_bloom),
    service: NutritionService = Depends(get_nutrition_service),
    cycle_service=Depends(get_cycle_service),
) -> NutritionalPlanResponse:
    if phase is None:
        try:
            current = await cycle_service.get_current(current_user)
            phase = current.phase
        except ValueError:
            phase = CyclePhase.follicular

    return await service.get_nutritional_plan(current_user, phase)


@router.get("/recipes", response_model=list[RecipePublic])
@limiter.limit("60/minute")
async def get_recipes(
    request: Request,
    phase: CyclePhase | None = Query(default=None),
    current_user: User = Depends(require_bloom),
    service: NutritionService = Depends(get_nutrition_service),
) -> list[RecipePublic]:
    return service.get_recipes(phase=phase)


@router.get("/supplements", response_model=list[SupplementRecommendation])
@limiter.limit("60/minute")
async def get_supplements(
    request: Request,
    phase: CyclePhase | None = Query(default=None),
    current_user: User = Depends(require_bloom),
    service: NutritionService = Depends(get_nutrition_service),
) -> list[SupplementRecommendation]:
    return service.get_supplements(phase=phase)


@router.get("/shopping-list", response_model=ShoppingListResponse)
@limiter.limit("20/hour")
async def get_shopping_list(
    request: Request,
    phase: CyclePhase | None = Query(default=None),
    current_user: User = Depends(require_bloom),
    service: NutritionService = Depends(get_nutrition_service),
    cycle_service=Depends(get_cycle_service),
) -> ShoppingListResponse:
    if phase is None:
        try:
            current = await cycle_service.get_current(current_user)
            phase = current.phase
        except ValueError:
            phase = CyclePhase.follicular

    from app.repositories.female_profile_repository import FemaleProfileRepository
    from sqlalchemy.ext.asyncio import AsyncSession
    cuisine = None

    return await service.get_shopping_list(current_user, phase, cuisine_preference=cuisine)


@router.post("/coach", response_model=NutritionCoachResponse)
@limiter.limit("20/hour")
async def nutrition_coach(
    request: Request,
    data: NutritionCoachRequest,
    current_user: User = Depends(require_bloom),
    service: NutritionService = Depends(get_nutrition_service),
    cycle_service=Depends(get_cycle_service),
) -> NutritionCoachResponse:
    context: dict = {}
    try:
        current = await cycle_service.get_current(current_user)
        context["cycle_phase"] = current.phase.value
    except ValueError:
        pass
    return await service.nutrition_coach(current_user, data.question, context)
