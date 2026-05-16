import structlog
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.database import get_async_session
from app.core.middleware import limiter
from app.models.user import User, UserPlan
from app.schemas.user import UserPublic, UserPlan as PlanSchema

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/users", response_model=list[dict])
@limiter.limit("30/minute")
async def list_users(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    _: None = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
) -> list[dict]:
    result = await session.execute(
        select(User).where(User.deleted_at.is_(None)).offset(skip).limit(limit)
    )
    users = result.scalars().all()
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "plan": u.plan.value,
            "beta_access": u.beta_access,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat(),
        }
        for u in users
    ]


@router.patch("/users/{user_id}/plan", response_model=dict)
@limiter.limit("30/minute")
async def set_user_plan(
    request: Request,
    user_id: UUID,
    plan: PlanSchema,
    _: None = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="user_not_found")
    old_plan = user.plan.value
    user.plan = UserPlan(plan.value)
    await session.commit()
    logger.info("admin.set_plan", user_id=str(user_id), old_plan=old_plan, new_plan=user.plan.value)
    return {"id": str(user.id), "plan": user.plan.value}


@router.patch("/users/{user_id}/beta", response_model=dict)
@limiter.limit("30/minute")
async def set_user_beta(
    request: Request,
    user_id: UUID,
    enabled: bool = True,
    _: None = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="user_not_found")
    user.beta_access = enabled
    await session.commit()
    logger.info("admin.set_beta", user_id=str(user_id), beta_access=enabled)
    return {"id": str(user.id), "beta_access": user.beta_access}


@router.delete("/users/{user_id}", status_code=204)
@limiter.limit("10/minute")
async def hard_delete_user(
    request: Request,
    user_id: UUID,
    _: None = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
) -> None:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="user_not_found")
    await session.delete(user)
    await session.commit()
    logger.warning("admin.hard_delete_user", user_id=str(user_id))
