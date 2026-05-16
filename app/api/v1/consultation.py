from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response

from app.api.deps import get_consultation_service, require_bloom, require_bloom_pro
from app.core.middleware import limiter
from app.models.user import User
from app.schemas.consultation import (
    ConsultationBookingCreate,
    ConsultationBookingPublic,
    ConsultationPrepResponse,
    MonthlyReportRequest,
)
from app.services.consultation_service import ConsultationService

router = APIRouter()


@router.post("/book", response_model=ConsultationBookingPublic)
@limiter.limit("10/hour")
async def book_consultation(
    request: Request,
    data: ConsultationBookingCreate,
    current_user: User = Depends(require_bloom_pro),
    service: ConsultationService = Depends(get_consultation_service),
) -> ConsultationBookingPublic:
    return await service.book_consultation(current_user, data)


@router.get("/bookings", response_model=list[ConsultationBookingPublic])
@limiter.limit("60/minute")
async def list_consultations(
    request: Request,
    current_user: User = Depends(require_bloom_pro),
    service: ConsultationService = Depends(get_consultation_service),
) -> list[ConsultationBookingPublic]:
    return await service.list_consultations(current_user)


@router.get("/preparation", response_model=ConsultationPrepResponse)
@limiter.limit("10/hour")
async def get_consultation_prep(
    request: Request,
    current_user: User = Depends(require_bloom_pro),
    service: ConsultationService = Depends(get_consultation_service),
) -> ConsultationPrepResponse:
    return await service.get_consultation_prep(current_user)


@router.post("/monthly-report/pdf")
@limiter.limit("5/day")
async def generate_monthly_report(
    request: Request,
    data: MonthlyReportRequest,
    current_user: User = Depends(require_bloom_pro),
    service: ConsultationService = Depends(get_consultation_service),
) -> Response:
    pdf_bytes = await service.generate_monthly_pdf(current_user, data.year, data.month)
    filename = f"flornya-rapport-mensuel-{data.year}-{data.month:02d}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/support-info", response_model=dict)
@limiter.limit("60/minute")
async def get_support_info(
    request: Request,
    current_user: User = Depends(require_bloom_pro),
) -> dict:
    return {
        "support_email": "support@flornya.app",
        "priority_queue": True,
        "response_time_hours": 2,
        "availability": "24/7",
        "channels": ["email", "chat_in_app"],
    }
