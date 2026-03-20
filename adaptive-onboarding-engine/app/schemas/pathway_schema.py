"""
app/schemas/pathway_schema.py

Pydantic response models for pathway API payloads.
"""

from __future__ import annotations

from typing import Any

try:
    from pydantic import BaseModel, Field, ConfigDict
except ImportError:  # pragma: no cover - pydantic is expected in runtime env
    try:
        from pydantic.v1 import BaseModel, Field  # type: ignore
        ConfigDict = dict  # type: ignore
    except ImportError:  # pragma: no cover - local fallback when pydantic is absent
        class BaseModel:  # type: ignore
            def __init__(self, **data: Any):
                for key, value in data.items():
                    setattr(self, key, value)

            @classmethod
            def model_validate(cls, data: Any):
                if isinstance(data, cls):
                    return data
                if isinstance(data, dict):
                    return cls(**data)
                raise TypeError("model_validate expects a dict-like value")

            @classmethod
            def parse_obj(cls, data: Any):
                return cls.model_validate(data)

            def model_dump(self) -> dict[str, Any]:
                return dict(vars(self))

            def dict(self) -> dict[str, Any]:
                return self.model_dump()

        def Field(default: Any = None, **kwargs: Any) -> Any:  # type: ignore
            if "default_factory" in kwargs:
                return kwargs["default_factory"]()
            return default

        ConfigDict = dict  # type: ignore


class PathwaySummary(BaseModel):
    total_phases: int = Field(default=0, ge=0)
    total_items: int = Field(default=0, ge=0)
    total_effort_days: int = Field(default=0, ge=0)
    unresolved_count: int = Field(default=0, ge=0)
    trimmed_count: int = Field(default=0, ge=0)
    pruned_count: int = Field(default=0, ge=0)
    valid_dependency_order: bool = True


class PathwayValidation(BaseModel):
    valid: bool = True
    violations: list[dict[str, Any]] = Field(default_factory=list)


class PathwayItem(BaseModel):
    skill_id: str
    label: str
    domain: str = "general"
    phase_number: int = Field(ge=0)
    proficiency_status: str
    current_proficiency: float = Field(ge=0.0, le=1.0)
    required_proficiency: float = Field(ge=0.0, le=1.0)
    gap_delta: float = Field(ge=0.0, le=1.0)
    base_effort_days: int = Field(ge=0)
    adjusted_effort_days: int = Field(ge=0)
    composite_score: float = Field(ge=0.0, le=1.0)
    unlock_count: int = Field(default=0, ge=0)
    resources: list[dict[str, Any]] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class PathwayPhase(BaseModel):
    phase_number: int = Field(ge=1)
    focus_domain: str = "general"
    total_effort_days: int = Field(default=0, ge=0)
    min_critical_level: int = Field(default=0, ge=0)
    max_critical_level: int = Field(default=0, ge=0)
    items: list[PathwayItem] = Field(default_factory=list)


class PathwayResponse(BaseModel):
    candidate_id: str | None = None
    job_id: str | None = None
    pathway_type: str = "targeted"
    summary: PathwaySummary = Field(default_factory=PathwaySummary)
    unresolved_ids: list[str] = Field(default_factory=list)
    pruned_ids: list[str] = Field(default_factory=list)
    trimmed_ids: list[str] = Field(default_factory=list)
    phase_validation: PathwayValidation = Field(default_factory=PathwayValidation)
    phases: list[PathwayPhase] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="ignore")


class PathwayPreviewResponse(BaseModel):
    candidate_id: str | None = None
    job_id: str | None = None
    pathway_type: str = "targeted"
    summary: PathwaySummary = Field(default_factory=PathwaySummary)

    model_config = ConfigDict(extra="ignore")


__all__ = [
    "PathwayItem",
    "PathwayPhase",
    "PathwaySummary",
    "PathwayValidation",
    "PathwayResponse",
    "PathwayPreviewResponse",
]
