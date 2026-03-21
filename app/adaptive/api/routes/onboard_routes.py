"""
app/api/routes/onboard_routes.py

HTTP route bindings for onboarding operations.
"""

from __future__ import annotations

from typing import Any
from collections.abc import Mapping

from app.adaptive.api._compat import APIRouter, Body, HTTPException
from app.adaptive.api.controllers import onboard_controller
from app.adaptive.schemas.onboard_schema import OnboardRequest


router = APIRouter(prefix="/v1/onboard", tags=["onboard"])


@router.post("")
async def onboard_endpoint(
    request: OnboardRequest | Mapping[str, Any] = Body(...),
) -> dict[str, Any]:
    try:
        response = await onboard_controller.onboard(request)
        return _dump_model(response)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.post("/preview")
async def preview_endpoint(
    request: OnboardRequest | Mapping[str, Any] = Body(...),
) -> dict[str, Any]:
    try:
        response = await onboard_controller.preview(request)
        return _dump_model(response)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.post("/{job_id}/refresh")
async def refresh_endpoint(
    job_id: str,
    request: OnboardRequest | Mapping[str, Any] = Body(...),
) -> dict[str, Any]:
    try:
        response = await onboard_controller.refresh(request, previous_job_id=job_id)
        return _dump_model(response)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


def _dump_model(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    if isinstance(value, Mapping):
        return dict(value)
    return dict(vars(value))


__all__ = ["router"]


