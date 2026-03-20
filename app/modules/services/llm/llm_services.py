import json
import re
from json import JSONDecodeError

from .langchain_client import call_llm
from .prompts import SYSTEM_PROMPT, build_prompt
from utils.logger import get_logger


logger = get_logger("llm")


FALLBACK = {
    "skills": [],
    "complexity": None,
    "evidence": "",
    "llm_status": "fallback",
}

LLM_STATUS_SUCCESS = "success"
LLM_STATUS_EMPTY_INPUT = "empty_input"
LLM_STATUS_PARSE_FAILED = "parse_failed"
LLM_STATUS_VALIDATION_FAILED = "validation_failed"
LLM_STATUS_PARTIAL_ACCEPTED = "partial_accepted"
LLM_STATUS_CALL_FAILED = "call_failed"


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
    except JSONDecodeError:
        return None


def _pick_anchored_evidence(description: str, skills: list[str]) -> str:
    lowered = description.lower()
    for skill in skills:
        idx = lowered.find(skill.lower())
        if idx >= 0:
            start = max(0, idx - 20)
            end = min(len(description), idx + len(skill) + 20)
            return description[start:end].strip()
    return ""


def validate_llm_output(data, description):
    if not isinstance(data, dict):
        return None, LLM_STATUS_VALIDATION_FAILED

    if not isinstance(description, str):
        return None, LLM_STATUS_VALIDATION_FAILED

    if "skills" not in data or "complexity" not in data or "evidence" not in data:
        return None, LLM_STATUS_VALIDATION_FAILED

    if not isinstance(data.get("skills"), list):
        return None, LLM_STATUS_VALIDATION_FAILED

    if data.get("complexity") not in ("low", "medium", "high", None):
        return None, LLM_STATUS_VALIDATION_FAILED

    evidence = data.get("evidence", "")
    if evidence is None:
        return None, LLM_STATUS_VALIDATION_FAILED
    if not isinstance(evidence, str):
        return None, LLM_STATUS_VALIDATION_FAILED

    description_lower = description.lower()
    cleaned_skills: list[str] = []
    dropped_count = 0
    for skill in data.get("skills", []):
        if not isinstance(skill, str):
            dropped_count += 1
            continue
        normalized = skill.strip()
        if normalized == "":
            dropped_count += 1
            continue
        if normalized.lower() not in description_lower:
            dropped_count += 1
            continue
        if normalized not in cleaned_skills:
            cleaned_skills.append(normalized)

    if evidence and evidence not in description:
        logger.debug("LLM evidence was not exact substring; attempting anchored fallback")
        anchored = _pick_anchored_evidence(description, cleaned_skills)
        evidence = anchored

    if not cleaned_skills:
        return None, LLM_STATUS_VALIDATION_FAILED

    cleaned = {
        "skills": cleaned_skills,
        "complexity": data.get("complexity"),
        "evidence": evidence,
        "llm_status": LLM_STATUS_SUCCESS if dropped_count == 0 else LLM_STATUS_PARTIAL_ACCEPTED,
    }

    return cleaned, cleaned["llm_status"]


def extract_project_info(description: str):
    if not isinstance(description, str) or description.strip() == "":
        fallback = dict(FALLBACK)
        fallback["llm_status"] = LLM_STATUS_EMPTY_INPUT
        return fallback

    logger.debug("LLM input: %s", _sanitize_text(description))

    user_prompt = build_prompt(description)

    try:
        raw = call_llm(SYSTEM_PROMPT, user_prompt)
        logger.debug("LLM raw output: %s", raw)
        parsed = safe_parse(raw)
        logger.debug("LLM parsed output: %s", parsed)
    except Exception as exc:
        logger.warning("LLM call failed: %s", exc.__class__.__name__)
        fallback = dict(FALLBACK)
        fallback["llm_status"] = LLM_STATUS_CALL_FAILED
        return fallback

    if parsed is None:
        logger.warning("LLM output rejected (parse failed)")
        fallback = dict(FALLBACK)
        fallback["llm_status"] = LLM_STATUS_PARSE_FAILED
        return fallback

    cleaned, status = validate_llm_output(parsed, description)
    if cleaned is None:
        logger.warning("LLM output rejected")
        fallback = dict(FALLBACK)
        fallback["llm_status"] = status
        return fallback

    if status == LLM_STATUS_PARTIAL_ACCEPTED:
        logger.warning("LLM output partially accepted")

    return cleaned