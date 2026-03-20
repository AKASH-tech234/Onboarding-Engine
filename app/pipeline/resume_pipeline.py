from modules.assembly.response_builder import build_response
from modules.enrichment.signal_builder import build_signals
from modules.extraction.skill_mapper import map_skills
from modules.normalization.skill_normalizer import normalize_skills
from modules.reasoning.reasoning_engine import generate_reasoning
from modules.scoring.confidence_engine import compute_confidence
from modules.scoring.proficiency_engine import compute_proficiency
from modules.validation.input_validator import validate_input

from modules.services.llm.llm_services import extract_project_info


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


def run_pipeline(data):

    data = validate_input(data)

    data = normalize_skills(data)

    mapped = map_skills(data)

    mapped = enhance_projects_with_llm(mapped, data["projects"])  # NEW

    signals = build_signals(mapped)

    scored = compute_proficiency(signals)

    confident = compute_confidence(scored)

    explained = generate_reasoning(confident)

    response = build_response(explained)

    return response