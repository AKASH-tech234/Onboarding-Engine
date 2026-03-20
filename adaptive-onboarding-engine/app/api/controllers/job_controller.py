"""
app/api/controllers/job_controller.py

Controller logic for job status endpoints.
"""

from __future__ import annotations

from typing import AsyncGenerator, Any
import json
from pathlib import Path
import importlib.util
import sys

try:
    from schemas.job_schema import JobResponse
except ImportError:  # pragma: no cover - alternate package root
    from app.schemas.job_schema import JobResponse

try:
    from queue import job_manager  # type: ignore
except Exception:  # pragma: no cover - queue module name conflicts with stdlib
    try:
        from app.queue import job_manager  # type: ignore
    except Exception:  # pragma: no cover - direct file fallback
        if "_job_manager_fallback" in sys.modules:
            job_manager = sys.modules["_job_manager_fallback"]  # type: ignore
        else:
            _job_manager_path = Path(__file__).resolve().parents[2] / "queue" / "job_manager.py"
            _spec = importlib.util.spec_from_file_location("_job_manager_fallback", _job_manager_path)
            _module = importlib.util.module_from_spec(_spec)
            sys.modules["_job_manager_fallback"] = _module
            assert _spec is not None and _spec.loader is not None
            _spec.loader.exec_module(_module)
            job_manager = _module  # type: ignore


async def get_job(job_id: str) -> JobResponse:
    """
    Fetch current job status.
    """
    job = job_manager.get_job_status(job_id)
    if job is None:
        raise ValueError(f"Job '{job_id}' not found.")
    return job


async def cancel_job(job_id: str) -> JobResponse:
    """
    Cancel a queued/running job.
    """
    job = job_manager.cancel_job(job_id)
    if job is None:
        raise ValueError(f"Job '{job_id}' not found.")
    return job


async def stream_job(job_id: str) -> AsyncGenerator[str, None]:
    """
    Minimal SSE-like stream generator.
    """
    job = job_manager.get_job_status(job_id)
    if job is None:
        raise ValueError(f"Job '{job_id}' not found.")

    payload = _to_payload(job)
    yield f"event: job.update\ndata: {json.dumps(payload)}\n\n"


def _to_payload(job: JobResponse) -> dict[str, Any]:
    if hasattr(job, "model_dump"):
        return job.model_dump()
    if hasattr(job, "dict"):
        return job.dict()
    return dict(vars(job))


__all__ = ["get_job", "cancel_job", "stream_job"]
