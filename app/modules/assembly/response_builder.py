"""Build final deterministic API response from enriched skill data."""

from __future__ import annotations


def build_response(skills: dict) -> dict:
    if not isinstance(skills, dict):
        raise ValueError("skills must be a dictionary")

    skill_items: list[dict] = []
    for name in sorted(skills.keys()):
        payload = skills[name]
        if not isinstance(payload, dict):
            raise ValueError(f"Skill payload for '{name}' must be an object")

        skill_items.append(
            {
                "name": payload.get("name", name),
                "score": payload.get("score", 0.0),
                "level": payload.get("level", "beginner"),
                "confidence": payload.get("confidence", 0.0),
                "reasoning": payload.get("reasoning", ""),
                "evidence": payload.get("evidence", []),
            }
        )

    return {
        "version": "1.0",
        "candidate_profile": {
            "skills": skill_items,
        },
        "meta": {
            "total_skills": len(skill_items),
        },
    }
