"""Input validation for deterministic resume parsing."""

from __future__ import annotations

from utils.logger import get_logger


logger = get_logger("validation")


REQUIRED_KEYS = ("skills", "projects", "experience")


def _clean_list_of_strings(items: list, field_name: str) -> list[str]:
    cleaned: list[str] = []

    for idx, item in enumerate(items):
        if item is None:
            continue
        if not isinstance(item, str):
            raise ValueError(f"{field_name}[{idx}] must be a string")

        stripped = item.strip()
        if stripped == "":
            continue
        if stripped not in cleaned:
            cleaned.append(stripped)

    return cleaned


def _clean_skill_sources(raw: dict) -> dict[str, list[str]]:
    cleaned: dict[str, list[str]] = {}
    for skill, sources in raw.items():
        if not isinstance(skill, str):
            continue
        if not isinstance(sources, list):
            continue

        normalized_skill = skill.strip().lower()
        if normalized_skill == "":
            continue

        cleaned_sources = _clean_list_of_strings(sources, "skill_sources")
        if cleaned_sources:
            cleaned[normalized_skill] = cleaned_sources

    return cleaned


def _clean_list_of_dicts(items: list, field_name: str) -> list[dict]:
    cleaned: list[dict] = []

    for idx, item in enumerate(items):
        if item is None or item == {}:
            continue
        if not isinstance(item, dict):
            raise ValueError(f"{field_name}[{idx}] must be an object")

        cleaned_item: dict = {}
        for key, value in item.items():
            if value is None:
                continue
            if isinstance(value, str):
                stripped = value.strip()
                if stripped == "":
                    continue
                cleaned_item[key] = stripped
            else:
                cleaned_item[key] = value

        if cleaned_item:
            cleaned.append(cleaned_item)

    return cleaned


def validate_input(data: dict) -> dict:
    logger.debug("Validation input keys: %s", list(data.keys()) if isinstance(data, dict) else type(data))

    if not isinstance(data, dict):
        raise ValueError("Input payload must be an object")

    for key in REQUIRED_KEYS:
        if key not in data:
            raise ValueError(f"Missing required key: {key}")

    skills = data["skills"]
    projects = data["projects"]
    experience = data["experience"]

    if not isinstance(skills, list):
        raise ValueError("skills must be a list")
    if not isinstance(projects, list):
        raise ValueError("projects must be a list")
    if not isinstance(experience, list):
        raise ValueError("experience must be a list")

    cleaned_skills: list[str] = []
    for idx, skill in enumerate(skills):
        if skill is None:
            continue
        if not isinstance(skill, str):
            raise ValueError(f"skills[{idx}] must be a string")
        stripped = skill.strip()
        if stripped == "":
            continue
        cleaned_skills.append(stripped)

    cleaned_projects = _clean_list_of_dicts(projects, "projects")
    cleaned_experience = _clean_list_of_dicts(experience, "experience")

    validated = {
        "skills": cleaned_skills,
        "projects": cleaned_projects,
        "experience": cleaned_experience,
    }

    # Preserve optional deterministic metadata used by downstream mapping/scoring.
    skill_sources = data.get("skill_sources")
    if isinstance(skill_sources, dict):
        validated["skill_sources"] = _clean_skill_sources(skill_sources)

    training_skills = data.get("training_skills")
    if isinstance(training_skills, list):
        validated["training_skills"] = _clean_list_of_strings(
            training_skills,
            "training_skills",
        )

    project_technology_skills = data.get("project_technology_skills")
    if isinstance(project_technology_skills, list):
        validated["project_technology_skills"] = _clean_list_of_strings(
            project_technology_skills,
            "project_technology_skills",
        )

    if isinstance(data.get("debug"), bool):
        validated["debug"] = data["debug"]

    logger.debug("Validation output: %s", validated)
    return validated
