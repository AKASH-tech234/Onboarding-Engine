"""
app/api/server.py

ASGI entrypoint for local development and production deployment.
"""

from __future__ import annotations

try:
    from api._compat import FASTAPI_AVAILABLE
    from api.app import create_app
    from config.settings import get_settings
    from utils.logger import configure_logging, get_logger
    import graph.graph_engine as graph_engine
except ImportError:  # pragma: no cover - alternate package root
    from app.api._compat import FASTAPI_AVAILABLE
    from app.api.app import create_app
    from app.config.settings import get_settings
    from app.utils.logger import configure_logging, get_logger
    from app.modules.graph import graph_engine


configure_logging()
logger = get_logger(__name__)
app = create_app()


def _preload_graph() -> None:
    try:
        if not graph_engine.is_loaded():
            graph_engine.load_graph()
    except Exception:
        # Keep startup resilient; readiness endpoint exposes exact failure.
        logger.exception("Graph preload failed; readiness endpoint will report degraded state.")


def run() -> None:
    if not FASTAPI_AVAILABLE:
        raise RuntimeError("FastAPI/uvicorn dependencies are not installed.")

    import uvicorn  # pragma: no cover - runtime dependency

    settings = get_settings()
    host = settings.host
    port = settings.port
    reload_flag = settings.reload
    logger.info("Starting API server on %s:%s (reload=%s)", host, port, reload_flag)
    uvicorn.run("app.api.server:app", host=host, port=port, reload=reload_flag)


_preload_graph()


if __name__ == "__main__":
    run()
