from fastapi.testclient import TestClient

import main


client = TestClient(main.app)


def _resume_payload() -> dict:
    return {
        "personal_info": {
            "name": "Rahul",
            "phone": "9876543210",
            "email": "rahul@example.com",
            "gender": "male",
            "date_of_birth": "1990-01-01",
            "father_name": "Father",
            "permanent_address": "Addr1",
            "contact_address": "Addr2",
        },
        "career_objective": "Objective",
        "education": [
            {
                "degree": "B.Tech",
                "institution": "ABC",
                "year": "2011-2015",
                "percentage": "80%",
            }
        ],
        "technical_skills": {
            "programming_languages": ["Python"],
            "databases": ["MySQL"],
            "web_technologies": [],
            "technologies": ["Machine Learning"],
            "testing_tools": [],
            "test_management_tools": [],
            "configuration_tools": [],
            "defect_tracking_tools": [],
            "operating_systems": ["Linux"],
        },
        "training": {
            "manual_testing": [],
            "automation_testing": [],
            "additional_training": [],
            "institute": "Institute",
        },
        "project": {
            "name": "Pred",
            "duration": "6 months",
            "role": "DS",
            "technologies": ["Python"],
            "description": "Built python model",
        },
        "skills": {"personal_skills": ["Problem-solving"]},
        "extra_curricular": [],
        "declaration": {
            "statement": "true",
            "place": "Noida",
            "date": "2026-03-20",
        },
    }


def _jd_payload() -> dict:
    return {
        "job_title": "Data Scientist",
        "job_location": "Bangalore",
        "employment_type": "Full-Time",
        "experience_required": "2-4 Years",
        "salary_range": "6-10",
        "job_summary": "Develop ML models",
        "key_responsibilities": ["Build pipelines"],
        "required_skills": {
            "manual_testing": [],
            "automation_testing": [],
            "tools": ["TensorFlow"],
            "technical_skills": ["Python", "Machine Learning"],
        },
        "preferred_qualifications": ["MTech"],
        "soft_skills": ["Communication"],
        "selection_process": ["Technical"],
        "company_details": {
            "company_name": "ABC",
            "industry": "IT",
            "website": "https://example.com",
        },
        "benefits": ["Insurance"],
    }


def test_parse_resume_default_include_pathway_false(monkeypatch) -> None:
    captured = {}

    def _fake_run_pipeline(data, jd_data=None, include_pathway=False, pathway_phase_size=3, scoring_profile="default"):
        captured["include_pathway"] = include_pathway
        captured["has_jd"] = jd_data is not None
        captured["pathway_phase_size"] = pathway_phase_size
        captured["scoring_profile"] = scoring_profile
        return {"version": "1.0", "candidate_profile": {"skills": []}, "meta": {"total_skills": 0}}

    monkeypatch.setattr(main, "run_pipeline", _fake_run_pipeline)

    payload = {"resume": _resume_payload(), "jd": _jd_payload()}
    response = client.post("/parse-resume", json=payload)

    assert response.status_code == 200
    assert captured["has_jd"] is True
    assert captured["include_pathway"] is False
    assert captured["pathway_phase_size"] == 3
    assert captured["scoring_profile"] == "default"


def test_parse_resume_include_pathway_true_propagates(monkeypatch) -> None:
    captured = {}

    def _fake_run_pipeline(data, jd_data=None, include_pathway=False, pathway_phase_size=3, scoring_profile="default"):
        captured["include_pathway"] = include_pathway
        return {"version": "1.0", "candidate_profile": {"skills": []}, "meta": {"total_skills": 0}}

    monkeypatch.setattr(main, "run_pipeline", _fake_run_pipeline)

    payload = {"resume": _resume_payload(), "jd": _jd_payload()}
    response = client.post("/parse-resume?include_pathway=true", json=payload)

    assert response.status_code == 200
    assert captured["include_pathway"] is True


def test_parse_resume_resume_only_still_works(monkeypatch) -> None:
    def _fake_run_pipeline(data, jd_data=None, include_pathway=False, pathway_phase_size=3, scoring_profile="default"):
        assert jd_data is None
        return {"version": "1.0", "candidate_profile": {"skills": []}, "meta": {"total_skills": 0}}

    monkeypatch.setattr(main, "run_pipeline", _fake_run_pipeline)

    response = client.post("/parse-resume", json=_resume_payload())

    assert response.status_code == 200
    assert "parsed" in response.json()


def test_parse_resume_value_error_maps_to_400(monkeypatch) -> None:
    def _fake_run_pipeline(*args, **kwargs):
        raise ValueError("bad input")

    monkeypatch.setattr(main, "run_pipeline", _fake_run_pipeline)

    payload = {"resume": _resume_payload(), "jd": _jd_payload()}
    response = client.post("/parse-resume", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "bad input"


def test_parse_resume_invalid_include_pathway_value_returns_422() -> None:
    payload = {"resume": _resume_payload(), "jd": _jd_payload()}
    response = client.post("/parse-resume?include_pathway=maybe", json=payload)

    assert response.status_code == 422


def test_parse_resume_missing_required_field_returns_422() -> None:
    bad_resume = _resume_payload()
    bad_resume.pop("training")

    response = client.post("/parse-resume", json=bad_resume)
    assert response.status_code == 422


def test_parse_resume_include_pathway_numeric_true(monkeypatch) -> None:
    captured = {}

    def _fake_run_pipeline(data, jd_data=None, include_pathway=False, pathway_phase_size=3, scoring_profile="default"):
        captured["include_pathway"] = include_pathway
        return {"version": "1.0", "candidate_profile": {"skills": []}, "meta": {"total_skills": 0}}

    monkeypatch.setattr(main, "run_pipeline", _fake_run_pipeline)

    payload = {"resume": _resume_payload(), "jd": _jd_payload()}
    response = client.post("/parse-resume?include_pathway=1", json=payload)

    assert response.status_code == 200
    assert captured["include_pathway"] is True


def test_parse_resume_body_options_propagate_when_query_missing(monkeypatch) -> None:
    captured = {}

    def _fake_run_pipeline(data, jd_data=None, include_pathway=False, pathway_phase_size=3, scoring_profile="default"):
        captured["include_pathway"] = include_pathway
        captured["pathway_phase_size"] = pathway_phase_size
        captured["scoring_profile"] = scoring_profile
        return {"version": "1.0", "candidate_profile": {"skills": []}, "meta": {"total_skills": 0}}

    monkeypatch.setattr(main, "run_pipeline", _fake_run_pipeline)

    payload = {
        "resume": _resume_payload(),
        "jd": _jd_payload(),
        "options": {
            "include_pathway": True,
            "pathway_phase_size": 2,
            "scoring_profile": "balanced",
        },
    }
    response = client.post("/parse-resume", json=payload)

    assert response.status_code == 200
    assert captured["include_pathway"] is True
    assert captured["pathway_phase_size"] == 2
    assert captured["scoring_profile"] == "balanced"


def test_parse_resume_query_overrides_body_include_pathway(monkeypatch) -> None:
    captured = {}

    def _fake_run_pipeline(data, jd_data=None, include_pathway=False, pathway_phase_size=3, scoring_profile="default"):
        captured["include_pathway"] = include_pathway
        return {"version": "1.0", "candidate_profile": {"skills": []}, "meta": {"total_skills": 0}}

    monkeypatch.setattr(main, "run_pipeline", _fake_run_pipeline)

    payload = {
        "resume": _resume_payload(),
        "jd": _jd_payload(),
        "options": {
            "include_pathway": False,
            "pathway_phase_size": 2,
            "scoring_profile": "balanced",
        },
    }
    response = client.post("/parse-resume?include_pathway=true", json=payload)

    assert response.status_code == 200
    assert captured["include_pathway"] is True


def test_parse_resume_options_invalid_phase_size_returns_422() -> None:
    payload = {
        "resume": _resume_payload(),
        "jd": _jd_payload(),
        "options": {
            "include_pathway": True,
            "pathway_phase_size": "oops",
            "scoring_profile": "balanced",
        },
    }
    response = client.post("/parse-resume", json=payload)
    assert response.status_code == 422


def test_parse_resume_query_overrides_body_phase_and_profile(monkeypatch) -> None:
    captured = {}

    def _fake_run_pipeline(data, jd_data=None, include_pathway=False, pathway_phase_size=3, scoring_profile="default"):
        captured["pathway_phase_size"] = pathway_phase_size
        captured["scoring_profile"] = scoring_profile
        return {"version": "1.0", "candidate_profile": {"skills": []}, "meta": {"total_skills": 0}}

    monkeypatch.setattr(main, "run_pipeline", _fake_run_pipeline)

    payload = {
        "resume": _resume_payload(),
        "jd": _jd_payload(),
        "options": {
            "include_pathway": True,
            "pathway_phase_size": 2,
            "scoring_profile": "balanced",
        },
    }
    response = client.post(
        "/parse-resume?pathway_phase_size=4&scoring_profile=aggressive",
        json=payload,
    )

    assert response.status_code == 200
    assert captured["pathway_phase_size"] == 4
    assert captured["scoring_profile"] == "aggressive"


def test_parse_resume_options_blank_scoring_profile_returns_422() -> None:
    payload = {
        "resume": _resume_payload(),
        "jd": _jd_payload(),
        "options": {
            "include_pathway": True,
            "pathway_phase_size": 2,
            "scoring_profile": "   ",
        },
    }
    response = client.post("/parse-resume", json=payload)
    assert response.status_code == 422


def test_parse_resume_query_invalid_phase_size_returns_422() -> None:
    payload = {"resume": _resume_payload(), "jd": _jd_payload()}
    response = client.post("/parse-resume?pathway_phase_size=0", json=payload)
    assert response.status_code == 422
