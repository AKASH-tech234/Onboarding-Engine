from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PersonalInfo(StrictModel):
    name: str
    phone: str
    email: str
    gender: str
    date_of_birth: str
    father_name: str
    permanent_address: str
    contact_address: str


class EducationItem(StrictModel):
    degree: str
    institution: str
    year: str
    percentage: str


class TechnicalSkills(StrictModel):
    programming_languages: list[str]
    databases: list[str]
    web_technologies: list[str]
    technologies: list[str]
    testing_tools: list[str]
    test_management_tools: list[str]
    configuration_tools: list[str]
    defect_tracking_tools: list[str]
    operating_systems: list[str]


class Training(StrictModel):
    manual_testing: list[str]
    automation_testing: list[str]
    additional_training: list[str]
    institute: str


class Project(StrictModel):
    name: str
    duration: str
    role: str
    technologies: list[str]
    description: str


class SoftSkills(StrictModel):
    personal_skills: list[str]


class Declaration(StrictModel):
    statement: str
    place: str
    date: str


class ResumeInput(StrictModel):
    personal_info: PersonalInfo
    career_objective: str
    education: list[EducationItem]
    technical_skills: TechnicalSkills
    training: Training
    project: Project
    skills: SoftSkills
    extra_curricular: list[str]
    declaration: Declaration


class CompanyDetails(StrictModel):
    company_name: str
    industry: str
    website: str


class RequiredSkills(StrictModel):
    manual_testing: list[str]
    automation_testing: list[str]
    tools: list[str]
    technical_skills: list[str]


class JobDescriptionInput(StrictModel):
    job_title: str
    job_location: str
    employment_type: str
    experience_required: str
    salary_range: str
    job_summary: str
    key_responsibilities: list[str]
    required_skills: RequiredSkills
    preferred_qualifications: list[str]
    soft_skills: list[str]
    selection_process: list[str]
    company_details: CompanyDetails
    benefits: list[str]


class ParseOptions(StrictModel):
    include_pathway: bool = False
    pathway_phase_size: int = Field(default=3, ge=1, le=50)
    scoring_profile: str = Field(default="default", min_length=1, max_length=64)

    @field_validator("scoring_profile")
    @classmethod
    def _validate_scoring_profile(cls, value: str) -> str:
        normalized = value.strip()
        if normalized == "":
            raise ValueError("scoring_profile must be a non-empty string")
        return normalized


class ParseRequest(StrictModel):
    resume: ResumeInput
    jd: JobDescriptionInput
    options: ParseOptions | None = None


def resume_to_pipeline_input(resume: ResumeInput) -> dict:
    flattened_skills: list[str] = []
    skill_sources: dict[str, list[str]] = {}
    training_skills: list[str] = []
    project_technology_skills: list[str] = []

    def _append_skill(skill: str, source: str) -> None:
        normalized = skill.strip().lower()
        if normalized == "":
            return
        if normalized not in flattened_skills:
            flattened_skills.append(normalized)
        if normalized not in skill_sources:
            skill_sources[normalized] = []
        if source not in skill_sources[normalized]:
            skill_sources[normalized].append(source)

    skill_groups = [
        resume.technical_skills.programming_languages,
        resume.technical_skills.databases,
        resume.technical_skills.web_technologies,
        resume.technical_skills.technologies,
        resume.technical_skills.testing_tools,
        resume.technical_skills.test_management_tools,
        resume.technical_skills.configuration_tools,
        resume.technical_skills.defect_tracking_tools,
        resume.technical_skills.operating_systems,
    ]

    group_sources = [
        "technical_skills.programming_languages",
        "technical_skills.databases",
        "technical_skills.web_technologies",
        "technical_skills.technologies",
        "technical_skills.testing_tools",
        "technical_skills.test_management_tools",
        "technical_skills.configuration_tools",
        "technical_skills.defect_tracking_tools",
        "technical_skills.operating_systems",
    ]

    for source, group in zip(group_sources, skill_groups):
        for item in group:
            _append_skill(item, source)

    for item in resume.training.manual_testing:
        _append_skill(item, "training.manual_testing")
        if item.strip().lower() not in training_skills:
            training_skills.append(item.strip().lower())

    for item in resume.training.automation_testing:
        _append_skill(item, "training.automation_testing")
        if item.strip().lower() not in training_skills:
            training_skills.append(item.strip().lower())

    for item in resume.project.technologies:
        _append_skill(item, "project.technologies")
        normalized = item.strip().lower()
        if normalized and normalized not in project_technology_skills:
            project_technology_skills.append(normalized)

    projects: list[dict] = [
        {
            "name": resume.project.name,
            "description": resume.project.description,
        }
    ]

    return {
        "skills": flattened_skills,
        "projects": projects,
        "experience": [],
        "skill_sources": skill_sources,
        "training_skills": training_skills,
        "project_technology_skills": project_technology_skills,
    }


def payload_to_pipeline_input(payload: ParseRequest | ResumeInput) -> dict:
    if isinstance(payload, ParseRequest):
        return resume_to_pipeline_input(payload.resume)
    return resume_to_pipeline_input(payload)


def jd_to_pipeline_input(jd: JobDescriptionInput) -> dict:
    required_groups = [
        jd.required_skills.manual_testing,
        jd.required_skills.automation_testing,
        jd.required_skills.tools,
        jd.required_skills.technical_skills,
        jd.soft_skills,
    ]

    flattened_skills: list[str] = []
    skill_sources: dict[str, list[str]] = {}
    training_skills: list[str] = []

    def _append_skill(skill: str, source: str) -> None:
        normalized = skill.strip().lower()
        if normalized == "":
            return
        if normalized not in flattened_skills:
            flattened_skills.append(normalized)
        if normalized not in skill_sources:
            skill_sources[normalized] = []
        if source not in skill_sources[normalized]:
            skill_sources[normalized].append(source)

    group_sources = [
        "training.manual_testing",
        "training.automation_testing",
        "technical_skills.tools",
        "technical_skills.technical_skills",
        "soft_skills",
    ]

    for source, group in zip(group_sources, required_groups):
        for item in group:
            _append_skill(item, source)
            if source.startswith("training.") and item.strip().lower() not in training_skills:
                training_skills.append(item.strip().lower())

    projects: list[dict] = []
    if jd.job_summary.strip():
        projects.append({"name": "job_summary", "description": jd.job_summary})

    for idx, responsibility in enumerate(jd.key_responsibilities):
        projects.append(
            {
                "name": f"responsibility_{idx + 1}",
                "description": responsibility,
            }
        )

    return {
        "skills": flattened_skills,
        "projects": projects,
        "experience": [],
        "skill_sources": skill_sources,
        "training_skills": training_skills,
        "project_technology_skills": [],
    }
