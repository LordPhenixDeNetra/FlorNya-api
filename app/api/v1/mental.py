from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.deps import get_current_user, get_mental_service, require_bloom
from app.core.middleware import limiter
from app.models.user import User
from app.schemas.common import CursorPaginatedResponse
from app.schemas.mental import (
    EmotionalJournalCreate,
    EmotionalJournalPublic,
    MentalAlertPublic,
    MentalInsightsResponse,
    MentalResourcePublic,
    MoodCorrelationResponse,
    MoodFilterParams,
    MoodLogCreate,
    MoodLogPublic,
    SPMDetectionResult,
    StressTechniquePublic,
)
from app.services.mental_service import MentalService

router = APIRouter()


@router.post("/mood", response_model=MoodLogPublic)
@limiter.limit("60/minute")
async def create_mood(
    request: Request,
    data: MoodLogCreate,
    current_user: User = Depends(get_current_user),
    service: MentalService = Depends(get_mental_service),
) -> MoodLogPublic:
    return await service.create_mood(current_user, data)


@router.get("/moods", response_model=CursorPaginatedResponse[MoodLogPublic])
@limiter.limit("60/minute")
async def list_moods(
    request: Request,
    params: MoodFilterParams = Depends(),
    current_user: User = Depends(get_current_user),
    service: MentalService = Depends(get_mental_service),
) -> CursorPaginatedResponse[MoodLogPublic]:
    return await service.list_moods(current_user, params)


@router.post("/journal", response_model=EmotionalJournalPublic)
@limiter.limit("60/minute")
async def add_journal_entry(
    request: Request,
    data: EmotionalJournalCreate,
    current_user: User = Depends(require_bloom),
    service: MentalService = Depends(get_mental_service),
) -> EmotionalJournalPublic:
    return await service.add_journal_entry(current_user, data)


@router.get("/journal", response_model=list[EmotionalJournalPublic])
@limiter.limit("60/minute")
async def list_journal_entries(
    request: Request,
    limit: int = 30,
    offset: int = 0,
    current_user: User = Depends(require_bloom),
    service: MentalService = Depends(get_mental_service),
) -> list[EmotionalJournalPublic]:
    return await service.list_journal_entries(current_user, limit=limit, offset=offset)


@router.get("/journal/prompt", response_model=dict)
@limiter.limit("30/minute")
async def get_journal_prompt(
    request: Request,
    mood_score: int = 3,
    cycle_phase: str = "follicular",
    current_user: User = Depends(require_bloom),
    service: MentalService = Depends(get_mental_service),
) -> dict:
    if not 1 <= mood_score <= 5:
        raise HTTPException(status_code=422, detail="mood_score_must_be_1_to_5")
    prompt = await service.get_ai_journal_prompt(current_user, mood_score, cycle_phase)
    return {"prompt": prompt}


@router.get("/stress-techniques", response_model=list[StressTechniquePublic])
@limiter.limit("60/minute")
async def get_stress_techniques(
    request: Request,
    phase: str | None = None,
    current_user: User = Depends(require_bloom),
    service: MentalService = Depends(get_mental_service),
) -> list[StressTechniquePublic]:
    return service.get_stress_techniques(phase=phase)


@router.get("/mood-correlation", response_model=MoodCorrelationResponse)
@limiter.limit("20/hour")
async def get_mood_correlation(
    request: Request,
    current_user: User = Depends(require_bloom),
    service: MentalService = Depends(get_mental_service),
) -> MoodCorrelationResponse:
    return await service.get_mood_correlation(current_user)


@router.get("/spm-detection", response_model=SPMDetectionResult)
@limiter.limit("10/hour")
async def detect_spm(
    request: Request,
    current_user: User = Depends(require_bloom),
    service: MentalService = Depends(get_mental_service),
) -> SPMDetectionResult:
    return await service.detect_spm(current_user)


@router.get("/insights", response_model=MentalInsightsResponse)
@limiter.limit("20/hour")
async def get_emotional_insights(
    request: Request,
    current_user: User = Depends(require_bloom),
    service: MentalService = Depends(get_mental_service),
) -> MentalInsightsResponse:
    return await service.get_emotional_insights(current_user)


@router.get("/alerts", response_model=list[MentalAlertPublic])
@limiter.limit("60/minute")
async def get_mental_alerts(
    request: Request,
    current_user: User = Depends(get_current_user),
    service: MentalService = Depends(get_mental_service),
) -> list[MentalAlertPublic]:
    return await service.get_mental_alerts(current_user)


@router.patch("/alerts/{alert_id}/resolve", response_model=dict)
@limiter.limit("60/minute")
async def resolve_alert(
    request: Request,
    alert_id: UUID,
    current_user: User = Depends(get_current_user),
    service: MentalService = Depends(get_mental_service),
) -> dict:
    await service.resolve_alert(current_user, alert_id)
    return {"status": "resolved"}


@router.get("/resources", response_model=list[MentalResourcePublic])
@limiter.limit("60/minute")
async def get_mental_resources(
    request: Request,
    current_user: User = Depends(get_current_user),
    service: MentalService = Depends(get_mental_service),
) -> list[MentalResourcePublic]:
    return service.get_mental_resources()
