import os

from modules.assembly.response_builder import build_response
from modules.enrichment.signal_builder import build_signals
from modules.extraction.skill_mapper import map_skills
from modules.normalization.skill_normalizer import normalize_skills
from modules.reasoning.reasoning_engine import generate_reasoning
from modules.scoring.confidence_engine import compute_confidence
from modules.scoring.proficiency_engine import compute_proficiency
from modules.validation.input_validator import validate_input

from modules.services.llm.llm_services import extract_project_info
from utils.logger import get_logger


logger = get_logger("pipeline")


def _is_debug_enabled(data: dict) -> bool:
    if isinstance(data, dict) and isinstance(data.get("debug"), bool):
        return data["debug"]

    env_value = os.getenv("PIPELINE_DEBUG", "").strip().lower()
    return env_value in {"1", "true", "yes", "on"}


def _debug_print(label: str, payload: dict, enabled: bool) -> None:
    if not enabled:
        return
    print(f"[PIPELINE DEBUG] {label}: {payload}")


def _redact_sensitive(payload: dict) -> dict:
    if not isinstance(payload, dict):
        return payload

    redacted = {}
    for key, value in payload.items():
        if key.lower() in {"email", "phone", "mobile", "contact"}:
            redacted[key] = "[REDACTED]"
        elif isinstance(value, dict):
            redacted[key] = _redact_sensitive(value)
        elif isinstance(value, list):
            redacted[key] = [
                _redact_sensitive(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            redacted[key] = value
    return redacted


def enhance_projects_with_llm(mapped: dict, projects: list[dict]) -> dict:
    if not isinstance(mapped, dict):
        return {}
    if not isinstance(projects, list):
        return mapped

    for project in projects:
        if not isinstance(project, dict):
            continue

        description = project.get("description", "")
        if not isinstance(description, str) or description.strip() == "":
            continue

        try:
            result = extract_project_info(description)
        except Exception:
            continue

        if not isinstance(result, dict):
            continue

        evidence = result.get("evidence", "")
        skills = result.get("skills", [])
        if not isinstance(skills, list):
            continue

        for skill in skills:
            if not isinstance(skill, str):
                continue
            normalized_skill = skill.strip().lower()
            if normalized_skill == "":
                continue

            if normalized_skill in mapped:
                mapped[normalized_skill]["projects"] += 1

                evidence_list = mapped[normalized_skill].setdefault("evidence", [])
                if not isinstance(evidence_list, list):
                    mapped[normalized_skill]["evidence"] = []
                    evidence_list = mapped[normalized_skill]["evidence"]

                if isinstance(evidence, str) and evidence and evidence not in evidence_list:
                    evidence_list.append(evidence)

    return mapped


def _run_skill_flow(data: dict, use_llm: bool) -> dict:
    debug_enabled = _is_debug_enabled(data)

    validated = validate_input(data)
    logger.debug("After validation: %s", _redact_sensitive(validated))
    normalized = normalize_skills(validated)
    logger.debug("After normalization: %s", _redact_sensitive(normalized))
    mapped = map_skills(normalized)
    logger.debug("Mapped skills: %s", mapped)
    _debug_print("mapped", mapped, debug_enabled)

    if use_llm:
        mapped = enhance_projects_with_llm(mapped, normalized["projects"])

    signals = build_signals(mapped)
    logger.debug("Signals: %s", signals)
    _debug_print("signals", signals, debug_enabled)
    scored = compute_proficiency(signals)
    logger.debug("Scores: %s", scored)
    _debug_print("scored", scored, debug_enabled)

    score_values = [payload.get("score") for payload in scored.values() if isinstance(payload, dict)]
    unique_scores = {value for value in score_values if isinstance(value, (int, float))}
    if len(unique_scores) == 1 and len(score_values) > 1:
        logger.warning("Flat scoring detected: all skills share score %.4f", score_values[0])

    missing_evidence = [
        name
        for name, payload in scored.items()
        if isinstance(payload, dict)
        and not any(isinstance(item, str) and item for item in payload.get("evidence", []))
    ]
    if missing_evidence:
        logger.warning("Skills with missing evidence: %s", missing_evidence)

    confident = compute_confidence(scored)
    logger.debug("Confidence: %s", confident)
    explained = generate_reasoning(confident)
    return explained


def run_pipeline(data, jd_data: dict | None = None):
    logger.info("Starting pipeline")

    try:
        candidate_skills = _run_skill_flow(data, use_llm=True)

        candidate_response = build_response(candidate_skills)

        if jd_data is None:
            logger.debug("Final response: %s", candidate_response)
            return candidate_response

        requirement_skills = _run_skill_flow(jd_data, use_llm=False)
        requirement_response = build_response(
            requirement_skills,
            profile_key="requirement_profile",
            total_key="required_total_skills",
        )

        combined_response = {
            "version": "1.0",
            "candidate_profile": candidate_response["candidate_profile"],
            "requirement_profile": requirement_response["requirement_profile"],
            "meta": {
                "total_skills": candidate_response["meta"]["total_skills"],
                "required_total_skills": requirement_response["meta"]["required_total_skills"],
            },
        }
        logger.debug("Final response: %s", combined_response)
        return combined_response
    except Exception as e:
        logger.error("Pipeline failed: %s", str(e))
        raise