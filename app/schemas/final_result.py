"""Final result schemas for complete pipeline output."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from schemas.pathway import PathwayResponse


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SkillOut(StrictModel):
    name: str
    score: float
    level: str
    confidence: float
    reasoning: str
    evidence: list[str]


class ProfileOut(StrictModel):
    skills: list[SkillOut]


class ParsedMeta(StrictModel):
    total_skills: int | None = None
    required_total_skills: int | None = None


class ParsedResult(StrictModel):
    version: str
    candidate_profile: ProfileOut
    requirement_profile: ProfileOut | None = None
    pathway: PathwayResponse | None = None
    meta: ParsedMeta


class FinalResultEnvelope(StrictModel):
    parsed: ParsedResult
