"""
app/api/middlewares/rate_limit_middleware.py

In-memory per-client sliding-window rate limit middleware.
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from time import time
from typing import Any

try:
    from api._compat import FASTAPI_AVAILABLE, JSONResponse
except ImportError:  # pragma: no cover - alternate package root
    from app.api._compat import FASTAPI_AVAILABLE, JSONResponse

try:
    from config.settings import get_settings
except ImportError:  # pragma: no cover - alternate package root
    from app.config.settings import get_settings


WINDOW_SECONDS = 60


@dataclass
class _RateWindow:
    started_at: float
    count: int


_LOCK = Lock()
_WINDOWS: dict[str, _RateWindow] = {}


def install_middleware(app: Any) -> None:
    if not FASTAPI_AVAILABLE or not hasattr(app, "middleware"):
        return

    @app.middleware("http")
    async def _rate_limit_middleware(request, call_next):  # type: ignore[no-untyped-def]
        settings = get_settings()
        if not settings.rate_limit_enabled:
            return await call_next(request)

        limit = max(1, int(settings.rate_limit_per_minute))
        key = _client_key(request)
        allowed, retry_after, remaining = _check_and_consume(key=key, limit=limit)

        if not allowed:
            return JSONResponse(
                {"error": "Rate limit exceeded", "retry_after_seconds": retry_after},
                status_code=429,
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        return response


def _check_and_consume(*, key: str, limit: int) -> tuple[bool, int, int]:
    now = time()
    with _LOCK:
        window = _WINDOWS.get(key)
        if window is None or now - window.started_at >= WINDOW_SECONDS:
            window = _RateWindow(started_at=now, count=0)
            _WINDOWS[key] = window

        if window.count >= limit:
            retry_after = max(1, int(WINDOW_SECONDS - (now - window.started_at)))
            return False, retry_after, 0

        window.count += 1
        remaining = limit - window.count
        return True, 0, remaining


def _client_key(request: Any) -> str:
    forwarded = str(request.headers.get("x-forwarded-for", "")).strip()
    if forwarded:
        return forwarded.split(",")[0].strip()
    client = getattr(request, "client", None)
    host = getattr(client, "host", None) if client else None
    return str(host or "unknown")


__all__ = ["install_middleware"]
