from modules.assembly.response_builder import build_response
from modules.enrichment.signal_builder import build_signals
from modules.reasoning.reasoning_engine import generate_reasoning
from modules.scoring.confidence_engine import compute_confidence
from modules.scoring.proficiency_engine import compute_proficiency
from pipeline.resume_pipeline import run_pipeline


SAMPLE_INPUT = {
    "skills": ["Python", "React"],
    "projects": [
        {
            "name": "Chat App",
            "description": "Built using Node.js and Socket.io",
        }
    ],
    "experience": [
        {
            "role": "Backend Intern",
            "description": "Worked on Python Django APIs",
            "duration": "Jan 2023 - Jun 2023",
        }
    ],
}


BASE_SKILLS = {
    "python": {
        "name": "python",
        "listed": True,
        "projects": 1,
        "experience_months": 6,
        "evidence": ["Worked on Python Django APIs"],
    },
    "react": {
        "name": "react",
        "listed": True,
        "projects": 0,
        "experience_months": 0,
        "evidence": [],
    },
}


def _skill_by_name(response: dict, name: str) -> dict:
    for skill in response["candidate_profile"]["skills"]:
        if skill["name"] == name:
            return skill
    raise AssertionError(f"Skill '{name}' was not found")


def test_build_signals_uses_required_formulas() -> None:
    skills = {
        "python": {
            "name": "python",
            "listed": True,
            "projects": 1,
            "experience_months": 6,
            "evidence": [],
        },
        "java": {
            "name": "java",
            "listed": False,
            "projects": 3,
            "experience_months": 24,
            "evidence": [],
        },
    }

    enriched = build_signals(skills)

    py = enriched["python"]["signals"]
    assert py["frequency"] == 1 / 3
    assert py["duration"] == 0.25
    assert py["complexity"] == 0.5
    assert py["recency"] == 0.9

    java = enriched["java"]["signals"]
    assert java["frequency"] == 1.0
    assert java["duration"] == 1.0
    assert java["complexity"] == 0.7
    assert java["recency"] == 0.9


def test_compute_proficiency_assigns_score_and_level() -> None:
    with_signals = build_signals(BASE_SKILLS)
    scored = compute_proficiency(with_signals)

    py = scored["python"]
    expected_py = round(0.2 * 1 + 0.3 * (1 / 3) + 0.3 * 0.25 + 0.2 * 0.9, 4)
    assert py["score"] == expected_py
    assert py["level"] == "intermediate"

    react = scored["react"]
    expected_react = round(0.2 * 1 + 0.3 * 0 + 0.3 * 0 + 0.2 * 0.3, 4)
    assert react["score"] == expected_react
    assert react["level"] == "beginner"


def test_compute_confidence_uses_rule_weights_and_caps() -> None:
    with_signals = build_signals(BASE_SKILLS)
    scored = compute_proficiency(with_signals)
    confident = compute_confidence(scored)

    py = confident["python"]
    assert py["confidence"] == 1.0

    react = confident["react"]
    assert react["confidence"] == 0.0


def test_generate_reasoning_is_template_based_and_non_empty() -> None:
    with_signals = build_signals(BASE_SKILLS)
    scored = compute_proficiency(with_signals)
    confident = compute_confidence(scored)
    explained = generate_reasoning(confident)

    assert explained["python"]["reasoning"] == "used in 1 projects and 6 months experience"
    assert explained["react"]["reasoning"] == "listed skill with no practical usage"


def test_build_response_has_expected_contract() -> None:
    with_signals = build_signals(BASE_SKILLS)
    scored = compute_proficiency(with_signals)
    confident = compute_confidence(scored)
    explained = generate_reasoning(confident)
    response = build_response(explained)

    assert response["version"] == "1.0"
    assert "candidate_profile" in response
    assert "skills" in response["candidate_profile"]
    assert response["meta"]["total_skills"] == 2


def test_pipeline_sample_resume_generates_desired_output() -> None:
    result = run_pipeline(SAMPLE_INPUT)

    python_skill = _skill_by_name(result, "python")
    assert python_skill["name"] == "python"
    assert python_skill["score"] == 0.455
    assert python_skill["level"] == "intermediate"
    assert python_skill["confidence"] > 0
    assert python_skill["reasoning"]
    assert python_skill["evidence"]

    assert result["meta"]["total_skills"] == 3


def test_pipeline_is_deterministic_for_same_input() -> None:
    result_a = run_pipeline(SAMPLE_INPUT)
    result_b = run_pipeline(SAMPLE_INPUT)

    assert result_a == result_b
