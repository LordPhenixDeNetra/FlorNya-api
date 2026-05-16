from fastapi import APIRouter, Depends, Request

from app.api.deps import get_current_user, get_intimate_service, require_adult, require_bloom
from app.core.middleware import limiter
from app.models.user import User
from app.schemas.intimate import (
    ContraceptionMethod,
    IntimateHealthLogCreate,
    IntimateHealthLogPublic,
    LibidoLogCreate,
    LibidoLogPublic,
    SexualEducationContent,
    VaginalHealthInfo,
)
from app.services.intimate_service import IntimateService

router = APIRouter()


@router.post("/libido", response_model=LibidoLogPublic)
@limiter.limit("60/minute")
async def log_libido(
    request: Request,
    data: LibidoLogCreate,
    current_user: User = Depends(require_adult),
    service: IntimateService = Depends(get_intimate_service),
) -> LibidoLogPublic:
    return await service.log_libido(current_user, data)


@router.get("/libido", response_model=list[LibidoLogPublic])
@limiter.limit("60/minute")
async def list_libido_logs(
    request: Request,
    limit: int = 30,
    current_user: User = Depends(require_adult),
    service: IntimateService = Depends(get_intimate_service),
) -> list[LibidoLogPublic]:
    return await service.list_libido_logs(current_user, limit=limit)


@router.post("/health-log", response_model=IntimateHealthLogPublic)
@limiter.limit("60/minute")
async def log_intimate_health(
    request: Request,
    data: IntimateHealthLogCreate,
    current_user: User = Depends(require_bloom),
    service: IntimateService = Depends(get_intimate_service),
) -> IntimateHealthLogPublic:
    return await service.log_intimate_health(current_user, data)


@router.get("/health-log", response_model=list[IntimateHealthLogPublic])
@limiter.limit("60/minute")
async def list_intimate_health_logs(
    request: Request,
    limit: int = 30,
    current_user: User = Depends(require_bloom),
    service: IntimateService = Depends(get_intimate_service),
) -> list[IntimateHealthLogPublic]:
    return await service.list_intimate_health_logs(current_user, limit=limit)


@router.get("/contraception-guide", response_model=list[ContraceptionMethod])
@limiter.limit("60/minute")
async def get_contraception_guide(
    request: Request,
    current_user: User = Depends(get_current_user),
    service: IntimateService = Depends(get_intimate_service),
) -> list[ContraceptionMethod]:
    return service.get_contraception_guide()


@router.get("/vaginal-health", response_model=VaginalHealthInfo)
@limiter.limit("60/minute")
async def get_vaginal_health_info(
    request: Request,
    current_user: User = Depends(require_bloom),
    service: IntimateService = Depends(get_intimate_service),
) -> VaginalHealthInfo:
    return service.get_vaginal_health_info()


@router.get("/sexual-education", response_model=list[SexualEducationContent])
@limiter.limit("60/minute")
async def get_sexual_education(
    request: Request,
    current_user: User = Depends(get_current_user),
    service: IntimateService = Depends(get_intimate_service),
) -> list[SexualEducationContent]:
    from app.core.security import is_adult
    adult = is_adult(current_user.date_of_birth)
    return service.get_sexual_education(is_adult=adult)


@router.post("/advice", response_model=dict)
@limiter.limit("20/hour")
async def get_intimate_advice(
    request: Request,
    body: dict,
    current_user: User = Depends(require_bloom),
    service: IntimateService = Depends(get_intimate_service),
) -> dict:
    concern = body.get("concern", "")
    cycle_phase = body.get("cycle_phase", "follicular")
    advice = await service.get_intimate_advice(current_user, concern, cycle_phase)
    return {"advice": advice}
