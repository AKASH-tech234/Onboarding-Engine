"""Convert pathway internals into API schema objects."""

from __future__ import annotations

from typing import Any, cast

from schemas.pathway import PathwayItem, PathwayMeta, PathwayPhase, PathwayResponse


def build_pathway_response(pathway: dict) -> dict:
    phases_in = pathway.get("phases", [])
    phases: list[PathwayPhase] = []

    order = 1
    for phase in phases_in:
        skills = phase.get("skills", [])
        items: list[PathwayItem] = []
        for skill_entry in skills:
            if isinstance(skill_entry, dict):
                skill_name = str(skill_entry.get("skill", "")).strip()
                score_value = float(skill_entry.get("score", 0.0))
            else:
                skill_name = str(skill_entry).strip()
                score_value = 0.0

            if skill_name == "":
                continue

            items.append(PathwayItem(skill=skill_name, order=order, score=score_value))
            order += 1

        phases.append(
            PathwayPhase(
                phase=int(phase.get("phase", len(phases) + 1)),
                title=str(phase.get("title", f"Phase {len(phases) + 1}")),
                items=items,
            )
        )

    response = PathwayResponse(
        phases=phases,
        meta=PathwayMeta(
            total_items=int(pathway.get("meta", {}).get("total_items", 0)),
            total_phases=int(pathway.get("meta", {}).get("total_phases", len(phases))),
            reason_code=pathway.get("meta", {}).get("reason_code"),
            graph_diagnostics=pathway.get("meta", {}).get("graph_diagnostics"),
        ),
    )

    response_any = cast(Any, response)
    return response_any.model_dump()
