from pipeline.resume_pipeline import run_pipeline
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
