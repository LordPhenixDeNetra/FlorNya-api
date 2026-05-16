from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.deps import get_current_user, get_pregnancy_service, require_bloom, require_bloom_pro
from app.core.middleware import limiter
from app.models.user import User
from app.schemas.pregnancy import (
    AppointmentCreate,
    AppointmentPublic,
    BreastfeedingSessionCreate,
    BreastfeedingSessionPublic,
    EPDSCreate,
    EPDSPublic,
    PostpartumActivate,
    PregnancyActivate,
    PregnancyProfilePublic,
    PregnancySymptomCreate,
    PregnancySymptomPublic,
    PregnancyWeekInfo,
)
from app.services.pregnancy_service import PregnancyService

router = APIRouter()


@router.post("/activate", response_model=PregnancyProfilePublic)
@limiter.limit("10/minute")
async def activate_pregnancy(
    request: Request,
    data: PregnancyActivate,
    current_user: User = Depends(require_bloom),
    service: PregnancyService = Depends(get_pregnancy_service),
) -> PregnancyProfilePublic:
    return await service.activate_pregnancy(current_user, data)


@router.get("/profile", response_model=PregnancyProfilePublic)
@limiter.limit("60/minute")
async def get_pregnancy_profile(
    request: Request,
    current_user: User = Depends(require_bloom),
    service: PregnancyService = Depends(get_pregnancy_service),
) -> PregnancyProfilePublic:
    profile = await service.get_pregnancy_profile(current_user)
    if profile is None:
        raise HTTPException(status_code=404, detail="pregnancy_profile_not_found")
    return profile


@router.post("/postpartum", response_model=PregnancyProfilePublic)
@limiter.limit("10/minute")
async def activate_postpartum(
    request: Request,
    data: PostpartumActivate,
    current_user: User = Depends(require_bloom),
    service: PregnancyService = Depends(get_pregnancy_service),
) -> PregnancyProfilePublic:
    return await service.activate_postpartum(current_user, data)


@router.get("/week/{week}", response_model=PregnancyWeekInfo)
@limiter.limit("60/minute")
async def get_week_info(
    request: Request,
    week: int,
    current_user: User = Depends(require_bloom),
    service: PregnancyService = Depends(get_pregnancy_service),
) -> PregnancyWeekInfo:
    if not (1 <= week <= 42):
        raise HTTPException(status_code=422, detail="week_out_of_range")
    return service.get_week_info(week)


@router.post("/symptoms", response_model=PregnancySymptomPublic)
@limiter.limit("60/minute")
async def log_pregnancy_symptom(
    request: Request,
    data: PregnancySymptomCreate,
    current_user: User = Depends(require_bloom),
    service: PregnancyService = Depends(get_pregnancy_service),
) -> PregnancySymptomPublic:
    profile = await service.get_pregnancy_profile(current_user)
    week = profile.current_week if profile else None
    return await service.log_pregnancy_symptom(current_user, data, week)


@router.get("/symptoms", response_model=list[PregnancySymptomPublic])
@limiter.limit("60/minute")
async def list_pregnancy_symptoms(
    request: Request,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    current_user: User = Depends(require_bloom),
    service: PregnancyService = Depends(get_pregnancy_service),
) -> list[PregnancySymptomPublic]:
    return await service.list_pregnancy_symptoms(current_user, date_from=date_from, date_to=date_to)


@router.post("/appointments", response_model=AppointmentPublic)
@limiter.limit("30/minute")
async def create_appointment(
    request: Request,
    data: AppointmentCreate,
    current_user: User = Depends(require_bloom),
    service: PregnancyService = Depends(get_pregnancy_service),
) -> AppointmentPublic:
    return await service.create_appointment(current_user, data)


@router.get("/appointments", response_model=list[AppointmentPublic])
@limiter.limit("60/minute")
async def list_appointments(
    request: Request,
    upcoming_only: bool = Query(default=False),
    current_user: User = Depends(require_bloom),
    service: PregnancyService = Depends(get_pregnancy_service),
) -> list[AppointmentPublic]:
    return await service.list_appointments(current_user, upcoming_only=upcoming_only)


@router.post("/breastfeeding", response_model=BreastfeedingSessionPublic)
@limiter.limit("60/minute")
async def log_breastfeeding(
    request: Request,
    data: BreastfeedingSessionCreate,
    current_user: User = Depends(require_bloom),
    service: PregnancyService = Depends(get_pregnancy_service),
) -> BreastfeedingSessionPublic:
    return await service.log_breastfeeding(current_user, data)


@router.get("/breastfeeding", response_model=list[BreastfeedingSessionPublic])
@limiter.limit("60/minute")
async def list_breastfeeding(
    request: Request,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    current_user: User = Depends(require_bloom),
    service: PregnancyService = Depends(get_pregnancy_service),
) -> list[BreastfeedingSessionPublic]:
    return await service.list_breastfeeding(current_user, date_from=date_from, date_to=date_to)


@router.post("/epds", response_model=EPDSPublic)
@limiter.limit("5/day")
async def submit_epds(
    request: Request,
    data: EPDSCreate,
    current_user: User = Depends(require_bloom),
    service: PregnancyService = Depends(get_pregnancy_service),
) -> EPDSPublic:
    return await service.submit_epds(current_user, data)
