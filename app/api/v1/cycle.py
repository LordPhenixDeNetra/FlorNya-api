from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.deps import get_current_user, get_cycle_service
from app.core.middleware import limiter
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.cycle import CurrentCycleResponse, CycleFilterParams, CycleRecordCreate, CycleRecordPublic
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
