from pipeline.resume_pipeline import run_pipeline


def _build_sample_input() -> dict:
    return {
        "skills": ["Python"],
        "projects": [
            {"name": "Chat", "description": "Built using WebSocket"}
        ],
        "experience": [],
    }


def _skill_by_name(result: dict, name: str) -> dict:
    for skill in result["candidate_profile"]["skills"]:
        if skill["name"] == name:
            return skill
    raise AssertionError(f"missing skill: {name}")


def test_full_pipeline_runs_and_has_required_contract() -> None:
    sample = _build_sample_input()
    result = run_pipeline(sample)

    assert result["version"] == "1.0"
    assert "candidate_profile" in result
    assert "skills" in result["candidate_profile"]
    assert isinstance(result["candidate_profile"]["skills"], list)
    assert "meta" in result
    assert isinstance(result["meta"]["total_skills"], int)


def test_full_pipeline_is_deterministic() -> None:
    sample = _build_sample_input()
    first = run_pipeline(sample)
    second = run_pipeline(sample)

    assert first == second


def test_no_hallucinated_skills_from_projects() -> None:
    sample = _build_sample_input()
    result = run_pipeline(sample)

    names = {skill["name"] for skill in result["candidate_profile"]["skills"]}
    assert "python" in names
    assert "websocket" not in names


def test_evidence_integrity_and_ranges() -> None:
    sample = _build_sample_input()
    result = run_pipeline(sample)

    valid_sources = [p.get("description", "") for p in sample["projects"]] + [
        e.get("description", "") for e in sample["experience"]
    ]

    for skill in result["candidate_profile"]["skills"]:
        score = skill.get("score")
        confidence = skill.get("confidence")
        reasoning = skill.get("reasoning")
        evidence = skill.get("evidence")

        assert isinstance(score, (int, float))
        assert 0.0 <= float(score) <= 1.0

        assert isinstance(confidence, (int, float))
        assert 0.0 <= float(confidence) <= 1.0

        assert isinstance(reasoning, str)
        assert reasoning.strip() != ""

        assert isinstance(evidence, list)
        for item in evidence:
            assert isinstance(item, str)
            assert item != ""
            assert any(item in src for src in valid_sources)


def test_total_skills_and_python_output_fields() -> None:
    sample = _build_sample_input()
    result = run_pipeline(sample)

    assert result["meta"]["total_skills"] == len(result["candidate_profile"]["skills"])

    python_skill = _skill_by_name(result, "python")
    assert "score" in python_skill
    assert "confidence" in python_skill
    assert "reasoning" in python_skill
    assert "evidence" in python_skill
