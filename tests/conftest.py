from collections.abc import AsyncGenerator

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import get_async_session
from app.models import Base


class FakeRedis:
    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self._store[key] = value

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def exists(self, key: str) -> int:
        return 1 if key in self._store else 0

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def incr(self, key: str) -> int:
        value = int(self._store.get(key, "0")) + 1
        self._store[key] = str(value)
        return value

    async def expire(self, key: str, seconds: int) -> None:
        return None


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
async def engine() -> AsyncGenerator:
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    session_maker = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
    async with session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session, monkeypatch) -> AsyncGenerator[AsyncClient, None]:
    from app.main import app
    import app.services.auth_service as auth_service_module
    import app.core.redis as redis_module

    fake_redis = FakeRedis()
    monkeypatch.setattr(auth_service_module, "redis_client", fake_redis)
    monkeypatch.setattr(redis_module, "redis_client", fake_redis)

    async def _override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_async_session] = _override_get_async_session
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
