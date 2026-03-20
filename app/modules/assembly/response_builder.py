"""Build final deterministic API response from enriched skill data."""

from __future__ import annotations


def _clamp(value: float) -> float:
    return round(max(0.0, min(value, 1.0)), 4)


def build_response(skills: dict) -> dict:
    if not isinstance(skills, dict):
        raise ValueError("skills must be a dictionary")

    skill_items: list[dict] = []
    for name in sorted(skills.keys()):
        payload = skills[name]
        if not isinstance(payload, dict):
            raise ValueError(f"Skill payload for '{name}' must be an object")

        score = _clamp(float(payload.get("score", 0.0)))
        confidence = _clamp(float(payload.get("confidence", 0.0)))

        evidence_raw = payload.get("evidence", [])
        evidence: list[str] = []
        if isinstance(evidence_raw, list):
            for item in evidence_raw:
                if isinstance(item, str) and item and item not in evidence:
                    evidence.append(item)

        reasoning = payload.get("reasoning", "")
        if not isinstance(reasoning, str) or reasoning.strip() == "":
            reasoning = "no reasoning available"

        skill_items.append(
            {
                "name": payload.get("name", name),
                "score": score,
                "level": payload.get("level", "beginner"),
                "confidence": confidence,
                "reasoning": reasoning,
                "evidence": evidence,
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
