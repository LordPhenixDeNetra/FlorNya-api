from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response

from app.api.deps import get_current_user, get_cycle_service, require_bloom, require_bloom_pro
from app.core.middleware import limiter
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.cycle import (
    CalendarResponse,
    CurrentCycleResponse,
    CycleFilterParams,
    CycleInsightsResponse,
    CycleRecordCreate,
    CycleRecordPublic,
    SymptomFilterParams,
    SymptomLogCreate,
    SymptomLogPublic,
)
from app.services.cycle_service import CycleService

router = APIRouter()


@router.post("/records", response_model=CycleRecordPublic)
@limiter.limit("60/minute")
async def create_record(
    request: Request,
    data: CycleRecordCreate,
    current_user: User = Depends(get_current_user),
    service: CycleService = Depends(get_cycle_service),
) -> CycleRecordPublic:
    return await service.create_record(current_user, data)


@router.get("/records", response_model=PaginatedResponse[CycleRecordPublic])
@limiter.limit("60/minute")
async def list_records(
    request: Request,
    params: CycleFilterParams = Depends(),
    current_user: User = Depends(get_current_user),
    service: CycleService = Depends(get_cycle_service),
) -> PaginatedResponse[CycleRecordPublic]:
    return await service.list_records(current_user, params)


@router.get("/current", response_model=CurrentCycleResponse)
@limiter.limit("60/minute")
async def current_cycle(
    request: Request,
    current_user: User = Depends(get_current_user),
    service: CycleService = Depends(get_cycle_service),
) -> CurrentCycleResponse:
    try:
        return await service.get_current(current_user)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="no_cycle_data") from exc


@router.get("/calendar", response_model=CalendarResponse)
@limiter.limit("60/minute")
async def get_calendar(
    request: Request,
    year: int,
    month: int,
    current_user: User = Depends(get_current_user),
    service: CycleService = Depends(get_cycle_service),
) -> CalendarResponse:
    if not (1 <= month <= 12):
        raise HTTPException(status_code=422, detail="invalid_month")
    return await service.get_calendar(current_user, year, month)


@router.post("/symptoms", response_model=SymptomLogPublic)
@limiter.limit("60/minute")
async def log_symptoms(
    request: Request,
    data: SymptomLogCreate,
    current_user: User = Depends(get_current_user),
    service: CycleService = Depends(get_cycle_service),
) -> SymptomLogPublic:
    return await service.log_symptoms(current_user, data)


@router.get("/symptoms", response_model=list[SymptomLogPublic])
@limiter.limit("60/minute")
async def list_symptoms(
    request: Request,
    params: SymptomFilterParams = Depends(),
    current_user: User = Depends(get_current_user),
    service: CycleService = Depends(get_cycle_service),
) -> list[SymptomLogPublic]:
    return await service.list_symptoms(current_user, params)


@router.get("/insights", response_model=CycleInsightsResponse)
@limiter.limit("20/hour")
async def get_insights(
    request: Request,
    current_user: User = Depends(require_bloom),
    service: CycleService = Depends(get_cycle_service),
) -> CycleInsightsResponse:
    return await service.get_insights(current_user)


@router.get("/export/pdf")
@limiter.limit("5/day")
async def export_pdf(
    request: Request,
    current_user: User = Depends(require_bloom_pro),
    service: CycleService = Depends(get_cycle_service),
) -> Response:
    pdf_bytes = await service.export_pdf(current_user)
    filename = f"flornya_cycle_{current_user.id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
