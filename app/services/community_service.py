import json
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_sensitive, encrypt_sensitive
from app.models.challenge import Challenge, UserChallenge
from app.models.community_post import CommunityPost
from app.models.community_recipe import CommunityRecipe
from app.models.user import User
from app.repositories.challenge_repository import ChallengeRepository, UserChallengeRepository
from app.repositories.community_repository import CommunityPostRepository, CommunityRecipeRepository
from app.schemas.community import (
    ChallengePublic,
    CommunityPostCreate,
    CommunityPostPublic,
    CommunityRecipeCreate,
    CommunityRecipePublic,
    UserChallengePublic,
)
from app.services.ai.anthropic_service import AnthropicInsightService


class CommunityService:
    def __init__(
        self,
        session: AsyncSession,
        posts_repo: CommunityPostRepository,
        recipes_repo: CommunityRecipeRepository,
        challenges_repo: ChallengeRepository,
        user_challenges_repo: UserChallengeRepository,
        ai_service: AnthropicInsightService | None = None,
    ):
        self.session = session
        self.posts_repo = posts_repo
        self.recipes_repo = recipes_repo
        self.challenges_repo = challenges_repo
        self.user_challenges_repo = user_challenges_repo
        self.ai_service = ai_service

    # ── Posts ─────────────────────────────────────────────────────────────

    async def create_post(self, user: User, data: CommunityPostCreate) -> CommunityPostPublic:
        is_approved = True
        if self.ai_service:
            result = await self.ai_service.moderate_community_post(data.title, data.body, user.language)
            is_approved = result["approved"]

        post = await self.posts_repo.create(
            user_id=user.id,
            title_encrypted=encrypt_sensitive(data.title),
            body_encrypted=encrypt_sensitive(data.body),
            category=data.category,
            anonymous_display_name=data.anonymous_display_name,
        )
        post.is_moderated = True
        post.is_approved = is_approved
        await self.session.commit()
        await self.session.refresh(post)
        return self._post_to_public(post, user.id)

    async def list_posts(
        self, user: User, category: str | None = None, limit: int = 20, offset: int = 0
    ) -> list[CommunityPostPublic]:
        posts = await self.posts_repo.list_approved(category=category, limit=limit, offset=offset)
        return [self._post_to_public(p, user.id) for p in posts]

    async def like_post(self, user: User, post_id: UUID) -> None:
        await self.posts_repo.increment_likes(post_id)
        await self.session.commit()

    async def list_my_posts(self, user: User) -> list[CommunityPostPublic]:
        posts = await self.posts_repo.list_by_user(user.id)
        return [self._post_to_public(p, user.id) for p in posts]

    # ── Recipes ───────────────────────────────────────────────────────────

    async def share_recipe(self, user: User, data: CommunityRecipeCreate) -> CommunityRecipePublic:
        ingredients_json = json.dumps(data.ingredients, ensure_ascii=False)

        nutrition_score: int | None = None
        if self.ai_service:
            nutrition_score = await self.ai_service.score_community_recipe(
                data.title, data.ingredients, data.phase, user.language
            )

        recipe = await self.recipes_repo.create(
            user_id=user.id,
            title=data.title,
            description_encrypted=encrypt_sensitive(data.description),
            ingredients_encrypted=encrypt_sensitive(ingredients_json),
            instructions_encrypted=encrypt_sensitive(data.instructions),
            phase=data.phase,
            cultural_cuisine=data.cultural_cuisine,
            prep_time_minutes=data.prep_time_minutes,
            nutrition_score=nutrition_score,
        )
        await self.session.commit()
        await self.session.refresh(recipe)
        return self._recipe_to_public(recipe, user.id)

    async def list_recipes(
        self, user: User, phase: str | None = None, cultural_cuisine: str | None = None, limit: int = 20
    ) -> list[CommunityRecipePublic]:
        recipes = await self.recipes_repo.list_approved(phase=phase, cultural_cuisine=cultural_cuisine, limit=limit)
        return [self._recipe_to_public(r, user.id) for r in recipes]

    async def like_recipe(self, user: User, recipe_id: UUID) -> None:
        await self.recipes_repo.increment_likes(recipe_id)
        await self.session.commit()

    # ── Challenges ────────────────────────────────────────────────────────

    async def list_challenges(self, category: str | None = None) -> list[ChallengePublic]:
        challenges = await self.challenges_repo.list_active(category=category)
        return [self._challenge_to_public(c) for c in challenges]

    async def enroll_challenge(self, user: User, challenge_id: UUID) -> UserChallengePublic:
        challenge = await self.challenges_repo.get_by_id(challenge_id)
        if challenge is None:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="challenge_not_found")

        uc = await self.user_challenges_repo.enroll(user.id, challenge_id)
        await self.challenges_repo.increment_participants(challenge_id)
        await self.session.commit()
        await self.session.refresh(uc)
        return self._user_challenge_to_public(uc, challenge)

    async def update_challenge_progress(self, user: User, challenge_id: UUID, progress_days: int) -> UserChallengePublic:
        uc = await self.user_challenges_repo.update_progress(user.id, challenge_id, progress_days)
        if uc is None:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="enrollment_not_found")
        challenge = await self.challenges_repo.get_by_id(challenge_id)
        await self.session.commit()
        return self._user_challenge_to_public(uc, challenge)

    async def list_my_challenges(self, user: User) -> list[UserChallengePublic]:
        user_challenges = await self.user_challenges_repo.list_user_challenges(user.id)
        result = []
        for uc in user_challenges:
            challenge = await self.challenges_repo.get_by_id(uc.challenge_id)
            if challenge:
                result.append(self._user_challenge_to_public(uc, challenge))
        return result

    # ── Converters ────────────────────────────────────────────────────────

    def _post_to_public(self, post: CommunityPost, viewer_id: UUID) -> CommunityPostPublic:
        return CommunityPostPublic(
            id=post.id,
            category=post.category.value,
            title=decrypt_sensitive(post.title_encrypted) or "",
            body=decrypt_sensitive(post.body_encrypted) or "",
            anonymous_display_name=post.anonymous_display_name,
            is_pinned=post.is_pinned,
            likes_count=post.likes_count,
            comments_count=post.comments_count,
            created_at=post.created_at,
            is_own=post.user_id == viewer_id,
        )

    def _recipe_to_public(self, recipe: CommunityRecipe, viewer_id: UUID) -> CommunityRecipePublic:
        ingredients_raw = decrypt_sensitive(recipe.ingredients_encrypted)
        try:
            ingredients = json.loads(ingredients_raw) if ingredients_raw else []
        except (json.JSONDecodeError, TypeError):
            ingredients = []
        return CommunityRecipePublic(
            id=recipe.id,
            user_id=recipe.user_id,
            title=recipe.title,
            description=decrypt_sensitive(recipe.description_encrypted),
            ingredients=ingredients,
            instructions=decrypt_sensitive(recipe.instructions_encrypted),
            phase=recipe.phase,
            cultural_cuisine=recipe.cultural_cuisine,
            prep_time_minutes=recipe.prep_time_minutes,
            nutrition_score=recipe.nutrition_score,
            likes_count=recipe.likes_count,
            created_at=recipe.created_at,
            is_own=recipe.user_id == viewer_id,
        )

    def _challenge_to_public(self, c: Challenge) -> ChallengePublic:
        return ChallengePublic(
            id=c.id,
            title=c.title,
            description=c.description,
            category=c.category,
            duration_days=c.duration_days,
            badge_icon=c.badge_icon,
            is_active=c.is_active,
            participants_count=c.participants_count,
            start_date=str(c.start_date) if c.start_date else None,
            end_date=str(c.end_date) if c.end_date else None,
        )

    def _user_challenge_to_public(self, uc: UserChallenge, challenge: Challenge | None) -> UserChallengePublic:
        duration = challenge.duration_days if challenge else 1
        return UserChallengePublic(
            id=uc.id,
            challenge_id=uc.challenge_id,
            challenge_title=challenge.title if challenge else "Défi",
            enrolled_at=uc.enrolled_at,
            completed_at=uc.completed_at,
            progress_days=uc.progress_days,
            is_completed=uc.is_completed,
            progress_pct=round(min(100.0, (uc.progress_days / duration) * 100), 1),
        )
