"""Prune already-met skills from a topologically ordered learning sequence."""

from __future__ import annotations


def prune_sequence(ordered_skills: list[str], candidate_skills: set[str]) -> list[str]:
    normalized_candidate = {
        skill.strip().lower() for skill in candidate_skills if isinstance(skill, str) and skill.strip()
    }
    return [skill for skill in ordered_skills if skill not in normalized_candidate]
