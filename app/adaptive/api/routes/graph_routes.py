"""
app/api/routes/graph_routes.py

HTTP route bindings for graph inspection and staged edits.
"""

from __future__ import annotations

from typing import Any
from collections.abc import Mapping

from app.adaptive.api._compat import APIRouter, Body, HTTPException, Query
from app.adaptive.api.controllers import graph_controller
from app.adaptive.schemas.graph_schema import GraphExpandRequest


router = APIRouter(prefix="/v1/graph", tags=["graph"])


@router.get("")
async def get_graph_endpoint(
    include_staged: bool = Query(default=False),
) -> dict[str, Any]:
    try:
        response = await graph_controller.get_snapshot(include_staged=include_staged)
        return _dump_model(response)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.get("/metadata")
async def get_graph_metadata_endpoint() -> dict[str, Any]:
    try:
        response = await graph_controller.get_metadata()
        return _dump_model(response)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.get("/validate")
async def validate_graph_endpoint() -> dict[str, Any]:
    try:
        response = await graph_controller.validate_graph()
        return _dump_model(response)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.post("/expand")
async def expand_graph_endpoint(
    payload: GraphExpandRequest | Mapping[str, Any] = Body(...),
) -> dict[str, Any]:
    try:
        response = await graph_controller.expand_graph(payload)
        return _dump_model(response)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/promote/{skill_id}")
async def promote_skill_endpoint(skill_id: str) -> dict[str, Any]:
    try:
        response = await graph_controller.promote_skill(skill_id)
        return _dump_model(response)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


def _dump_model(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    if isinstance(value, Mapping):
        return dict(value)
    return dict(vars(value))


__all__ = ["router"]


