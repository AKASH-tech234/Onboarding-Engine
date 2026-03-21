"""Pathway response schemas for graph-based roadmap output."""

from __future__ import annotations

from pydantic import BaseModel


class PathwayStrictModel(BaseModel):
    class Config:
        extra = "forbid"


class PathwayItem(PathwayStrictModel):
    skill: str
    order: int
    score: float


class PathwayPhase(PathwayStrictModel):
    phase: int
    title: str
    items: list[PathwayItem]


class PathwayMeta(PathwayStrictModel):
    total_items: int
    total_phases: int
    reason_code: str | None = None
    graph_diagnostics: dict[str, int | str] | None = None


class PathwayResponse(PathwayStrictModel):
    phases: list[PathwayPhase]
    meta: PathwayMeta
