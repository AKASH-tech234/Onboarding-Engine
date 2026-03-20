"""
app/api/middlewares/request_id_middleware.py

Injects a request id into request state, logger context, and response headers.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

try:
    from api._compat import FASTAPI_AVAILABLE
except ImportError:  # pragma: no cover - alternate package root
    from app.api._compat import FASTAPI_AVAILABLE

try:
    from utils.logger import clear_request_id, set_request_id
except ImportError:  # pragma: no cover - alternate package root
    from app.utils.logger import clear_request_id, set_request_id


REQUEST_ID_HEADER = "X-Request-ID"


def install_middleware(app: Any) -> None:
    if not FASTAPI_AVAILABLE or not hasattr(app, "middleware"):
        return

    @app.middleware("http")
    async def _request_id_middleware(request, call_next):  # type: ignore[no-untyped-def]
        incoming = request.headers.get(REQUEST_ID_HEADER, "")
        request_id = incoming.strip() or str(uuid4())

        request.state.request_id = request_id
        set_request_id(request_id)
        try:
            response = await call_next(request)
        finally:
            clear_request_id()

        response.headers[REQUEST_ID_HEADER] = request_id
        return response


__all__ = ["REQUEST_ID_HEADER", "install_middleware"]
