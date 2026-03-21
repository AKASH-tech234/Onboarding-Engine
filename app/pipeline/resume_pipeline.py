import os

from modules.assembly.response_builder import build_response
from modules.enrichment.signal_builder import build_signals
from modules.extraction.skill_mapper import map_skills
from modules.normalization.skill_normalizer import normalize_skills
from modules.reasoning.reasoning_engine import generate_reasoning
from modules.scoring.confidence_engine import compute_confidence
from modules.scoring.proficiency_engine import compute_proficiency
from modules.validation.input_validator import validate_input

from modules.services.llm.llm_services import (
    LLM_STATUS_SUCCESS,
    LLM_STATUS_PARTIAL_ACCEPTED,
    extract_project_info,
)
from modules.pathway.pathway_builder import build_pathway
from modules.pathway.response_builder import build_pathway_response
from utils.logger import get_logger


logger = get_logger("pipeline")


def _reason_code_from_error(err: Exception) -> str:
    message = str(err or "").strip()
    if not message:
        return "pathway_unavailable"
    if ":" in message:
        candidate = message.split(":", 1)[0].strip().lower().replace(" ", "_")
        if candidate:
            return candidate
    return "pathway_unavailable"


def _extract_normalized_profile_skill_names(profile: dict) -> set[str]:
    names: set[str] = set()
    if not isinstance(profile, dict):
        return names

    skills = profile.get("skills", [])
    if not isinstance(skills, list):
        return names

    for item in skills:
        if not isinstance(item, dict):
            continue
        raw_name = item.get("name", "")
        if not isinstance(raw_name, str):
            continue
        normalized = raw_name.strip().lower()
        if normalized:
            names.add(normalized)
    return names


def _derive_pathway_inputs(candidate_response: dict, requirement_response: dict) -> tuple[set[str], list[str]]:
    candidate_profile = candidate_response.get("candidate_profile", {}) if isinstance(candidate_response, dict) else {}
    requirement_profile = requirement_response.get("requirement_profile", {}) if isinstance(requirement_response, dict) else {}

    candidate_names = _extract_normalized_profile_skill_names(candidate_profile)
    required_names = sorted(_extract_normalized_profile_skill_names(requirement_profile))
    missing = [name for name in required_names if name not in candidate_names]

    logger.debug(
        "Derived pathway inputs from parsed profiles: candidate=%d required=%d missing=%d",
        len(candidate_names),
        len(required_names),
        len(missing),
    )
    return candidate_names, missing


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

        llm_status = result.get("llm_status", "fallback")
        logger.debug("LLM status for project '%s': %s", project.get("name", "unknown"), llm_status)
        if llm_status not in {LLM_STATUS_SUCCESS, LLM_STATUS_PARTIAL_ACCEPTED}:
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

            if normalized_skill not in mapped:
                mapped[normalized_skill] = {
                    "name": normalized_skill,
                    "listed": False,
                    "projects": 0,
                    "experience_months": 0,
                    "evidence": [],
                }

            mapped[normalized_skill]["projects"] += 1

            evidence_list = mapped[normalized_skill].setdefault("evidence", [])
            if not isinstance(evidence_list, list):
                mapped[normalized_skill]["evidence"] = []
                evidence_list = mapped[normalized_skill]["evidence"]

            if "llm.project_description" not in evidence_list:
                evidence_list.append("llm.project_description")

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


def run_pipeline(
    data,
    jd_data: dict | None = None,
    include_pathway: bool = False,
    pathway_phase_size: int = 3,
    scoring_profile: str = "default",
):
    logger.info("Starting pipeline")

    try:
        if pathway_phase_size <= 0:
            raise ValueError("pathway_phase_size must be greater than zero")
        if not isinstance(scoring_profile, str) or scoring_profile.strip() == "":
            raise ValueError("scoring_profile must be a non-empty string")

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

        if include_pathway:
            candidate_names, missing = _derive_pathway_inputs(
                candidate_response,
                requirement_response,
            )

            try:
                pathway = build_pathway(
                    missing_skills=missing,
                    candidate_skills=candidate_names,
                    phase_size=pathway_phase_size,
                )
            except ValueError as err:
                reason_code = _reason_code_from_error(err)
                logger.warning("Pathway generation failed; reason_code=%s error=%s", reason_code, err)
                pathway = {
                    "ordered": [],
                    "phases": [],
                    "meta": {
                        "total_items": 0,
                        "total_phases": 0,
                        "reason_code": reason_code,
                    },
                }

            combined_response["pathway"] = build_pathway_response(pathway)

        logger.debug("Final response: %s", combined_response)
        return combined_response
    except Exception as e:
        logger.error("Pipeline failed: %s", str(e))
        raise