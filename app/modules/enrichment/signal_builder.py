"""Build deterministic normalized signals from mapped skill data."""

from __future__ import annotations


def _clamp(value: float) -> float:
    return max(0.0, min(value, 1.0))


def build_signals(skills: dict) -> dict:
    if not isinstance(skills, dict):
        raise ValueError("skills must be a dictionary")

    result: dict = {}
    for name in sorted(skills.keys()):
        payload = skills[name]
        if not isinstance(payload, dict):
            raise ValueError(f"Skill payload for '{name}' must be an object")

        projects = payload.get("projects", 0)
        experience_months = payload.get("experience_months", 0)

        if not isinstance(projects, int):
            raise ValueError(f"projects for '{name}' must be an integer")
        if not isinstance(experience_months, int):
            raise ValueError(f"experience_months for '{name}' must be an integer")

        frequency = _clamp(projects / 3.0)
        duration = _clamp(experience_months / 24.0)

        if projects >= 2:
            complexity = 0.7
        elif projects == 1:
            complexity = 0.5
        else:
            complexity = 0.2

        if experience_months > 0:
            recency = 0.9
        elif projects > 0:
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
        result[name] = updated

    return result
