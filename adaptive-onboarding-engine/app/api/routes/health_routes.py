"""
app/api/routes/health_routes.py

Operational health/readiness endpoints.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from pathlib import Path
import importlib.util
import sys

try:
    from api._compat import APIRouter
    import graph.graph_engine as graph_engine
except ImportError:  # pragma: no cover - alternate package root
    from app.api._compat import APIRouter
    from app.modules.graph import graph_engine

try:
    from queue import job_manager, job_queue  # type: ignore
except Exception:  # pragma: no cover - queue module name conflicts with stdlib
    try:
        from app.queue import job_manager, job_queue  # type: ignore
    except Exception:  # pragma: no cover - direct file fallback
        _queue_dir = Path(__file__).resolve().parents[2] / "queue"

        if "_job_manager_fallback" in sys.modules:
            job_manager = sys.modules["_job_manager_fallback"]  # type: ignore
        else:
            _jm_spec = importlib.util.spec_from_file_location(
                "_job_manager_fallback",
                _queue_dir / "job_manager.py",
            )
            _jm_module = importlib.util.module_from_spec(_jm_spec)
            sys.modules["_job_manager_fallback"] = _jm_module
            assert _jm_spec is not None and _jm_spec.loader is not None
            _jm_spec.loader.exec_module(_jm_module)
            job_manager = _jm_module  # type: ignore

        if "_job_queue_fallback" in sys.modules:
            job_queue = sys.modules["_job_queue_fallback"]  # type: ignore
        else:
            _jq_spec = importlib.util.spec_from_file_location(
                "_job_queue_fallback",
                _queue_dir / "job_queue.py",
            )
            _jq_module = importlib.util.module_from_spec(_jq_spec)
            sys.modules["_job_queue_fallback"] = _jq_module
            assert _jq_spec is not None and _jq_spec.loader is not None
            _jq_spec.loader.exec_module(_jq_module)
            job_queue = _jq_module  # type: ignore


router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "adaptive-onboarding-engine",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/ready")
async def ready() -> dict[str, Any]:
    graph_ok = True
    graph_message = "loaded"

    try:
        if not graph_engine.is_loaded():
            graph_engine.load_graph()
            graph_message = "loaded_on_demand"
    except Exception as error:
        graph_ok = False
        graph_message = str(error)

    status = "ready" if graph_ok else "degraded"

    return {
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {
            "graph": {"ok": graph_ok, "detail": graph_message},
            "queue": {"ok": True, "size": job_queue.queue_size()},
            "jobs": {"ok": True, **job_manager.get_job_metrics()},
        },
    }


@router.get("/metrics")
async def metrics() -> dict[str, Any]:
    job_metrics = job_manager.get_job_metrics()
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "jobs": job_metrics,
        "queue": {
            "size": job_queue.queue_size(),
            "pathway_tasks": job_queue.queue_size(task_type="pathway"),
            "trace_tasks": job_queue.queue_size(task_type="trace"),
        },
    }


__all__ = ["router"]
