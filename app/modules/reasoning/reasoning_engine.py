"""Template-based deterministic reasoning generation."""

from __future__ import annotations

from utils.logger import get_logger


logger = get_logger("reasoning")


def generate_reasoning(skills: dict) -> dict:
    logger.debug("Reasoning input: %s", skills)

    if not isinstance(skills, dict):
        raise ValueError("skills must be a dictionary")

    result: dict = {}
    for name in sorted(skills.keys()):
        payload = skills[name]
        if not isinstance(payload, dict):
            raise ValueError(f"Skill payload for '{name}' must be an object")

        listed = bool(payload.get("listed", False))
        projects = payload.get("projects", 0)
        experience_months = payload.get("experience_months", 0)

        if projects > 0 and experience_months > 0:
            reasoning = f"used in {projects} projects and {experience_months} months experience"
        elif projects > 0:
            if listed:
                reasoning = f"listed skill used in {projects} projects"
            else:
                reasoning = f"detected from project evidence in {projects} projects"
        elif experience_months > 0:
            if listed:
                reasoning = f"listed skill with {experience_months} months experience"
            else:
                reasoning = f"detected from experience evidence with {experience_months} months"
        elif listed:
            reasoning = "listed skill with no practical usage"
        else:
            reasoning = "detected skill with no practical usage"

        updated = dict(payload)
        updated["reasoning"] = reasoning
        logger.debug("Reasoning for %s: %s", name, reasoning)
        result[name] = updated

    logger.debug("Reasoning output: %s", result)
    return result
