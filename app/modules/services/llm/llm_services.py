import json

from .langchain_client import call_llm
from .prompts import SYSTEM_PROMPT, build_prompt


FALLBACK = {
    "skills": [],
    "complexity": None,
    "evidence": "",
}


def safe_parse(response: str):
    try:
        if not isinstance(response, str) or response.strip() == "":
            return None

        start = response.find("{")
        end = response.rfind("}") + 1
        if start < 0 or end <= start:
            return None

        return json.loads(response[start:end])
    except Exception:
        return None


def validate_llm_output(data, description):
    if not isinstance(data, dict):
        return False

    if not isinstance(description, str):
        return False

    if "skills" not in data or "complexity" not in data or "evidence" not in data:
        return False

    if not isinstance(data.get("skills"), list):
        return False

    if data.get("complexity") not in ("low", "medium", "high", None):
        return False

    evidence = data.get("evidence", "")
    if evidence is None:
        return False
    if not isinstance(evidence, str):
        return False
    if evidence and evidence not in description:
        return False

    description_lower = description.lower()
    cleaned_skills: list[str] = []
    for skill in data.get("skills", []):
        if not isinstance(skill, str):
            return False
        normalized = skill.strip()
        if normalized == "":
            return False
        if normalized.lower() not in description_lower:
            return False
        cleaned_skills.append(normalized)

    data["skills"] = cleaned_skills
    data["evidence"] = evidence

    return True


def extract_project_info(description: str):
    if not isinstance(description, str) or description.strip() == "":
        return dict(FALLBACK)

    user_prompt = build_prompt(description)

    try:
        raw = call_llm(SYSTEM_PROMPT, user_prompt)
        parsed = safe_parse(raw)
    except Exception:
        return dict(FALLBACK)

    if not validate_llm_output(parsed, description):
        return dict(FALLBACK)

    return parsed