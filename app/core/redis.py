from __future__ import annotations

import time
from fnmatch import fnmatch
from typing import Any

from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError

from app.config import get_settings

settings = get_settings()

_real_redis_client: Redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)


class _InMemoryRedis:
    def __init__(self) -> None:
        self._store: dict[str, tuple[str, float | None]] = {}

    def _now(self) -> float:
        return time.time()

    def _get_entry(self, key: str) -> tuple[str, float | None] | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if expires_at is not None and expires_at <= self._now():
            self._store.pop(key, None)
            return None
        return value, expires_at

    async def get(self, key: str) -> str | None:
        entry = self._get_entry(key)
        return entry[0] if entry is not None else None

    async def set(self, key: str, value: Any, ex: int | None = None) -> bool:
        expires_at = self._now() + ex if ex is not None else None
        self._store[key] = (str(value), expires_at)
        return True

    async def exists(self, key: str) -> int:
        return 1 if self._get_entry(key) is not None else 0

    async def incr(self, key: str) -> int:
        entry = self._get_entry(key)
        current = 0
        expires_at: float | None = None
        if entry is not None:
            value_s, expires_at = entry
            try:
                current = int(value_s)
            except ValueError:
                current = 0
        current += 1
        self._store[key] = (str(current), expires_at)
        return current

    async def expire(self, key: str, seconds: int) -> bool:
        entry = self._get_entry(key)
        if entry is None:
            return False
        value, _ = entry
        self._store[key] = (value, self._now() + seconds)
        return True

    async def delete(self, *keys: str) -> int:
        removed = 0
        for key in keys:
            if key in self._store:
                self._store.pop(key, None)
                removed += 1
        return removed

    async def scan(
        self, *, cursor: int = 0, match: str | None = None, count: int = 10
    ) -> tuple[int, list[str]]:
        keys = []
        for k in list(self._store.keys()):
            if self._get_entry(k) is None:
                continue
            if match is None or fnmatch(k, match):
                keys.append(k)
        keys.sort()
        start = int(cursor or 0)
        batch = keys[start : start + count]
        next_cursor = 0 if start + count >= len(keys) else start + count
        return next_cursor, batch


_fallback_redis_client = _InMemoryRedis()


class RedisClientProxy:
    def __init__(self, real_client: Redis, fallback_client: _InMemoryRedis) -> None:
        self._real = real_client
        self._fallback = fallback_client

    async def get(self, key: str) -> str | None:
        try:
            return await self._real.get(key)
        except RedisConnectionError:
            return await self._fallback.get(key)

    async def set(self, key: str, value: Any, ex: int | None = None) -> bool:
        try:
            result = await self._real.set(key, value, ex=ex)
            return bool(result)
        except RedisConnectionError:
            return await self._fallback.set(key, value, ex=ex)

    async def exists(self, key: str) -> int:
        try:
            return int(await self._real.exists(key))
        except RedisConnectionError:
            return await self._fallback.exists(key)

    async def incr(self, key: str) -> int:
        try:
            return int(await self._real.incr(key))
        except RedisConnectionError:
            return await self._fallback.incr(key)

    async def expire(self, key: str, seconds: int) -> bool:
        try:
            return bool(await self._real.expire(key, seconds))
        except RedisConnectionError:
            return await self._fallback.expire(key, seconds)

    async def delete(self, *keys: str) -> int:
        try:
            return int(await self._real.delete(*keys))
        except RedisConnectionError:
            return await self._fallback.delete(*keys)

    async def scan(
        self, *, cursor: int = 0, match: str | None = None, count: int = 10
    ) -> tuple[int, list[str]]:
        try:
            new_cursor, keys = await self._real.scan(cursor=cursor, match=match, count=count)
            if isinstance(new_cursor, (bytes, str)):
                new_cursor = int(new_cursor)
            keys_s = [k.decode() if isinstance(k, bytes) else str(k) for k in keys]
            return int(new_cursor), keys_s
        except RedisConnectionError:
            return await self._fallback.scan(cursor=cursor, match=match, count=count)


redis_client = RedisClientProxy(_real_redis_client, _fallback_redis_client)


async def get_redis() -> RedisClientProxy:
    return redis_client
