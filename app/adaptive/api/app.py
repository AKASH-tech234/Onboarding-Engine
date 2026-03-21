"""
app/api/app.py

Application factory and router registration.
"""

from __future__ import annotations

from app.adaptive.api._compat import FASTAPI_AVAILABLE, FastAPI
from app.adaptive.api.middlewares import (
    auth_middleware,
    error_handler_middleware,
    rate_limit_middleware,
    request_id_middleware,
    validate_middleware,
)
from app.adaptive.api.routes import graph_routes, health_routes, jobs_routes, onboard_routes, skills_routes
from app.adaptive.config.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Adaptive Onboarding Engine API",
        version="0.1.0",
    )

    if FASTAPI_AVAILABLE:
        try:
            from fastapi.middleware.cors import CORSMiddleware

            app.add_middleware(
                CORSMiddleware,
                allow_origins=list(settings.allowed_origins),
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
        except Exception:
            pass

    request_id_middleware.install_middleware(app)
    error_handler_middleware.install_middleware(app)
    auth_middleware.install_middleware(app)
    rate_limit_middleware.install_middleware(app)
    validate_middleware.install_middleware(app)

    app.include_router(health_routes.router)
    app.include_router(onboard_routes.router)
    app.include_router(jobs_routes.router)
    app.include_router(skills_routes.router)
    app.include_router(graph_routes.router)
    return app


app = create_app()


__all__ = ["app", "create_app"]


