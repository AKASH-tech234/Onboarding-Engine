"""
app/api/middlewares/validate_middleware.py

Basic transport-level request validation middleware.
"""

from __future__ import annotations

import os
from typing import Any

try:
    from api._compat import FASTAPI_AVAILABLE, JSONResponse
except ImportError:  # pragma: no cover - alternate package root
    from app.api._compat import FASTAPI_AVAILABLE, JSONResponse


DEFAULT_MAX_BODY_BYTES = 2 * 1024 * 1024  # 2 MB


def install_middleware(app: Any) -> None:
    if not FASTAPI_AVAILABLE or not hasattr(app, "middleware"):
        return

    @app.middleware("http")
    async def _validate_middleware(request, call_next):  # type: ignore[no-untyped-def]
        max_bytes = _max_body_bytes()
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > max_bytes:
                    return JSONResponse(
                        {"error": f"Request body too large. Max bytes: {max_bytes}"},
                        status_code=413,
                    )
            except ValueError:
                return JSONResponse({"error": "Invalid Content-Length header."}, status_code=400)

        method = str(request.method).upper()
        if method in {"POST", "PUT", "PATCH"}:
            content_type = str(request.headers.get("content-type", "")).lower()
            if content_type and "application/json" not in content_type and "multipart/form-data" not in content_type:
                return JSONResponse(
                    {"error": "Unsupported Content-Type. Use application/json or multipart/form-data."},
                    status_code=415,
                )

        return await call_next(request)


def _max_body_bytes() -> int:
    raw = os.getenv("MAX_REQUEST_BODY_BYTES")
    try:
        if raw is None:
            return DEFAULT_MAX_BODY_BYTES
        return max(1024, int(raw))
    except (TypeError, ValueError):
        return DEFAULT_MAX_BODY_BYTES


__all__ = ["install_middleware"]
