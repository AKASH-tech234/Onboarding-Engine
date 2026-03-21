from pipeline.resume_pipeline import run_pipeline
from pipeline import resume_pipeline
from schemas.request import (
    JobDescriptionInput,
    ParseRequest,
    ResumeInput,
    jd_to_pipeline_input,
    payload_to_pipeline_input,
)


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
    valid_structured_sources = {
        "skills",
        "technical_skills.programming_languages",
        "technical_skills.databases",
        "technical_skills.web_technologies",
        "technical_skills.tools",
        "training",
        "training.manual_testing",
        "training.automation_testing",
        "project.technologies",
    }

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
            assert item in valid_structured_sources or any(item in src for src in valid_sources)


def test_total_skills_and_python_output_fields() -> None:
    sample = _build_sample_input()
    result = run_pipeline(sample)

    assert result["meta"]["total_skills"] == len(result["candidate_profile"]["skills"])

    python_skill = _skill_by_name(result, "python")
    assert "score" in python_skill
    assert "confidence" in python_skill
    assert "reasoning" in python_skill
    assert "evidence" in python_skill


def test_combined_candidate_and_requirement_output() -> None:
    wrapped = {
        "resume": {
            "personal_info": {
                "name": "Himanshu",
                "phone": "9000000000",
                "email": "Apna@gmail.com",
                "gender": "male",
                "date_of_birth": "July 14, 1994",
                "father_name": "K. Upendar",
                "permanent_address": "Addr1",
                "contact_address": "Addr2",
            },
            "career_objective": "",
            "education": [
                {
                    "degree": "B.Tech (ECE)",
                    "institution": "Visveswaraya College, JNTU",
                    "year": "2011-2015",
                    "percentage": "70%",
                }
            ],
            "technical_skills": {
                "programming_languages": ["Java"],
                "databases": ["SQL Server"],
                "web_technologies": ["HTML", "JavaScript"],
                "technologies": ["Data Structures"],
                "testing_tools": ["Selenium WebDriver", "TestNG"],
                "test_management_tools": ["Jira"],
                "configuration_tools": ["MS VSS 6.0"],
                "defect_tracking_tools": ["Bugzilla 3.3"],
                "operating_systems": ["Windows XP"],
            },
            "training": {
                "manual_testing": ["SDLC"],
                "automation_testing": ["Selenium WebDriver"],
                "additional_training": ["Test Case Authoring"],
                "institute": "Q Edge Technologies",
            },
            "project": {
                "name": "K-algorithm",
                "duration": "8 months",
                "role": "Team Leader",
                "technologies": ["Microprocessor"],
                "description": "Built a Selenium WebDriver demo harness",
            },
            "skills": {"personal_skills": ["Analytical skills", "Hardworking"]},
            "extra_curricular": ["Sports"],
            "declaration": {
                "statement": "True to best of my knowledge",
                "place": "",
                "date": "",
            },
        },
        "jd": {
            "job_title": "Software Test Engineer (Fresher)",
            "job_location": "Hyderabad",
            "employment_type": "Full-Time",
            "experience_required": "0-1 Years",
            "salary_range": "2.5 LPA - 4 LPA",
            "job_summary": "Need Selenium WebDriver and TestNG with SDLC knowledge",
            "key_responsibilities": [
                "Design and execute test cases",
                "Develop automation scripts using Selenium WebDriver",
            ],
            "required_skills": {
                "manual_testing": ["SDLC and STLC knowledge"],
                "automation_testing": ["Selenium WebDriver", "TestNG"],
                "tools": ["Jira", "Bugzilla"],
                "technical_skills": ["Core Java", "SQL basics"],
            },
            "preferred_qualifications": ["B.Tech / B.E"],
            "soft_skills": ["Analytical thinking", "Willingness to learn"],
            "selection_process": ["Aptitude", "Technical", "HR"],
            "company_details": {
                "company_name": "ABC Technologies",
                "industry": "IT",
                "website": "https://www.abctech.com",
            },
            "benefits": ["Health insurance"],
        },
    }

    parsed_request = ParseRequest(
        resume=ResumeInput(**wrapped["resume"]),
        jd=JobDescriptionInput(**wrapped["jd"]),
    )
    resume_input = payload_to_pipeline_input(parsed_request)
    jd_input = jd_to_pipeline_input(parsed_request.jd)

    result = run_pipeline(resume_input, jd_data=jd_input)

    assert "candidate_profile" in result
    assert "requirement_profile" in result
    assert result["meta"]["required_total_skills"] == len(result["requirement_profile"]["skills"])

    requirement_names = {item["name"] for item in result["requirement_profile"]["skills"]}
    assert "selenium webdriver" in requirement_names


def test_pipeline_adds_llm_project_skill_when_valid(monkeypatch) -> None:
    sample = {
        "skills": ["Python"],
        "projects": [
            {
                "name": "Graph",
                "description": "Implemented graph algorithm in C++",
            }
        ],
        "experience": [],
    }

    monkeypatch.setattr(
        resume_pipeline,
        "extract_project_info",
        lambda _desc: {
            "skills": ["algorithm"],
            "complexity": "high",
            "evidence": "graph algorithm",
            "llm_status": "success",
        },
    )

    result = run_pipeline(sample)
    names = {skill["name"] for skill in result["candidate_profile"]["skills"]}

    assert "algorithm" in names


def test_combined_response_can_include_pathway_when_enabled() -> None:
    sample = {
        "skills": ["python"],
        "projects": [],
        "experience": [],
    }
    jd_input = {
        "skills": ["machine learning", "deep learning"],
        "projects": [],
        "experience": [],
    }

    result = run_pipeline(sample, jd_data=jd_input, include_pathway=True)

    assert "pathway" in result
    assert "phases" in result["pathway"]
    assert "meta" in result["pathway"]


def test_combined_response_pathway_failure_returns_reason_code(monkeypatch) -> None:
    sample = {
        "skills": ["python"],
        "projects": [],
        "experience": [],
    }
    jd_input = {
        "skills": ["machine learning"],
        "projects": [],
        "experience": [],
    }

    def _raise_pathway_failure(**_kwargs):
        raise ValueError("cycle_detected: synthetic test")

    monkeypatch.setattr(resume_pipeline, "build_pathway", _raise_pathway_failure)

    result = run_pipeline(sample, jd_data=jd_input, include_pathway=True)

    assert "pathway" in result
    assert result["pathway"]["meta"]["total_items"] == 0
    assert result["pathway"]["meta"]["reason_code"] == "cycle_detected"


def test_combined_response_excludes_pathway_by_default() -> None:
    sample = {
        "skills": ["python"],
        "projects": [],
        "experience": [],
    }
    jd_input = {
        "skills": ["machine learning", "deep learning"],
        "projects": [],
        "experience": [],
    }

    result = run_pipeline(sample, jd_data=jd_input)
    assert "pathway" not in result


def test_pathway_integration_is_deterministic() -> None:
    sample = {
        "skills": ["python"],
        "projects": [],
        "experience": [],
    }
    jd_input = {
        "skills": ["machine learning", "deep learning"],
        "projects": [],
        "experience": [],
    }

    first = run_pipeline(sample, jd_data=jd_input, include_pathway=True)
    second = run_pipeline(sample, jd_data=jd_input, include_pathway=True)

    assert first == second


def test_pathway_phase_size_affects_grouping() -> None:
    sample = {
        "skills": ["python"],
        "projects": [],
        "experience": [],
    }
    jd_input = {
        "skills": ["python", "sql", "machine learning", "deep learning"],
        "projects": [],
        "experience": [],
    }

    result = run_pipeline(
        sample,
        jd_data=jd_input,
        include_pathway=True,
        pathway_phase_size=1,
    )

    assert "pathway" in result
    assert result["pathway"]["meta"]["total_phases"] >= 2


def test_invalid_pathway_phase_size_raises_value_error() -> None:
    sample = {
        "skills": ["python"],
        "projects": [],
        "experience": [],
    }
    jd_input = {
        "skills": ["machine learning"],
        "projects": [],
        "experience": [],
    }

    try:
        run_pipeline(
            sample,
            jd_data=jd_input,
            include_pathway=True,
            pathway_phase_size=0,
        )
    except ValueError as exc:
        assert "pathway_phase_size" in str(exc)
        return

    raise AssertionError("Expected ValueError for invalid phase size")


def test_pathway_inputs_are_derived_from_parsed_profiles(monkeypatch) -> None:
    captured = {}

    def _fake_run_skill_flow(_data, use_llm):
        return {"python": {"name": "python"}} if use_llm else {"ml": {"name": "ml"}}

    def _fake_build_response(_skills, profile_key="candidate_profile", total_key="total_skills"):
        if profile_key == "candidate_profile":
            return {
                "version": "1.0",
                "candidate_profile": {
                    "skills": [{"name": "PyThOn"}],
                },
                "meta": {"total_skills": 1},
            }

        return {
            "version": "1.0",
            "requirement_profile": {
                "skills": [{"name": "PYTHON"}, {"name": "Machine Learning"}],
            },
            "meta": {"required_total_skills": 2},
        }

    def _fake_build_pathway(missing_skills, candidate_skills=None, graph=None, phase_size=3):
        captured["missing_skills"] = missing_skills
        captured["candidate_skills"] = candidate_skills
        return {
            "ordered": [],
            "phases": [],
            "meta": {"total_items": 0, "total_phases": 0, "reason_code": "ok"},
        }

    monkeypatch.setattr(resume_pipeline, "_run_skill_flow", _fake_run_skill_flow)
    monkeypatch.setattr(resume_pipeline, "build_response", _fake_build_response)
    monkeypatch.setattr(resume_pipeline, "build_pathway", _fake_build_pathway)

    result = run_pipeline(
        {"skills": ["python"], "projects": [], "experience": []},
        jd_data={"skills": ["machine learning"], "projects": [], "experience": []},
        include_pathway=True,
    )

    assert "pathway" in result
    assert captured["candidate_skills"] == {"python"}
    assert captured["missing_skills"] == ["machine learning"]


def test_derive_pathway_inputs_normalizes_profile_names() -> None:
    candidate_response = {
        "candidate_profile": {
            "skills": [{"name": "  PYTHON "}, {"name": "Sql"}],
        }
    }
    requirement_response = {
        "requirement_profile": {
            "skills": [{"name": "python"}, {"name": " MACHINE LEARNING "}, {"name": "SQL"}],
        }
    }

    candidate_names, missing = resume_pipeline._derive_pathway_inputs(
        candidate_response,
        requirement_response,
    )

    assert candidate_names == {"python", "sql"}
    assert missing == ["machine learning"]
