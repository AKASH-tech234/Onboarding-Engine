"""
app/api/middlewares/auth_middleware.py

Simple token-based auth middleware for protected deployments.
"""

from __future__ import annotations

from typing import Any

try:
    from api._compat import FASTAPI_AVAILABLE, JSONResponse
except ImportError:  # pragma: no cover - alternate package root
    from app.api._compat import FASTAPI_AVAILABLE, JSONResponse

try:
    from config.settings import get_settings
except ImportError:  # pragma: no cover - alternate package root
    from app.config.settings import get_settings


def install_middleware(app: Any) -> None:
    if not FASTAPI_AVAILABLE or not hasattr(app, "middleware"):
        return

    @app.middleware("http")
    async def _auth_middleware(request, call_next):  # type: ignore[no-untyped-def]
        settings = get_settings()
        if not settings.auth_enabled:
            return await call_next(request)

        expected_token = (settings.api_auth_token or "").strip()
        if not expected_token:
            return JSONResponse(
                {"error": "Auth is enabled but no API token is configured."},
                status_code=500,
            )

        provided = _extract_token(request)
        if provided != expected_token:
            return JSONResponse({"error": "Unauthorized"}, status_code=401)

        request.state.authenticated = True
        return await call_next(request)


def _extract_token(request: Any) -> str:
    auth_header = str(request.headers.get("authorization", "")).strip()
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()
    return str(request.headers.get("x-api-key", "")).strip()


__all__ = ["install_middleware"]
