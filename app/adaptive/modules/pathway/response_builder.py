"""
app/modules/pathway/response_builder.py

Transforms PathwayResult objects into API-ready dictionaries.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any
from collections.abc import Mapping

from app.adaptive.modules.pathway.pathway_builder import PathwayResult


def build_response(
    pathway_result: PathwayResult | Mapping[str, Any],
    *,
    include_metadata: bool = True,
) -> dict[str, Any]:
    """
    Build a consistent JSON-ready response shape.
    """
    data = _coerce_to_dict(pathway_result)

    phases = _coerce_list(data.get("phases"))
    response: dict[str, Any] = {
        "candidate_id": data.get("candidate_id"),
        "job_id": data.get("job_id"),
        "pathway_type": data.get("pathway_type", "targeted"),
        "summary": {
            "total_phases": len(phases),
            "total_items": int(data.get("total_items", 0)),
            "total_effort_days": int(data.get("total_effort_days", 0)),
            "unresolved_count": len(_coerce_list(data.get("unresolved_ids"))),
            "trimmed_count": len(_coerce_list(data.get("trimmed_ids"))),
            "pruned_count": len(_coerce_list(data.get("pruned_ids"))),
            "valid_dependency_order": _extract_validation_flag(data.get("phase_validation")),
        },
        "unresolved_ids": _coerce_list(data.get("unresolved_ids")),
        "pruned_ids": _coerce_list(data.get("pruned_ids")),
        "trimmed_ids": _coerce_list(data.get("trimmed_ids")),
        "phase_validation": _coerce_mapping(
            data.get("phase_validation"),
            default={"valid": True, "violations": []},
        ),
        "phases": [_serialize_phase(phase) for phase in phases],
    }

    if include_metadata:
        response["metadata"] = _coerce_mapping(data.get("metadata"), default={})

    return response


def build_preview_response(pathway_result: PathwayResult | Mapping[str, Any]) -> dict[str, Any]:
    """
    Lightweight summary-only response.
    """
    payload = build_response(pathway_result, include_metadata=False)
    return {
        "candidate_id": payload.get("candidate_id"),
        "job_id": payload.get("job_id"),
        "pathway_type": payload.get("pathway_type"),
        "summary": payload.get("summary", {}),
    }


def build_response_model(pathway_result: PathwayResult | Mapping[str, Any]) -> Any:
    """
    Return Pydantic model instance if schema is available; otherwise returns dict.
    """
    payload = build_response(pathway_result)

    try:
        from app.adaptive.schemas.pathway_schema import PathwayResponse  # type: ignore
    except Exception:
        return payload

    if hasattr(PathwayResponse, "model_validate"):
        return PathwayResponse.model_validate(payload)
    if hasattr(PathwayResponse, "parse_obj"):
        return PathwayResponse.parse_obj(payload)
    return payload


def _serialize_phase(phase: Any) -> dict[str, Any]:
    phase_data = _coerce_to_dict(phase)
    items = [_serialize_item(item) for item in _coerce_list(phase_data.get("items"))]
    return {
        "phase_number": int(phase_data.get("phase_number", 0)),
        "focus_domain": str(phase_data.get("focus_domain", "general")),
        "total_effort_days": int(phase_data.get("total_effort_days", 0)),
        "min_critical_level": int(phase_data.get("min_critical_level", 0)),
        "max_critical_level": int(phase_data.get("max_critical_level", 0)),
        "items": items,
    }


def _serialize_item(item: Any) -> dict[str, Any]:
    item_data = _coerce_to_dict(item)
    return {
        "skill_id": item_data.get("skill_id"),
        "label": item_data.get("label"),
        "domain": item_data.get("domain", "general"),
        "phase_number": int(item_data.get("phase_number", 0)),
        "proficiency_status": item_data.get("proficiency_status"),
        "current_proficiency": float(item_data.get("current_proficiency", 0.0)),
        "required_proficiency": float(item_data.get("required_proficiency", 0.0)),
        "gap_delta": float(item_data.get("gap_delta", 0.0)),
        "base_effort_days": int(item_data.get("base_effort_days", 0)),
        "adjusted_effort_days": int(item_data.get("adjusted_effort_days", 0)),
        "composite_score": float(item_data.get("composite_score", 0.0)),
        "unlock_count": int(item_data.get("unlock_count", 0)),
        "resources": _coerce_list(item_data.get("resources")),
        "notes": _coerce_list(item_data.get("notes")),
    }


def _coerce_to_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "__dict__"):
        return dict(vars(value))
    return {}


def _coerce_mapping(value: Any, default: dict[str, Any]) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return default


def _coerce_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _extract_validation_flag(value: Any) -> bool:
    if isinstance(value, Mapping):
        return bool(value.get("valid", True))
    return True


__all__ = [
    "build_response",
    "build_preview_response",
    "build_response_model",
]


