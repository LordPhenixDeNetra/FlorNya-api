from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.deps import get_current_user, get_cycle_service, get_fertility_service, require_bloom
from app.core.middleware import limiter
from app.models.user import User
from app.schemas.fertility import (
    ConceptionAttemptCreate,
    ConceptionAttemptPublic,
    FertilityCoachRequest,
    FertilityCoachResponse,
    FertilityLogCreate,
    FertilityLogPublic,
    FertilityScoreResponse,
)
from app.services.fertility_service import FertilityService

router = APIRouter()


@router.post("/logs", response_model=FertilityLogPublic)
@limiter.limit("60/minute")
async def log_fertility(
    request: Request,
    data: FertilityLogCreate,
    current_user: User = Depends(require_bloom),
    service: FertilityService = Depends(get_fertility_service),
) -> FertilityLogPublic:
    return await service.log_fertility(current_user, data)


@router.get("/logs", response_model=list[FertilityLogPublic])
@limiter.limit("60/minute")
async def list_fertility_logs(
    request: Request,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    current_user: User = Depends(require_bloom),
    service: FertilityService = Depends(get_fertility_service),
) -> list[FertilityLogPublic]:
    return await service.list_fertility_logs(current_user, date_from=date_from, date_to=date_to)


@router.get("/score", response_model=FertilityScoreResponse)
@limiter.limit("60/minute")
async def get_fertility_score(
    request: Request,
    target_date: date = Query(default=None),
    current_user: User = Depends(require_bloom),
    service: FertilityService = Depends(get_fertility_service),
    cycle_service=Depends(get_cycle_service),
) -> FertilityScoreResponse:
    if target_date is None:
        target_date = date.today()

    try:
        current = await cycle_service.get_current(current_user, today=target_date)
    except ValueError:
        raise HTTPException(status_code=404, detail="no_cycle_data")

    return await service.get_fertility_score(
        current_user,
        target_date=target_date,
        cycle_start=current.last_period_start,
        cycle_length=28,
    )


@router.post("/attempts", response_model=ConceptionAttemptPublic)
@limiter.limit("30/minute")
async def log_attempt(
    request: Request,
    data: ConceptionAttemptCreate,
    current_user: User = Depends(require_bloom),
    service: FertilityService = Depends(get_fertility_service),
) -> ConceptionAttemptPublic:
    return await service.log_attempt(current_user, data)


@router.get("/attempts", response_model=list[ConceptionAttemptPublic])
@limiter.limit("60/minute")
async def list_attempts(
    request: Request,
    current_user: User = Depends(require_bloom),
    service: FertilityService = Depends(get_fertility_service),
) -> list[ConceptionAttemptPublic]:
    return await service.list_attempts(current_user)


@router.post("/coach", response_model=FertilityCoachResponse)
@limiter.limit("20/hour")
async def fertility_coach(
    request: Request,
    data: FertilityCoachRequest,
    current_user: User = Depends(require_bloom),
    service: FertilityService = Depends(get_fertility_service),
    cycle_service=Depends(get_cycle_service),
) -> FertilityCoachResponse:
    cycle_context: dict = {}
    try:
        current = await cycle_service.get_current(current_user)
        cycle_context = {"cycle_phase": current.phase.value}
    except ValueError:
        pass
    return await service.fertility_coach(current_user, data.question, cycle_context)
