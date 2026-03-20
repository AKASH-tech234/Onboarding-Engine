"""
app/schemas/job_schema.py

Job tracking and webhook payload schemas.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
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


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobProgress(BaseModel):
    stage: str | None = None
    message: str | None = None
    percent: int = Field(default=0, ge=0, le=100)


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    created_at: datetime | None = None
    updated_at: datetime | None = None
    candidate_id: str | None = None
    job_profile_id: str | None = None
    progress: JobProgress | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    trace_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="ignore")


class WebhookPayload(BaseModel):
    event: str
    job_id: str
    status: JobStatus
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    callback_url: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    signature: str | None = None

    model_config = ConfigDict(extra="ignore")


__all__ = [
    "JobStatus",
    "JobProgress",
    "JobResponse",
    "WebhookPayload",
]
