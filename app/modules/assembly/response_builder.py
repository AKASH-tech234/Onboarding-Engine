"""Build final deterministic API response from enriched skill data."""

from __future__ import annotations

from utils.logger import get_logger


logger = get_logger("response")


def _clamp(value: float) -> float:
    return round(max(0.0, min(value, 1.0)), 4)


def build_response(
    skills: dict,
    profile_key: str = "candidate_profile",
    total_key: str = "total_skills",
) -> dict:
    logger.debug("Response builder input: %s", skills)

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
        if not evidence:
            logger.warning("No evidence for skill: %s", name)
            evidence = ["skills"]

        reasoning = payload.get("reasoning", "")
        if not isinstance(reasoning, str) or reasoning.strip() == "":
            reasoning = "no reasoning available"

        level = payload.get("level", "beginner")
        if not isinstance(level, str) or level.strip() == "":
            level = "beginner"

        item = {
            "name": payload.get("name", name),
            "score": score,
            "level": level,
            "confidence": confidence,
            "reasoning": reasoning,
            "evidence": evidence,
        }

        # Keep contract stable while stripping null/empty-string values.
        cleaned_item = {
            key: value
            for key, value in item.items()
            if value is not None and not (isinstance(value, str) and value == "")
        }

        skill_items.append(cleaned_item)

    response = {
        "version": "1.0",
        profile_key: {
            "skills": skill_items,
        },
        "meta": {
            total_key: len(skill_items),
        },
    }
    logger.debug("Response builder output: %s", response)

    return response
