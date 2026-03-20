from pydantic import BaseModel


class ResumeRequest(BaseModel):
    skills: list[str]
    projects: list[dict]
    experience: list[dict]
