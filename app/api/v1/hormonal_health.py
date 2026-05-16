from datetime import date

from fastapi import APIRouter, Depends, Query, Request, Response

from app.api.deps import get_current_user, get_hormonal_health_service, require_bloom, require_bloom_pro
from app.core.middleware import limiter
from app.models.user import User
from app.schemas.hormonal_health import (
    EndoResourcesResponse,
    HormonalTreatmentCreate,
    HormonalTreatmentPublic,
    PCOSRiskAssessment,
    PCOSRiskResponse,
    PainLogCreate,
    PainLogPublic,
)
from app.services.hormonal_health_service import HormonalHealthService

router = APIRouter()


@router.post("/pain", response_model=PainLogPublic)
@limiter.limit("60/minute")
async def log_pain(
    request: Request,
    data: PainLogCreate,
    current_user: User = Depends(require_bloom),
    service: HormonalHealthService = Depends(get_hormonal_health_service),
) -> PainLogPublic:
    return await service.log_pain(current_user, data)


@router.get("/pain", response_model=list[PainLogPublic])
@limiter.limit("60/minute")
async def list_pain_logs(
    request: Request,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    current_user: User = Depends(require_bloom),
    service: HormonalHealthService = Depends(get_hormonal_health_service),
) -> list[PainLogPublic]:
    return await service.list_pain_logs(current_user, date_from=date_from, date_to=date_to)


@router.get("/pain/export/pdf")
@limiter.limit("5/day")
async def export_pain_pdf(
    request: Request,
    current_user: User = Depends(require_bloom_pro),
    service: HormonalHealthService = Depends(get_hormonal_health_service),
) -> Response:
    pdf_bytes = await service.export_pain_pdf(current_user)
    filename = f"flornya_pain_report_{current_user.id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/pcos/assessment", response_model=PCOSRiskResponse)
@limiter.limit("10/minute")
async def pcos_risk_assessment(
    request: Request,
    data: PCOSRiskAssessment,
    current_user: User = Depends(require_bloom),
    service: HormonalHealthService = Depends(get_hormonal_health_service),
) -> PCOSRiskResponse:
    return await service.pcos_risk_assessment(current_user, data)


@router.get("/endometriosis/resources", response_model=EndoResourcesResponse)
@limiter.limit("60/minute")
async def endo_resources(
    request: Request,
    current_user: User = Depends(require_bloom),
    service: HormonalHealthService = Depends(get_hormonal_health_service),
) -> EndoResourcesResponse:
    return service.get_endo_resources()


@router.post("/treatments", response_model=HormonalTreatmentPublic)
@limiter.limit("30/minute")
async def add_treatment(
    request: Request,
    data: HormonalTreatmentCreate,
    current_user: User = Depends(get_current_user),
    service: HormonalHealthService = Depends(get_hormonal_health_service),
) -> HormonalTreatmentPublic:
    return await service.add_treatment(current_user, data)


@router.get("/treatments", response_model=list[HormonalTreatmentPublic])
@limiter.limit("60/minute")
async def list_treatments(
    request: Request,
    active_only: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    service: HormonalHealthService = Depends(get_hormonal_health_service),
) -> list[HormonalTreatmentPublic]:
    return await service.list_treatments(current_user, active_only=active_only)
