"""
app/config/scoring_config.py

Role-based scoring weight configuration.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from collections.abc import Mapping


@dataclass(frozen=True)
class ScoringWeightConfig:
    """Weights used by the scoring engine."""

    criticality: float
    impact: float
    efficiency: float
    recency: float

    def as_dict(self) -> dict[str, float]:
        return {
            "criticality": self.criticality,
            "impact": self.impact,
            "efficiency": self.efficiency,
            "recency": self.recency,
        }


DEFAULT_WEIGHTS = ScoringWeightConfig(
    criticality=0.35,
    impact=0.30,
    efficiency=0.25,
    recency=0.10,
)


ROLE_WEIGHTS: dict[str, ScoringWeightConfig] = {
    "default": DEFAULT_WEIGHTS,
    "general": DEFAULT_WEIGHTS,
    "backend": ScoringWeightConfig(criticality=0.40, impact=0.30, efficiency=0.20, recency=0.10),
    "frontend": ScoringWeightConfig(criticality=0.30, impact=0.30, efficiency=0.25, recency=0.15),
    "devops": ScoringWeightConfig(criticality=0.40, impact=0.35, efficiency=0.15, recency=0.10),
    "data": ScoringWeightConfig(criticality=0.35, impact=0.25, efficiency=0.20, recency=0.20),
    "ml": ScoringWeightConfig(criticality=0.30, impact=0.25, efficiency=0.20, recency=0.25),
}


def get_scoring_weights(role: str | None = None) -> ScoringWeightConfig:
    """Return role-specific weight config with safe fallback."""
    if not role:
        return DEFAULT_WEIGHTS
    return ROLE_WEIGHTS.get(role.strip().lower(), DEFAULT_WEIGHTS)


def override_role_weights(role: str, weights: Mapping[str, Any]) -> None:
    """Allow runtime override in tests/local scripts."""
    normalized_role = role.strip().lower()
    ROLE_WEIGHTS[normalized_role] = ScoringWeightConfig(
        criticality=float(weights.get("criticality", DEFAULT_WEIGHTS.criticality)),
        impact=float(weights.get("impact", DEFAULT_WEIGHTS.impact)),
        efficiency=float(weights.get("efficiency", DEFAULT_WEIGHTS.efficiency)),
        recency=float(weights.get("recency", DEFAULT_WEIGHTS.recency)),
    )


__all__ = [
    "ScoringWeightConfig",
    "DEFAULT_WEIGHTS",
    "ROLE_WEIGHTS",
    "get_scoring_weights",
    "override_role_weights",
]


