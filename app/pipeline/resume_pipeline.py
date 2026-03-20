from modules.assembly.response_builder import build_response
from modules.enrichment.signal_builder import build_signals
from modules.extraction.skill_mapper import map_skills
from modules.normalization.skill_normalizer import normalize_skills
from modules.reasoning.reasoning_engine import generate_reasoning
from modules.scoring.confidence_engine import compute_confidence
from modules.scoring.proficiency_engine import compute_proficiency
from modules.validation.input_validator import validate_input


def run_pipeline(data: dict) -> dict:
    data = validate_input(data)
    data = normalize_skills(data)
    mapped = map_skills(data)
    signals = build_signals(mapped)
    scored = compute_proficiency(signals)
    confident = compute_confidence(scored)
    explained = generate_reasoning(confident)
    response = build_response(explained)
    return response