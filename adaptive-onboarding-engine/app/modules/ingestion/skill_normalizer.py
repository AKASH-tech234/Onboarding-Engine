"""
app/modules/ingestion/skill_normalizer.py

Deterministic skill normalization utilities.

Current implementation is graph-backed:
- uses graph node IDs and labels as canonical vocabulary
- normalizes by exact case-insensitive match
- applies a small alias map for common variants
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any
from collections.abc import Iterable, Mapping, Sequence

try:
    import graph.graph_engine as graph_engine
except ImportError:  # pragma: no cover - alternate package root
    from app.modules.graph import graph_engine


DEFAULT_ALIASES: dict[str, str] = {
    "reactjs": "react",
    "react.js": "react",
    "nodejs": "node.js",
    "node": "node.js",
    "js": "javascript",
    "ts": "typescript",
    "k8s": "kubernetes",
    "postgres": "postgresql",
    "py": "python",
}


@dataclass(frozen=True)
class NormalizedSkill:
    raw: str
    normalized_input: str
    canonical_id: str
    canonical_label: str
    matched: bool
    confidence: float
    source: str


def normalize_skills(
    payload_or_skills: Sequence[str] | Mapping[str, Any] | None,
    *,
    alias_map: Mapping[str, str] | None = None,
) -> list[dict[str, Any]]:
    """
    Normalize raw skill names into canonical IDs.

    Supported input shapes:
      1) ["Python", "ReactJS", ...]
      2) {"skills": ["Python", "ReactJS", ...]}
      3) {"skills": [{"name": "Python"}, {"label": "ReactJS"}]}
    """
    raw_names = _coerce_skill_names(payload_or_skills)
    if not raw_names:
        return []

    aliases = dict(DEFAULT_ALIASES)
    if alias_map:
        for key, value in alias_map.items():
            aliases[_normalize_text(key)] = _normalize_text(value)

    canonical_lookup, labels = _build_canonical_lookup()
    output: list[dict[str, Any]] = []

    for raw in raw_names:
        normalized_input = _normalize_text(raw)
        alias_target = aliases.get(normalized_input, normalized_input)
        canonical_id = canonical_lookup.get(alias_target)

        if canonical_id:
            label = labels.get(canonical_id, canonical_id)
            item = NormalizedSkill(
                raw=raw,
                normalized_input=normalized_input,
                canonical_id=canonical_id,
                canonical_label=label,
                matched=True,
                confidence=1.0 if alias_target == normalized_input else 0.9,
                source="graph",
            )
        else:
            fallback_id = _fallback_canonical_id(alias_target)
            item = NormalizedSkill(
                raw=raw,
                normalized_input=normalized_input,
                canonical_id=fallback_id,
                canonical_label=raw.strip() or fallback_id,
                matched=False,
                confidence=0.4,
                source="fallback",
            )

        output.append(asdict(item))

    return output


def normalize_skill_name(name: str) -> dict[str, Any]:
    """
    Convenience helper for one skill name.
    """
    results = normalize_skills([name])
    return results[0] if results else {}


def _build_canonical_lookup() -> tuple[dict[str, str], dict[str, str]]:
    lookup: dict[str, str] = {}
    labels: dict[str, str] = {}

    try:
        if not graph_engine.is_loaded():
            graph_engine.load_graph()
        node_ids = graph_engine.get_node_ids()
    except Exception:
        return lookup, labels

    for node_id in node_ids:
        node = graph_engine.get_node(node_id)
        if node is None:
            continue

        labels[node_id] = node.label
        lookup[_normalize_text(node_id)] = node_id
        lookup[_normalize_text(node.label)] = node_id

    return lookup, labels


def _coerce_skill_names(payload_or_skills: Sequence[str] | Mapping[str, Any] | None) -> list[str]:
    if payload_or_skills is None:
        return []

    if isinstance(payload_or_skills, Mapping):
        skills = payload_or_skills.get("skills")
    else:
        skills = payload_or_skills

    if not isinstance(skills, Iterable) or isinstance(skills, (str, bytes)):
        return []

    names: list[str] = []
    for skill in skills:
        if isinstance(skill, str):
            text = " ".join(skill.split())
            if text:
                names.append(text)
            continue

        if isinstance(skill, Mapping):
            for key in ("name", "label", "skill", "canonical_id"):
                value = skill.get(key)
                if isinstance(value, str):
                    text = " ".join(value.split())
                    if text:
                        names.append(text)
                    break

    return names


def _fallback_canonical_id(value: str) -> str:
    compact = value.replace(" ", "_")
    return compact or "unknown_skill"


def _normalize_text(value: str) -> str:
    return " ".join(value.strip().lower().split())


if __name__ == "__main__":
    sample = {"skills": ["Python", "ReactJS", "K8s", "Unknown Tool"]}
    for item in normalize_skills(sample):
        print(item)
