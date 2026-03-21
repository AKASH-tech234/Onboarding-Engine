"""
app/modules/ingestion/gap_analyzer.py

Pure-function gap analysis for skill profiles.

Supported input shapes:

1. A single parsed JSON payload:
    {
        "candidate_profile": {"skills": [...]},
        "requirement_profile": {"skills": [...]}
    }

2. Two profile dictionaries passed separately:
    analyze_gaps(candidate_profile, requirement_profile)

Each skill item is expected to look like:
    {
        "name": "Python",
        "score": 0.8,
        "confidence": 0.9
    }

Matching is done by normalized skill name.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any
from collections.abc import Mapping

MISSING_THRESHOLD = 0.4
WEAK_THRESHOLD = 0.1
DEFAULT_SCORE = 0.0
DEFAULT_CONFIDENCE = 1.0


@dataclass(frozen=True)
class SkillSnapshot:
    """Normalized representation of one skill entry."""

    name: str
    normalized_name: str
    score: float
    confidence: float
    effective: float


def analyze_gaps(
    payload_or_candidate: Mapping[str, Any] | None,
    requirement_profile: Mapping[str, Any] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """
    Analyze skill gaps between candidate and requirement profiles.

    Args:
        payload_or_candidate:
            Either the full parsed JSON payload containing
            `candidate_profile` and `requirement_profile`, or the
            candidate profile dictionary itself.
        requirement_profile:
            Optional requirement profile when profiles are passed separately.

    Returns:
        A dictionary with `missing`, `weak`, and `strong` skill gap lists.

    Edge-case behavior:
      - Missing or invalid profiles are treated as empty.
      - Missing or invalid `skills` lists are treated as empty.
      - Invalid skill entries are skipped.
      - Missing or invalid numeric values fall back to safe defaults.
      - Values outside `[0, 1]` are clamped.
      - Duplicate skill names keep the highest effective score.
    """
    candidate_profile, requirement_profile = _resolve_profiles(
        payload_or_candidate,
        requirement_profile,
    )

    candidate_skills = _build_skill_index(candidate_profile)
    required_skills = _build_skill_index(requirement_profile)

    result: dict[str, list[dict[str, Any]]] = {
        "missing": [],
        "weak": [],
        "strong": [],
    }

    for required_skill in required_skills.values():
        candidate_skill = candidate_skills.get(required_skill.normalized_name)
        gap_item = _build_gap_item(required_skill, candidate_skill)
        result[_classify_gap(gap_item["gap"])].append(gap_item)

    for bucket in result.values():
        bucket.sort(key=lambda item: item["gap"], reverse=True)

    return result


def _resolve_profiles(
    payload_or_candidate: Mapping[str, Any] | None,
    requirement_profile: Mapping[str, Any] | None,
) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    """Resolve the supported call signatures into two profile mappings."""
    if requirement_profile is not None:
        return _as_mapping(payload_or_candidate), _as_mapping(requirement_profile)

    payload = _as_mapping(payload_or_candidate)
    return (
        _as_mapping(payload.get("candidate_profile")),
        _as_mapping(payload.get("requirement_profile")),
    )


def _build_skill_index(profile: Mapping[str, Any]) -> dict[str, SkillSnapshot]:
    """
    Convert a profile's skills into a lookup table keyed by normalized name.

    If the same skill appears multiple times, the highest effective score wins.
    """
    index: dict[str, SkillSnapshot] = {}

    for raw_skill in _extract_skill_list(profile):
        snapshot = _parse_skill(raw_skill)
        if snapshot is None:
            continue

        current = index.get(snapshot.normalized_name)
        if current is None or snapshot.effective > current.effective:
            index[snapshot.normalized_name] = snapshot

    return index


def _extract_skill_list(profile: Mapping[str, Any]) -> list[Any]:
    """Return a profile's skill list or an empty list for invalid input."""
    skills = profile.get("skills")
    return skills if isinstance(skills, list) else []


def _parse_skill(raw_skill: Any) -> SkillSnapshot | None:
    """Parse one raw skill entry into a normalized snapshot."""
    if not isinstance(raw_skill, Mapping):
        return None

    name = _extract_skill_name(raw_skill)
    if name is None:
        return None

    score = _coerce_score(raw_skill.get("score"), default=DEFAULT_SCORE)
    confidence = _coerce_score(
        raw_skill.get("confidence"),
        default=DEFAULT_CONFIDENCE,
    )
    effective = round(score * confidence, 4)

    return SkillSnapshot(
        name=name,
        normalized_name=_normalize_skill_name(name),
        score=score,
        confidence=confidence,
        effective=effective,
    )


def _extract_skill_name(raw_skill: Mapping[str, Any]) -> str | None:
    """Extract a usable skill name from a raw skill entry."""
    for key in ("name", "skill", "label", "canonical_id"):
        value = raw_skill.get(key)
        if isinstance(value, str):
            cleaned = " ".join(value.split())
            if cleaned:
                return cleaned
    return None


def _build_gap_item(
    required_skill: SkillSnapshot,
    candidate_skill: SkillSnapshot | None,
) -> dict[str, Any]:
    """Build one response item for a required skill."""
    candidate_score = candidate_skill.score if candidate_skill else 0.0
    candidate_confidence = candidate_skill.confidence if candidate_skill else 0.0
    effective_candidate = candidate_skill.effective if candidate_skill else 0.0
    gap = round(required_skill.effective - effective_candidate, 4)

    return {
        "name": required_skill.name,
        "matched": candidate_skill is not None,
        "candidate_score": candidate_score,
        "candidate_confidence": candidate_confidence,
        "effective_candidate": effective_candidate,
        "required_score": required_skill.score,
        "required_confidence": required_skill.confidence,
        "effective_required": required_skill.effective,
        "gap": gap,
    }


def _classify_gap(gap: float) -> str:
    """Classify a gap using the requested thresholds."""
    if gap > MISSING_THRESHOLD:
        return "missing"
    if gap > WEAK_THRESHOLD:
        return "weak"
    return "strong"


def _normalize_skill_name(name: str) -> str:
    """Normalize skill names for matching."""
    return " ".join(name.strip().lower().split())


def _coerce_score(value: Any, default: float) -> float:
    """Coerce a score-like value into a clamped float in [0, 1]."""
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return default
    return round(_clamp(numeric, 0.0, 1.0), 4)


def _clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp a numeric value to a fixed range."""
    return max(minimum, min(maximum, value))


def _as_mapping(value: Any) -> Mapping[str, Any]:
    """Return a mapping-like value or an empty mapping."""
    return value if isinstance(value, Mapping) else {}


if __name__ == "__main__":
    example_payload = {
        "candidate_profile": {
            "skills": [
                {"name": "Python", "score": 0.9, "confidence": 0.9},
                {"name": "Docker", "score": 0.5, "confidence": 0.8},
                {"name": "SQL", "score": 0.8, "confidence": 0.7},
            ]
        },
        "requirement_profile": {
            "skills": [
                {"name": "Python", "score": 0.8, "confidence": 1.0},
                {"name": "Docker", "score": 0.9, "confidence": 0.9},
                {"name": "Kubernetes", "score": 0.7, "confidence": 1.0},
                {"name": "SQL", "score": 0.6, "confidence": 0.8},
            ]
        },
    }

    print(json.dumps(analyze_gaps(example_payload), indent=2))


