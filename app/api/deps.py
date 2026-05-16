from uuid import UUID

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.database import get_async_session
from app.core.security import decode_token, is_adult
from app.models.user import User
from app.repositories.cycle_repository import CycleRepository
from app.repositories.female_profile_repository import FemaleProfileRepository
from app.repositories.mood_repository import MoodRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.cycle_service import CycleService
from app.services.mental_service import MentalService
from app.services.phase_calculator import PhaseCalculator
from app.services.user_service import UserService

settings = get_settings()

bearer = HTTPBearer(auto_error=False)


async def get_user_repository(session: AsyncSession = Depends(get_async_session)) -> UserRepository:
    return UserRepository(session)


async def get_female_profile_repository(
    session: AsyncSession = Depends(get_async_session),
) -> FemaleProfileRepository:
    return FemaleProfileRepository(session)


async def get_cycle_repository(session: AsyncSession = Depends(get_async_session)) -> CycleRepository:
    return CycleRepository(session)


async def get_mood_repository(session: AsyncSession = Depends(get_async_session)) -> MoodRepository:
    return MoodRepository(session)


async def get_auth_service(
    session: AsyncSession = Depends(get_async_session),
    users: UserRepository = Depends(get_user_repository),
) -> AuthService:
    return AuthService(session=session, users=users)


async def get_user_service(
    session: AsyncSession = Depends(get_async_session),
    users: UserRepository = Depends(get_user_repository),
    profiles: FemaleProfileRepository = Depends(get_female_profile_repository),
) -> UserService:
    return UserService(session=session, users=users, profiles=profiles)


async def get_phase_calculator() -> PhaseCalculator:
    return PhaseCalculator()


async def get_cycle_service(
    session: AsyncSession = Depends(get_async_session),
    cycles: CycleRepository = Depends(get_cycle_repository),
    calculator: PhaseCalculator = Depends(get_phase_calculator),
) -> CycleService:
    return CycleService(session=session, cycles=cycles, calculator=calculator)


async def get_mental_service(
    session: AsyncSession = Depends(get_async_session),
    moods: MoodRepository = Depends(get_mood_repository),
) -> MentalService:
    return MentalService(session=session, moods=moods)


async def get_current_user(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    users: UserRepository = Depends(get_user_repository),
) -> User:
    if creds is None:
        raise HTTPException(status_code=401, detail="missing_token")
    payload = decode_token(creds.credentials)
    if payload.get("typ") != "access":
        raise HTTPException(status_code=401, detail="invalid_token")
    sub = payload.get("sub")
    if not isinstance(sub, str):
        raise HTTPException(status_code=401, detail="invalid_token")
    user_id = UUID(sub)
    user = await users.get_active(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="invalid_token")
    request.state.user_id = str(user.id)
    return user


async def require_adult(current_user: User = Depends(get_current_user)) -> User:
    if not is_adult(current_user.date_of_birth):
        raise HTTPException(status_code=403, detail="adult_content_restricted")
    return current_user
