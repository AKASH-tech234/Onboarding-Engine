"""
app/schemas/onboard_schema.py

Input schemas for onboarding endpoints.
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


class CandidateSkillInput(BaseModel):
    name: str
    score: float | None = Field(default=None, ge=0.0, le=1.0)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CandidateInput(BaseModel):
    id: str | None = None
    skills: list[CandidateSkillInput] = Field(default_factory=list)
    resume_text: str | None = None
    profile: dict[str, Any] = Field(default_factory=dict)


class JobSkillInput(BaseModel):
    name: str
    score: float | None = Field(default=None, ge=0.0, le=1.0)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    required: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class JobInput(BaseModel):
    id: str | None = None
    title: str | None = None
    role: str | None = None
    description: str | None = None
    skills: list[JobSkillInput] = Field(default_factory=list)
    raw_jd_text: str | None = None
    profile: dict[str, Any] = Field(default_factory=dict)


class OptionsInput(BaseModel):
    role: str | None = None
    graph_version: str = "v1"
    learning_mode: str = "deep_learning"
    time_budget_days: int | None = Field(default=None, ge=1)
    include_traces: bool = True
    include_resources: bool = True
    group_by_domain: bool = True
    max_days_per_phase: int = Field(default=7, ge=1)
    max_items_per_phase: int = Field(default=5, ge=1)


class OnboardRequest(BaseModel):
    """
    Main request payload for `/v1/onboard`.

    Supports either `requirement_profile` or `job_profile`.
    """

    request_id: str | None = None
    candidate_profile: CandidateInput
    requirement_profile: JobInput | None = None
    job_profile: JobInput | None = None
    options: OptionsInput = Field(default_factory=OptionsInput)

    model_config = ConfigDict(extra="ignore")

    def resolved_job_profile(self) -> JobInput | None:
        return self.requirement_profile or self.job_profile


class OnboardPreviewResponse(BaseModel):
    request_id: str | None = None
    accepted: bool = True
    candidate_id: str | None = None
    job_id: str | None = None
    warnings: list[str] = Field(default_factory=list)
    estimated_gap_count: int = Field(default=0, ge=0)


__all__ = [
    "CandidateSkillInput",
    "CandidateInput",
    "JobSkillInput",
    "JobInput",
    "OptionsInput",
    "OnboardRequest",
    "OnboardPreviewResponse",
]
