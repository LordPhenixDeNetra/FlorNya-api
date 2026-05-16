from datetime import date

from fastapi import APIRouter, Depends, Query, Request, Response

from app.api.deps import get_current_user, get_menopause_service, require_bloom, require_bloom_pro
from app.core.middleware import limiter
from app.models.user import User
from app.schemas.menopause import (
    HotFlashQuickLog,
    MenopauseInsightsResponse,
    MenopauseLogCreate,
    MenopauseLogPublic,
    PerimenopauseScreening,
    PerimenopauseScreeningResult,
)
from app.services.menopause_service import MenopauseService

router = APIRouter()


@router.post("/logs", response_model=MenopauseLogPublic)
@limiter.limit("60/minute")
async def log_symptoms(
    request: Request,
    data: MenopauseLogCreate,
    current_user: User = Depends(require_bloom),
    service: MenopauseService = Depends(get_menopause_service),
) -> MenopauseLogPublic:
    return await service.log_symptoms(current_user, data)


@router.get("/logs", response_model=list[MenopauseLogPublic])
@limiter.limit("60/minute")
async def list_logs(
    request: Request,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    current_user: User = Depends(require_bloom),
    service: MenopauseService = Depends(get_menopause_service),
) -> list[MenopauseLogPublic]:
    return await service.list_logs(current_user, date_from=date_from, date_to=date_to)


@router.post("/hot-flash", response_model=MenopauseLogPublic)
@limiter.limit("100/day")
async def quick_hot_flash(
    request: Request,
    data: HotFlashQuickLog,
    current_user: User = Depends(require_bloom),
    service: MenopauseService = Depends(get_menopause_service),
) -> MenopauseLogPublic:
    return await service.quick_hot_flash(current_user, data)


@router.get("/insights", response_model=MenopauseInsightsResponse)
@limiter.limit("20/hour")
async def get_insights(
    request: Request,
    current_user: User = Depends(require_bloom),
    service: MenopauseService = Depends(get_menopause_service),
) -> MenopauseInsightsResponse:
    return await service.get_insights(current_user)


@router.post("/perimenopause/screening", response_model=PerimenopauseScreeningResult)
@limiter.limit("10/minute")
async def perimenopause_screening(
    request: Request,
    data: PerimenopauseScreening,
    current_user: User = Depends(require_bloom),
    service: MenopauseService = Depends(get_menopause_service),
) -> PerimenopauseScreeningResult:
    return await service.perimenopause_screening(current_user, data)


@router.get("/export/pdf")
@limiter.limit("5/day")
async def export_pdf(
    request: Request,
    current_user: User = Depends(require_bloom_pro),
    service: MenopauseService = Depends(get_menopause_service),
) -> Response:
    pdf_bytes = await service.export_pdf(current_user)
    filename = f"flornya_menopause_{current_user.id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
