"""Skill normalization for deterministic resume parsing."""

from __future__ import annotations

from utils.logger import get_logger


SKILL_VARIANTS = {
    "nodejs": "node.js",
    "node": "node.js",
    "node js": "node.js",
    "py": "python",
}


logger = get_logger("normalization")


def _normalize_single_skill(skill: str) -> str:
    lowered = skill.strip().lower()
    if lowered in SKILL_VARIANTS:
        return SKILL_VARIANTS[lowered]

    compact = lowered.replace(" ", "")
    if compact in SKILL_VARIANTS:
        return SKILL_VARIANTS[compact]

    return lowered


def normalize_skills(data: dict) -> dict:
    logger.debug("Normalization input: %s", data)

    if not isinstance(data, dict):
        raise ValueError("Input must be an object")

    skills = data.get("skills")
    if not isinstance(skills, list):
        raise ValueError("skills must be a list")

    normalized_skills: list[str] = []
    seen: set[str] = set()

    for idx, skill in enumerate(skills):
        if not isinstance(skill, str):
            raise ValueError(f"skills[{idx}] must be a string")
        if skill.strip() == "":
            raise ValueError(f"skills[{idx}] cannot be empty")

        normalized = _normalize_single_skill(skill)
        if normalized not in seen:
            seen.add(normalized)
            normalized_skills.append(normalized)

    updated = dict(data)
    updated["skills"] = normalized_skills
    logger.debug("Normalization output: %s", updated)
    return updated
