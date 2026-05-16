from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.deps import get_current_user, get_reminder_service
from app.core.middleware import limiter
from app.models.user import User
from app.schemas.reminder import ReminderConfigCreate, ReminderConfigPublic, ReminderType
from app.services.reminder_service import ReminderService

router = APIRouter()


@router.get("", response_model=list[ReminderConfigPublic])
@limiter.limit("60/minute")
async def list_reminders(
    request: Request,
    current_user: User = Depends(get_current_user),
    service: ReminderService = Depends(get_reminder_service),
) -> list[ReminderConfigPublic]:
    return await service.list_reminders(current_user)


@router.put("/{reminder_type}", response_model=ReminderConfigPublic)
@limiter.limit("30/minute")
async def upsert_reminder(
    request: Request,
    reminder_type: ReminderType,
    data: ReminderConfigCreate,
    current_user: User = Depends(get_current_user),
    service: ReminderService = Depends(get_reminder_service),
) -> ReminderConfigPublic:
    return await service.upsert_reminder(current_user, reminder_type, data)


@router.delete("/{reminder_type}", status_code=204)
@limiter.limit("30/minute")
async def delete_reminder(
    request: Request,
    reminder_type: ReminderType,
    current_user: User = Depends(get_current_user),
    service: ReminderService = Depends(get_reminder_service),
) -> None:
    try:
        await service.delete_reminder(current_user, reminder_type)
    except ValueError:
        raise HTTPException(status_code=404, detail="reminder_not_found")
