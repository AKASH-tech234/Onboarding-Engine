"""
app/modules/scoring/scoring_weights.py

Adapter layer exposing role-based weights to scoring modules.
"""

from __future__ import annotations

from dataclasses import dataclass

try:
    from config.scoring_config import get_scoring_weights
except ImportError:  # pragma: no cover - alternate package root
    from app.config.scoring_config import get_scoring_weights


@dataclass(frozen=True)
class WeightConfig:
    """Normalized weight container used by scoring_engine."""

    criticality: float
    impact: float
    efficiency: float
    recency: float

    def normalized(self) -> WeightConfig:
        total = self.criticality + self.impact + self.efficiency + self.recency
        if total <= 0:
            return WeightConfig(0.35, 0.30, 0.25, 0.10)
        return WeightConfig(
            criticality=self.criticality / total,
            impact=self.impact / total,
            efficiency=self.efficiency / total,
            recency=self.recency / total,
        )

    def as_dict(self) -> dict[str, float]:
        return {
            "criticality": self.criticality,
            "impact": self.impact,
            "efficiency": self.efficiency,
            "recency": self.recency,
        }


def for_role(role: str | None = None) -> WeightConfig:
    """Return normalized weights for a role."""
    raw = get_scoring_weights(role)
    return WeightConfig(
        criticality=raw.criticality,
        impact=raw.impact,
        efficiency=raw.efficiency,
        recency=raw.recency,
    ).normalized()


def as_dict(role: str | None = None) -> dict[str, float]:
    """Return role weights as a plain dictionary."""
    return for_role(role).as_dict()


__all__ = ["WeightConfig", "for_role", "as_dict"]
