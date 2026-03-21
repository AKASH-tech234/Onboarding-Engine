"""
app/api/routes/jobs_routes.py

HTTP route bindings for job status, cancellation, and event streaming.
"""

from __future__ import annotations

from typing import Any

from app.adaptive.api._compat import APIRouter, FASTAPI_AVAILABLE, HTTPException, StreamingResponse
from app.adaptive.api.controllers import job_controller


router = APIRouter(prefix="/v1/jobs", tags=["jobs"])


@router.get("/{job_id}")
async def get_job_endpoint(job_id: str) -> dict[str, Any]:
    try:
        response = await job_controller.get_job(job_id)
        return _dump_model(response)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.delete("/{job_id}")
async def cancel_job_endpoint(job_id: str) -> dict[str, Any]:
    try:
        response = await job_controller.cancel_job(job_id)
        return _dump_model(response)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.get("/{job_id}/stream")
async def stream_job_endpoint(job_id: str):
    try:
        stream = job_controller.stream_job(job_id)
        if FASTAPI_AVAILABLE:
            return StreamingResponse(stream, media_type="text/event-stream")

        events = [event async for event in stream]
        return {"events": events}
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


def _dump_model(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    return dict(vars(value))


__all__ = ["router"]


