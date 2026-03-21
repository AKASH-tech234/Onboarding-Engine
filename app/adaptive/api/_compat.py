"""
app/api/_compat.py

Compatibility helpers so API modules can import cleanly even when FastAPI
is not installed in the local environment.
"""

from __future__ import annotations

from typing import Any, Callable

try:  # pragma: no cover - exercised in runtime environments with FastAPI
    from fastapi import APIRouter, Body, FastAPI, HTTPException, Query
    from fastapi.responses import JSONResponse, StreamingResponse

    FASTAPI_AVAILABLE = True
except ImportError:  # pragma: no cover - local fallback for missing deps
    FASTAPI_AVAILABLE = False

    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str | dict[str, Any]):
            self.status_code = status_code
            self.detail = detail
            super().__init__(str(detail))

    def Query(default: Any = None, **_: Any) -> Any:
        return default

    def Body(default: Any = None, **_: Any) -> Any:
        return default

    class JSONResponse(dict):
        def __init__(self, content: Any, status_code: int = 200):
            super().__init__(content=content, status_code=status_code)

    class StreamingResponse:
        def __init__(self, content: Any, media_type: str = "text/plain"):
            self.content = content
            self.media_type = media_type

    class APIRouter:
        def __init__(self, *, prefix: str = "", tags: list[str] | None = None):
            self.prefix = prefix
            self.tags = tags or []
            self.routes: list[dict[str, Any]] = []

        def _add_route(
            self,
            method: str,
            path: str,
            endpoint: Callable[..., Any],
            **kwargs: Any,
        ) -> Callable[..., Any]:
            self.routes.append(
                {
                    "method": method,
                    "path": path,
                    "endpoint": endpoint,
                    "kwargs": kwargs,
                }
            )
            return endpoint

        def get(self, path: str = "", **kwargs: Any):
            def decorator(endpoint: Callable[..., Any]) -> Callable[..., Any]:
                return self._add_route("GET", path, endpoint, **kwargs)

            return decorator

        def post(self, path: str = "", **kwargs: Any):
            def decorator(endpoint: Callable[..., Any]) -> Callable[..., Any]:
                return self._add_route("POST", path, endpoint, **kwargs)

            return decorator

        def delete(self, path: str = "", **kwargs: Any):
            def decorator(endpoint: Callable[..., Any]) -> Callable[..., Any]:
                return self._add_route("DELETE", path, endpoint, **kwargs)

            return decorator

    class FastAPI(APIRouter):
        def __init__(self, *args: Any, **kwargs: Any):
            super().__init__()
            self.args = args
            self.kwargs = kwargs
            self.routers: list[APIRouter] = []
            self.middlewares: list[dict[str, Any]] = []

        def include_router(self, router: APIRouter) -> None:
            self.routers.append(router)

        def add_middleware(self, middleware_class: Any, **options: Any) -> None:
            self.middlewares.append(
                {"middleware_class": middleware_class, "options": options}
            )


__all__ = [
    "APIRouter",
    "Body",
    "FASTAPI_AVAILABLE",
    "FastAPI",
    "HTTPException",
    "JSONResponse",
    "Query",
    "StreamingResponse",
]


