"""
app/api/controllers/skills_controller.py

Controller logic for skill discovery and normalization endpoints.
"""

from __future__ import annotations

from typing import Any
from collections.abc import Mapping, Sequence

from app.adaptive.modules.graph import graph_engine
from app.adaptive.modules.ingestion.skill_normalizer import normalize_skills as normalize_skill_names


class SkillNotFoundError(ValueError):
    """Raised when a skill cannot be resolved."""


async def list_skills(*, query: str | None = None, limit: int = 100) -> dict[str, Any]:
    """
    Return canonical skills from the loaded graph.
    """
    _ensure_graph_loaded()

    normalized_query = _normalize_text(query or "")
    clamped_limit = max(1, min(500, int(limit)))

    items: list[dict[str, Any]] = []
    for skill_id in graph_engine.get_node_ids():
        node = graph_engine.get_node(skill_id)
        if node is None:
            continue

        if normalized_query and normalized_query not in _normalize_text(node.label) and normalized_query not in _normalize_text(node.id):
            continue

        items.append(
            {
                "id": node.id,
                "label": node.label,
                "domain": node.domain,
                "difficulty": node.difficulty,
                "base_effort_days": node.base_effort_days,
                "tags": list(node.tags),
                "source": node.source,
            }
        )

    items.sort(key=lambda item: _normalize_text(str(item.get("label", ""))))
    sliced = items[:clamped_limit]

    return {
        "items": sliced,
        "count": len(sliced),
        "total": len(items),
        "query": query,
        "limit": clamped_limit,
    }


async def get_skill(skill_id: str) -> dict[str, Any]:
    """
    Return one canonical skill and its graph neighborhood.
    """
    _ensure_graph_loaded()
    node = _resolve_node(skill_id)
    if node is None:
        raise SkillNotFoundError(f"Skill '{skill_id}' not found.")

    prerequisites = graph_engine.get_prerequisites(node.id)
    dependents = graph_engine.get_dependents(node.id)

    return {
        "id": node.id,
        "label": node.label,
        "domain": node.domain,
        "difficulty": node.difficulty,
        "base_effort_days": node.base_effort_days,
        "tags": list(node.tags),
        "source": node.source,
        "prerequisites": prerequisites,
        "dependents": dependents,
    }


async def normalize(payload: Mapping[str, Any] | Sequence[str] | None) -> dict[str, Any]:
    """
    Normalize one or many skill names into canonical IDs.
    """
    items = normalize_skill_names(payload)
    matched = sum(1 for item in items if item.get("matched"))
    unmatched = len(items) - matched

    return {
        "items": items,
        "count": len(items),
        "matched_count": matched,
        "unmatched_count": unmatched,
    }


def _resolve_node(skill_ref: str):
    normalized = _normalize_text(skill_ref)
    if not normalized:
        return None

    direct = graph_engine.get_node(normalized)
    if direct is not None:
        return direct

    for node_id in graph_engine.get_node_ids():
        node = graph_engine.get_node(node_id)
        if node is None:
            continue
        if _normalize_text(node.label) == normalized:
            return node
    return None


def _ensure_graph_loaded() -> None:
    if graph_engine.is_loaded():
        return
    graph_engine.load_graph()


def _normalize_text(value: str) -> str:
    return " ".join(value.strip().lower().split())


__all__ = ["SkillNotFoundError", "list_skills", "get_skill", "normalize"]


