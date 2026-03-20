from typing import TypedDict


class SkillInternal(TypedDict):
    name: str
    listed: bool
    projects: int
    experience_months: int
    evidence: list[str]
