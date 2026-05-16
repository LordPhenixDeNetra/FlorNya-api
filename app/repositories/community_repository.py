from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.community_post import CommunityPost
from app.models.community_recipe import CommunityRecipe


class CommunityPostRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        user_id: UUID,
        title_encrypted: str,
        body_encrypted: str,
        category: str,
        anonymous_display_name: str | None = None,
    ) -> CommunityPost:
        post = CommunityPost(
            user_id=user_id,
            title_encrypted=title_encrypted,
            body_encrypted=body_encrypted,
            category=category,
            anonymous_display_name=anonymous_display_name,
        )
        self.session.add(post)
        return post

    async def list_approved(
        self,
        category: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[CommunityPost]:
        q = select(CommunityPost).where(CommunityPost.is_approved == True)  # noqa: E712
        if category:
            q = q.where(CommunityPost.category == category)
        q = q.order_by(CommunityPost.is_pinned.desc(), CommunityPost.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def get_by_id(self, post_id: UUID) -> CommunityPost | None:
        result = await self.session.execute(select(CommunityPost).where(CommunityPost.id == post_id))
        return result.scalar_one_or_none()

    async def increment_likes(self, post_id: UUID) -> None:
        post = await self.get_by_id(post_id)
        if post:
            post.likes_count += 1

    async def list_by_user(self, user_id: UUID, limit: int = 20) -> list[CommunityPost]:
        result = await self.session.execute(
            select(CommunityPost)
            .where(CommunityPost.user_id == user_id)
            .order_by(CommunityPost.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class CommunityRecipeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, user_id: UUID, **kwargs) -> CommunityRecipe:
        recipe = CommunityRecipe(user_id=user_id, **kwargs)
        self.session.add(recipe)
        return recipe

    async def list_approved(
        self,
        phase: str | None = None,
        cultural_cuisine: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[CommunityRecipe]:
        q = select(CommunityRecipe).where(CommunityRecipe.is_approved == True)  # noqa: E712
        if phase:
            q = q.where(CommunityRecipe.phase == phase)
        if cultural_cuisine:
            q = q.where(CommunityRecipe.cultural_cuisine == cultural_cuisine)
        q = q.order_by(CommunityRecipe.likes_count.desc(), CommunityRecipe.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def get_by_id(self, recipe_id: UUID) -> CommunityRecipe | None:
        result = await self.session.execute(select(CommunityRecipe).where(CommunityRecipe.id == recipe_id))
        return result.scalar_one_or_none()

    async def increment_likes(self, recipe_id: UUID) -> None:
        recipe = await self.get_by_id(recipe_id)
        if recipe:
            recipe.likes_count += 1

    async def update_nutrition_score(self, recipe_id: UUID, score: int) -> None:
        recipe = await self.get_by_id(recipe_id)
        if recipe:
            recipe.nutrition_score = score
