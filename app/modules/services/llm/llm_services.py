import json
import re

from .langchain_client import call_llm
from .prompts import SYSTEM_PROMPT, build_prompt
from utils.logger import get_logger


logger = get_logger("llm")


FALLBACK = {
    "skills": [],
    "complexity": None,
    "evidence": "",
}


def _sanitize_text(text: str) -> str:
    if not isinstance(text, str):
        return ""

    sanitized = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]", text)
    sanitized = re.sub(r"\b\d{10}\b", "[REDACTED_PHONE]", sanitized)
    return sanitized


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

    logger.debug("LLM input: %s", _sanitize_text(description))

    user_prompt = build_prompt(description)

    try:
        raw = call_llm(SYSTEM_PROMPT, user_prompt)
        logger.debug("LLM raw output: %s", raw)
        parsed = safe_parse(raw)
        logger.debug("LLM parsed output: %s", parsed)
    except Exception:
        logger.warning("LLM call failed")
        return dict(FALLBACK)

    if not validate_llm_output(parsed, description):
        logger.warning("LLM output rejected")
        return dict(FALLBACK)

    return parsed