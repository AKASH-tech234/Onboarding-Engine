"""
app/db/redis_client.py

Redis client factory with in-memory fallback for local/test environments.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from time import time
from typing import Any

try:
    from config.settings import get_settings
except ImportError:  # pragma: no cover - alternate package root
    from app.config.settings import get_settings


@dataclass
class _MemRedis:
    _values: dict[str, tuple[str, float | None]] = field(default_factory=dict)

    async def get(self, key: str) -> str | None:
        record = self._values.get(key)
        if record is None:
            return None
        value, expires_at = record
        if expires_at is not None and expires_at < time():
            self._values.pop(key, None)
            return None
        return value

    async def set(self, key: str, value: str, ex: int | None = None) -> bool:
        expires_at = None if ex is None else time() + max(1, int(ex))
        self._values[key] = (str(value), expires_at)
        return True

    async def delete(self, key: str) -> int:
        return 1 if self._values.pop(key, None) is not None else 0

    async def ping(self) -> bool:
        return True

    async def close(self) -> None:
        self._values.clear()


_LOCK = Lock()
_CLIENT: Any = None


def get_redis():
    global _CLIENT
    if _CLIENT is not None:
        return _CLIENT

    with _LOCK:
        if _CLIENT is not None:
            return _CLIENT

        settings = get_settings()
        redis_url = settings.redis_url

        if redis_url:
            try:
                import redis.asyncio as redis  # type: ignore

                _CLIENT = redis.from_url(redis_url, decode_responses=True)
                return _CLIENT
            except Exception:
                pass

        _CLIENT = _MemRedis()
        return _CLIENT


async def close_redis() -> None:
    global _CLIENT
    client = _CLIENT
    _CLIENT = None
    if client is None:
        return
    close_fn = getattr(client, "close", None)
    if callable(close_fn):
        maybe_awaitable = close_fn()
        if hasattr(maybe_awaitable, "__await__"):
            await maybe_awaitable


__all__ = ["get_redis", "close_redis"]
