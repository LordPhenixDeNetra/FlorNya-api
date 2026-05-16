from fastapi import APIRouter, Depends, Request

from app.api.deps import get_current_user, get_dashboard_service
from app.core.middleware import limiter
from app.models.user import User
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("", response_model=DashboardResponse)
@limiter.limit("60/minute")
async def get_dashboard(
    request: Request,
    current_user: User = Depends(get_current_user),
    service: DashboardService = Depends(get_dashboard_service),
) -> DashboardResponse:
    return await service.get_dashboard(current_user)
