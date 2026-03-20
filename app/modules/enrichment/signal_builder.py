"""Build deterministic normalized signals from mapped skill data."""

from __future__ import annotations

from utils.logger import get_logger


logger = get_logger("signals")


def _clamp(value: float) -> float:
    return max(0.0, min(value, 1.0))


def build_signals(skills: dict) -> dict:
    logger.debug("Signal builder input: %s", skills)

    if not isinstance(skills, dict):
        raise ValueError("skills must be a dictionary")

    result: dict = {}
    for name in sorted(skills.keys()):
        payload = skills[name]
        if not isinstance(payload, dict):
            raise ValueError(f"Skill payload for '{name}' must be an object")

        projects = payload.get("projects", 0)
        experience_months = payload.get("experience_months", 0)
        evidence = payload.get("evidence", [])

        if not isinstance(projects, int):
            raise ValueError(f"projects for '{name}' must be an integer")
        if not isinstance(experience_months, int):
            raise ValueError(f"experience_months for '{name}' must be an integer")
        if not isinstance(evidence, list):
            raise ValueError(f"evidence for '{name}' must be a list")

        evidence_lower = [item.lower() for item in evidence if isinstance(item, str)]

        has_project_technology_source = any(
            item == "project.technologies" or item.startswith("project.technologies")
            for item in evidence_lower
        )
        has_training_source = any(
            item == "training" or item.startswith("training.")
            for item in evidence_lower
        )

        effective_projects = projects + (1 if has_project_technology_source else 0)

        frequency = _clamp(effective_projects / 3.0)
        if has_training_source:
            frequency = _clamp(frequency + 0.5)
        duration = _clamp(experience_months / 24.0)

        if effective_projects >= 2:
            complexity = 0.7
        elif effective_projects == 1:
            complexity = 0.5
        else:
            complexity = 0.2

        if experience_months > 0:
            recency = 0.9
        elif effective_projects > 0:
            recency = 0.7
        else:
            recency = 0.3

        updated = dict(payload)
        updated["signals"] = {
            "frequency": _clamp(frequency),
            "duration": _clamp(duration),
            "complexity": _clamp(complexity),
            "recency": _clamp(recency),
        }
        logger.debug(
            "Signals for %s -> freq=%.2f, duration=%.2f, recency=%.2f",
            name,
            updated["signals"]["frequency"],
            updated["signals"]["duration"],
            updated["signals"]["recency"],
        )
        result[name] = updated

    logger.debug("Signal builder output: %s", result)
    return result
