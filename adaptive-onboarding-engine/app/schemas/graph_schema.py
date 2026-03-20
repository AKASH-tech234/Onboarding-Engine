"""
app/schemas/graph_schema.py

Pydantic schemas for graph endpoints.
"""

from __future__ import annotations

from typing import Any, Literal

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


class GraphNodeSchema(BaseModel):
    id: str
    label: str
    domain: str = "general"
    base_effort_days: int = Field(default=0, ge=0)
    difficulty: int = Field(default=1, ge=1, le=5)
    tags: list[str] = Field(default_factory=list)
    source: str = "curated"


class GraphEdgeSchema(BaseModel):
    from_id: str = Field(alias="from")
    to_id: str = Field(alias="to")
    importance: Literal["mandatory", "recommended"] = "mandatory"
    weight: float = Field(default=1.0, ge=0.0, le=1.0)

    model_config = ConfigDict(populate_by_name=True)


class GraphMetadataResponse(BaseModel):
    version: str | None = None
    node_count: int = Field(default=0, ge=0)
    edge_count: int = Field(default=0, ge=0)
    domains: list[str] = Field(default_factory=list)
    graph_path: str | None = None


class GraphSnapshotResponse(BaseModel):
    metadata: GraphMetadataResponse = Field(default_factory=GraphMetadataResponse)
    nodes: list[GraphNodeSchema] = Field(default_factory=list)
    edges: list[GraphEdgeSchema] = Field(default_factory=list)


class GraphValidationIssue(BaseModel):
    code: str
    message: str
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    details: dict[str, Any] = Field(default_factory=dict)


class GraphValidationResponse(BaseModel):
    valid: bool = True
    issues: list[GraphValidationIssue] = Field(default_factory=list)


class GraphExpandRequest(BaseModel):
    skill_label: str
    role_context: str | None = None
    domain_hint: str | None = None
    max_new_nodes: int = Field(default=5, ge=1, le=20)


class GraphExpandResponse(BaseModel):
    accepted: bool = True
    staged_node_ids: list[str] = Field(default_factory=list)
    message: str | None = None


class GraphPromoteResponse(BaseModel):
    promoted: bool = True
    promoted_node_ids: list[str] = Field(default_factory=list)
    message: str | None = None


__all__ = [
    "GraphNodeSchema",
    "GraphEdgeSchema",
    "GraphMetadataResponse",
    "GraphSnapshotResponse",
    "GraphValidationIssue",
    "GraphValidationResponse",
    "GraphExpandRequest",
    "GraphExpandResponse",
    "GraphPromoteResponse",
]
