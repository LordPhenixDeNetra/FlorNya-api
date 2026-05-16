from uuid import UUID

from fastapi import APIRouter, Depends, Request

from app.api.deps import get_community_service, require_bloom
from app.core.middleware import limiter
from app.models.user import User
from app.schemas.community import (
    ChallengePublic,
    CommunityPostCreate,
    CommunityPostPublic,
    CommunityRecipeCreate,
    CommunityRecipePublic,
    UserChallengePublic,
)
from app.services.community_service import CommunityService

router = APIRouter()


# ── Posts ─────────────────────────────────────────────────────────────────────

@router.post("/posts", response_model=CommunityPostPublic)
@limiter.limit("10/minute")
async def create_post(
    request: Request,
    data: CommunityPostCreate,
    current_user: User = Depends(require_bloom),
    service: CommunityService = Depends(get_community_service),
) -> CommunityPostPublic:
    return await service.create_post(current_user, data)


@router.get("/posts", response_model=list[CommunityPostPublic])
@limiter.limit("60/minute")
async def list_posts(
    request: Request,
    category: str | None = None,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(require_bloom),
    service: CommunityService = Depends(get_community_service),
) -> list[CommunityPostPublic]:
    return await service.list_posts(current_user, category=category, limit=limit, offset=offset)


@router.post("/posts/{post_id}/like", response_model=dict)
@limiter.limit("60/minute")
async def like_post(
    request: Request,
    post_id: UUID,
    current_user: User = Depends(require_bloom),
    service: CommunityService = Depends(get_community_service),
) -> dict:
    await service.like_post(current_user, post_id)
    return {"status": "liked"}


@router.get("/posts/mine", response_model=list[CommunityPostPublic])
@limiter.limit("60/minute")
async def list_my_posts(
    request: Request,
    current_user: User = Depends(require_bloom),
    service: CommunityService = Depends(get_community_service),
) -> list[CommunityPostPublic]:
    return await service.list_my_posts(current_user)


# ── Recipes ───────────────────────────────────────────────────────────────────

@router.post("/recipes", response_model=CommunityRecipePublic)
@limiter.limit("10/minute")
async def share_recipe(
    request: Request,
    data: CommunityRecipeCreate,
    current_user: User = Depends(require_bloom),
    service: CommunityService = Depends(get_community_service),
) -> CommunityRecipePublic:
    return await service.share_recipe(current_user, data)


@router.get("/recipes", response_model=list[CommunityRecipePublic])
@limiter.limit("60/minute")
async def list_community_recipes(
    request: Request,
    phase: str | None = None,
    cultural_cuisine: str | None = None,
    limit: int = 20,
    current_user: User = Depends(require_bloom),
    service: CommunityService = Depends(get_community_service),
) -> list[CommunityRecipePublic]:
    return await service.list_recipes(current_user, phase=phase, cultural_cuisine=cultural_cuisine, limit=limit)


@router.post("/recipes/{recipe_id}/like", response_model=dict)
@limiter.limit("60/minute")
async def like_recipe(
    request: Request,
    recipe_id: UUID,
    current_user: User = Depends(require_bloom),
    service: CommunityService = Depends(get_community_service),
) -> dict:
    await service.like_recipe(current_user, recipe_id)
    return {"status": "liked"}


# ── Challenges ────────────────────────────────────────────────────────────────

@router.get("/challenges", response_model=list[ChallengePublic])
@limiter.limit("60/minute")
async def list_challenges(
    request: Request,
    category: str | None = None,
    current_user: User = Depends(require_bloom),
    service: CommunityService = Depends(get_community_service),
) -> list[ChallengePublic]:
    return await service.list_challenges(category=category)


@router.post("/challenges/{challenge_id}/enroll", response_model=UserChallengePublic)
@limiter.limit("20/hour")
async def enroll_challenge(
    request: Request,
    challenge_id: UUID,
    current_user: User = Depends(require_bloom),
    service: CommunityService = Depends(get_community_service),
) -> UserChallengePublic:
    return await service.enroll_challenge(current_user, challenge_id)


@router.patch("/challenges/{challenge_id}/progress", response_model=UserChallengePublic)
@limiter.limit("60/minute")
async def update_challenge_progress(
    request: Request,
    challenge_id: UUID,
    body: dict,
    current_user: User = Depends(require_bloom),
    service: CommunityService = Depends(get_community_service),
) -> UserChallengePublic:
    progress_days = int(body.get("progress_days", 0))
    return await service.update_challenge_progress(current_user, challenge_id, progress_days)


@router.get("/challenges/mine", response_model=list[UserChallengePublic])
@limiter.limit("60/minute")
async def list_my_challenges(
    request: Request,
    current_user: User = Depends(require_bloom),
    service: CommunityService = Depends(get_community_service),
) -> list[UserChallengePublic]:
    return await service.list_my_challenges(current_user)
