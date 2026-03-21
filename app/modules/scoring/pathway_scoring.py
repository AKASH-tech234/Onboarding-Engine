"""Deterministic scoring for pathway items."""

from __future__ import annotations


def _clamp(value: float) -> float:
    return max(0.0, min(value, 1.0))


def score_pathway_items(ordered_skills: list[str], prereq_counts: dict[str, int]) -> dict[str, float]:
    total = max(1, len(ordered_skills))
    scores: dict[str, float] = {}

    for index, skill in enumerate(ordered_skills):
        urgency = (total - index) / total
        dependency = _clamp(float(prereq_counts.get(skill, 0)) / 5.0)
        score = _clamp(0.55 * dependency + 0.45 * urgency)
        scores[skill] = round(score, 4)

    return scores


def stable_rank(items: list[dict]) -> list[dict]:
    return sorted(
        items,
        key=lambda item: (
            -float(item.get("score", 0.0)),
            -int(item.get("prereq_count", 0)),
            str(item.get("skill", "")),
        ),
    )
