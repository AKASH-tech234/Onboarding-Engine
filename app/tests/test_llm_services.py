from modules.services.llm import llm_services


def test_validate_llm_output_partial_acceptance_keeps_valid_skills() -> None:
    description = "Built a Python API and optimized algorithm complexity"
    data = {
        "skills": ["Python", "HallucinatedSkill"],
        "complexity": "high",
        "evidence": "optimized algorithm complexity",
    }

    cleaned, status = llm_services.validate_llm_output(data, description)

    assert cleaned is not None
    assert status == llm_services.LLM_STATUS_PARTIAL_ACCEPTED
    assert cleaned["skills"] == ["Python"]
    assert cleaned["evidence"] == "optimized algorithm complexity"


def test_extract_project_info_parse_fail_returns_fallback_status(monkeypatch) -> None:
    monkeypatch.setattr(llm_services, "call_llm", lambda _s, _u: "not-json")

    result = llm_services.extract_project_info("Built Python tooling")

    assert result["skills"] == []
    assert result["llm_status"] == llm_services.LLM_STATUS_PARSE_FAILED


def test_extract_project_info_accepts_valid_output(monkeypatch) -> None:
    monkeypatch.setattr(
        llm_services,
        "call_llm",
        lambda _s, _u: '{"skills":["Python"],"complexity":"medium","evidence":"Python"}',
    )

    result = llm_services.extract_project_info("Used Python for backend services")

    assert result["skills"] == ["Python"]
    assert result["llm_status"] == llm_services.LLM_STATUS_SUCCESS
