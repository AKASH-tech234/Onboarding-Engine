"""
app/api/middlewares/error_handler_middleware.py

Global exception mapping middleware.
"""

from __future__ import annotations

from typing import Any

from app.adaptive.api._compat import FASTAPI_AVAILABLE, HTTPException, JSONResponse
from app.adaptive.config.settings import get_settings
from app.adaptive.utils.errors import GraphEngineError
from app.adaptive.utils.logger import get_logger


logger = get_logger(__name__)


def install_middleware(app: Any) -> None:
    if not FASTAPI_AVAILABLE or not hasattr(app, "middleware"):
        return

    @app.middleware("http")
    async def _error_handler_middleware(request, call_next):  # type: ignore[no-untyped-def]
        try:
            return await call_next(request)
        except HTTPException:
            raise
        except GraphEngineError as error:
            logger.exception("Graph engine error: %s", error)
            return JSONResponse(
                {
                    "error": str(error),
                    "code": getattr(error, "code", "GRAPH_ENGINE_ERROR"),
                },
                status_code=400,
            )
        except ValueError as error:
            logger.warning("Validation error: %s", error)
            return JSONResponse({"error": str(error)}, status_code=400)
        except Exception as error:
            settings = get_settings()
            logger.exception("Unhandled API error: %s", error)
            detail = str(error) if not settings.is_production else "Internal server error"
            return JSONResponse({"error": detail}, status_code=500)


__all__ = ["install_middleware"]


