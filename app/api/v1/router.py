from fastapi import APIRouter

from app.api.v1 import (
    admin,
    auth,
    bot,
    chat,
    community,
    consultation,
    cycle,
    dashboard,
    fertility,
    hormonal_health,
    intimate,
    mental,
    menopause,
    nutrition,
    payments,
    pregnancy,
    reminders,
    users,
)

api_router = APIRouter()

# Phase 1
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(cycle.router, prefix="/cycle", tags=["cycle"])
api_router.include_router(mental.router, prefix="/mental", tags=["mental"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(reminders.router, prefix="/reminders", tags=["reminders"])

# Phase 2
api_router.include_router(fertility.router, prefix="/fertility", tags=["fertility"])
api_router.include_router(pregnancy.router, prefix="/pregnancy", tags=["pregnancy"])
api_router.include_router(hormonal_health.router, prefix="/hormonal-health", tags=["hormonal-health"])
api_router.include_router(menopause.router, prefix="/menopause", tags=["menopause"])
api_router.include_router(nutrition.router, prefix="/nutrition", tags=["nutrition"])

# Phase 3
api_router.include_router(intimate.router, prefix="/intimate", tags=["intimate"])
api_router.include_router(community.router, prefix="/community", tags=["community"])
api_router.include_router(consultation.router, prefix="/consultation", tags=["consultation"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])

# Extras — Bot webhooks
api_router.include_router(bot.router, prefix="/bot", tags=["bot"])

# Admin (X-Admin-Key required)
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
