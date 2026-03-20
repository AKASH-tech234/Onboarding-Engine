"""Input validation for deterministic resume parsing."""

from __future__ import annotations


REQUIRED_KEYS = ("skills", "projects", "experience")


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

    return {
        "skills": cleaned_skills,
        "projects": cleaned_projects,
        "experience": cleaned_experience,
    }
