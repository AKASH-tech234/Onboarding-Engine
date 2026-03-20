"""
app/api/controllers/graph_controller.py

Controller logic for graph metadata, validation, and staged expansion.
"""

from __future__ import annotations

from typing import Any, TypeVar
from collections.abc import Mapping

try:
    import graph.graph_engine as graph_engine
    from graph.models import SkillNode
    from graph.topological_sort import detect_cycle
    from schemas.graph_schema import (
        GraphEdgeSchema,
        GraphExpandRequest,
        GraphExpandResponse,
        GraphMetadataResponse,
        GraphNodeSchema,
        GraphPromoteResponse,
        GraphSnapshotResponse,
        GraphValidationIssue,
        GraphValidationResponse,
    )
except ImportError:  # pragma: no cover - alternate package root
    from app.modules.graph import graph_engine
    from app.modules.graph.models import SkillNode
    from app.modules.graph.topological_sort import detect_cycle
    from app.schemas.graph_schema import (
        GraphEdgeSchema,
        GraphExpandRequest,
        GraphExpandResponse,
        GraphMetadataResponse,
        GraphNodeSchema,
        GraphPromoteResponse,
        GraphSnapshotResponse,
        GraphValidationIssue,
        GraphValidationResponse,
    )


TModel = TypeVar("TModel")


async def get_metadata() -> GraphMetadataResponse:
    _ensure_graph_loaded()
    return _to_model(GraphMetadataResponse, graph_engine.get_metadata())


async def get_snapshot(*, include_staged: bool = False) -> GraphSnapshotResponse:
    _ensure_graph_loaded()

    node_ids = graph_engine.get_node_ids()
    nodes: list[GraphNodeSchema] = []
    edges: list[GraphEdgeSchema] = []

    for node_id in node_ids:
        node = graph_engine.get_node(node_id)
        if node is None:
            continue
        nodes.append(
            GraphNodeSchema(
                id=node.id,
                label=node.label,
                domain=node.domain,
                base_effort_days=node.base_effort_days,
                difficulty=node.difficulty,
                tags=list(node.tags),
                source=node.source,
            )
        )

    for node_id in node_ids:
        for edge in graph_engine.get_successor_edges(node_id):
            edges.append(
                GraphEdgeSchema(
                    from_id=edge.from_id,
                    to_id=edge.to_id,
                    importance=edge.importance.value,
                    weight=edge.weight,
                )
            )

    metadata = graph_engine.get_metadata()
    metadata["node_count"] = len(nodes)
    metadata["edge_count"] = len(edges)
    if include_staged:
        metadata["staged_included"] = False
        metadata["staged_note"] = "Staged nodes are not enumerable in current graph engine API."

    return GraphSnapshotResponse(
        metadata=_to_model(GraphMetadataResponse, metadata),
        nodes=nodes,
        edges=edges,
    )


async def validate_graph() -> GraphValidationResponse:
    _ensure_graph_loaded()

    adjacency = {
        node_id: graph_engine.get_dependents(node_id)
        for node_id in graph_engine.get_node_ids()
    }

    issues: list[GraphValidationIssue] = []

    if detect_cycle(adjacency):
        issues.append(
            GraphValidationIssue(
                code="cycle_detected",
                severity="critical",
                message="Cycle detected in graph dependencies.",
                details={"hint": "Run topological sort diagnostics for detailed cycle nodes."},
            )
        )

    isolated_nodes: list[str] = []
    for node_id in graph_engine.get_node_ids():
        if not graph_engine.get_prerequisites(node_id) and not graph_engine.get_dependents(node_id):
            isolated_nodes.append(node_id)

    if isolated_nodes:
        issues.append(
            GraphValidationIssue(
                code="isolated_nodes",
                severity="low",
                message="Graph contains isolated nodes.",
                details={"count": len(isolated_nodes), "sample": isolated_nodes[:10]},
            )
        )

    valid = not any(issue.severity in {"critical", "high"} for issue in issues)
    return GraphValidationResponse(valid=valid, issues=issues)


async def expand_graph(request: GraphExpandRequest | Mapping[str, Any]) -> GraphExpandResponse:
    _ensure_graph_loaded()
    payload = _to_model(GraphExpandRequest, request)
    canonical_id = _canonicalize_skill_id(payload.skill_label)

    if graph_engine.has_node(canonical_id):
        return GraphExpandResponse(
            accepted=False,
            staged_node_ids=[],
            message=f"Skill '{canonical_id}' already exists in the graph.",
        )

    node = SkillNode(
        id=canonical_id,
        label=payload.skill_label.strip(),
        domain=(payload.domain_hint or "general").strip().lower(),
        base_effort_days=3,
        difficulty=3,
        tags=tuple(),
        source="llm_generated",
    )
    graph_engine.stage_node(node, edges=[])

    return GraphExpandResponse(
        accepted=True,
        staged_node_ids=[node.id],
        message="Skill staged successfully.",
    )


async def promote_skill(skill_id: str) -> GraphPromoteResponse:
    _ensure_graph_loaded()
    canonical_id = _canonicalize_skill_id(skill_id)

    if graph_engine.has_node(canonical_id):
        return GraphPromoteResponse(
            promoted=True,
            promoted_node_ids=[canonical_id],
            message="Skill is already present in the active graph.",
        )

    staged = graph_engine.get_staged_node(canonical_id)
    if staged is None:
        return GraphPromoteResponse(
            promoted=False,
            promoted_node_ids=[],
            message=f"Staged skill '{canonical_id}' not found.",
        )

    data = _dump_current_graph()
    existing_ids = {node["id"] for node in data["nodes"]}
    if staged.id not in existing_ids:
        data["nodes"].append(
            {
                "id": staged.id,
                "label": staged.label,
                "domain": staged.domain,
                "base_effort_days": staged.base_effort_days,
                "difficulty": staged.difficulty,
                "tags": list(staged.tags),
                "source": staged.source,
            }
        )

    graph_engine.load_graph_from_dict(data)
    return GraphPromoteResponse(
        promoted=True,
        promoted_node_ids=[staged.id],
        message="Staged skill promoted to the active in-memory graph.",
    )


def _dump_current_graph() -> dict[str, Any]:
    node_ids = graph_engine.get_node_ids()
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    for node_id in node_ids:
        node = graph_engine.get_node(node_id)
        if node is None:
            continue
        nodes.append(
            {
                "id": node.id,
                "label": node.label,
                "domain": node.domain,
                "base_effort_days": node.base_effort_days,
                "difficulty": node.difficulty,
                "tags": list(node.tags),
                "source": node.source,
            }
        )

    for node_id in node_ids:
        for edge in graph_engine.get_successor_edges(node_id):
            edges.append(
                {
                    "from": edge.from_id,
                    "to": edge.to_id,
                    "importance": edge.importance.value,
                    "weight": edge.weight,
                }
            )

    return {
        "version": graph_engine.get_version() or "v1",
        "nodes": nodes,
        "edges": edges,
    }


def _ensure_graph_loaded() -> None:
    if graph_engine.is_loaded():
        return
    graph_engine.load_graph()


def _canonicalize_skill_id(label: str) -> str:
    return "_".join(" ".join(label.strip().lower().split()).split())


def _to_model(model_type: type[TModel], value: Any) -> TModel:
    if isinstance(value, model_type):
        return value
    if hasattr(model_type, "model_validate"):
        return model_type.model_validate(value)  # type: ignore[return-value]
    if hasattr(model_type, "parse_obj"):
        return model_type.parse_obj(value)  # type: ignore[return-value]
    return model_type(**dict(value))  # type: ignore[arg-type]


__all__ = [
    "get_metadata",
    "get_snapshot",
    "validate_graph",
    "expand_graph",
    "promote_skill",
]
