"""
app/api/routes/skills_routes.py

HTTP route bindings for skill discovery and normalization.
"""

from __future__ import annotations

from typing import Any
from collections.abc import Mapping

try:
    from api._compat import APIRouter, Body, HTTPException, Query
    from api.controllers import skills_controller
except ImportError:  # pragma: no cover - alternate package root
    from app.api._compat import APIRouter, Body, HTTPException, Query
    from app.api.controllers import skills_controller


router = APIRouter(prefix="/v1/skills", tags=["skills"])


@router.get("")
async def list_skills_endpoint(
    q: str | None = Query(default=None),
    limit: int = Query(default=100),
) -> dict[str, Any]:
    try:
        return await skills_controller.list_skills(query=q, limit=limit)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.get("/{skill_id}")
async def get_skill_endpoint(skill_id: str) -> dict[str, Any]:
    try:
        return await skills_controller.get_skill(skill_id)
    except skills_controller.SkillNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.post("/normalize")
async def normalize_skills_endpoint(payload: Mapping[str, Any] = Body(...)) -> dict[str, Any]:
    try:
        return await skills_controller.normalize(payload)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


__all__ = ["router"]
