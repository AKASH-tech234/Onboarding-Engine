"""
app/modules/scoring/scoring_engine.py

Deterministic scoring utilities for pathway items.

Composite score formula (all components in [0, 1]):
    score = w1 * criticality + w2 * impact + w3 * efficiency + w4 * recency
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from collections.abc import Mapping

try:
    from scoring import scoring_weights
except ImportError:  # pragma: no cover - alternate package root
    try:
        from app.adaptive.modules.scoring import scoring_weights
    except ImportError:  # pragma: no cover - unresolved in direct script mode
        scoring_weights = None


@dataclass(frozen=True)
class WeightConfig:
    """Weights used by the composite score formula."""

    criticality: float = 0.35
    impact: float = 0.30
    efficiency: float = 0.25
    recency: float = 0.10

    def normalized(self) -> WeightConfig:
        total = self.criticality + self.impact + self.efficiency + self.recency
        if total <= 0:
            return WeightConfig()
        return WeightConfig(
            criticality=self.criticality / total,
            impact=self.impact / total,
            efficiency=self.efficiency / total,
            recency=self.recency / total,
        )


def compute_composite_score(
    *,
    criticality: float,
    impact: float,
    efficiency: float,
    recency: float,
    weights: WeightConfig | Mapping[str, float] | None = None,
) -> float:
    """
    Compute weighted composite score in [0, 1].
    """
    weight_cfg = _coerce_weights(weights).normalized()
    value = (
        weight_cfg.criticality * _clamp01(criticality)
        + weight_cfg.impact * _clamp01(impact)
        + weight_cfg.efficiency * _clamp01(efficiency)
        + weight_cfg.recency * _clamp01(recency)
    )
    return round(_clamp01(value), 4)


def score_skill(
    *,
    gap: float,
    unlock_count: int = 0,
    effort_days: int = 1,
    recency_months: int | None = None,
    max_unlock_count: int = 10,
    max_effort_days: int = 30,
    role: str | None = None,
    weights: WeightConfig | Mapping[str, float] | None = None,
) -> float:
    """
    Convenience helper that derives the four components from simple inputs.

    Inputs:
    - gap: required - candidate (clamped to [0, 1]) -> criticality
    - unlock_count: downstream unlock impact
    - effort_days: lower effort increases efficiency
    - recency_months: lower value increases recency
    """
    criticality = _clamp01(gap)
    impact = _safe_ratio(unlock_count, max_unlock_count)
    efficiency = 1.0 - _safe_ratio(effort_days, max_effort_days)
    recency = _recency_score(recency_months)

    resolved_weights = weights or _weights_for_role(role)

    return compute_composite_score(
        criticality=criticality,
        impact=impact,
        efficiency=efficiency,
        recency=recency,
        weights=resolved_weights,
    )


def score(
    item: Mapping[str, Any],
    *,
    role: str | None = None,
    weights: WeightConfig | Mapping[str, float] | None = None,
) -> float:
    """
    Generic scoring entrypoint for dict-like pathway items.
    """
    gap = _to_float(item.get("gap"), default=0.0)
    unlock_count = int(_to_float(item.get("unlock_count"), default=0.0))
    effort_days = max(1, int(_to_float(item.get("effort_days"), default=1.0)))
    recency_raw = item.get("recency_months")
    recency_months = None if recency_raw is None else int(_to_float(recency_raw, default=0.0))

    return score_skill(
        gap=gap,
        unlock_count=unlock_count,
        effort_days=effort_days,
        recency_months=recency_months,
        role=role,
        weights=weights,
    )


def _coerce_weights(weights: WeightConfig | Mapping[str, float] | None) -> WeightConfig:
    if isinstance(weights, WeightConfig):
        return weights
    if isinstance(weights, Mapping):
        return WeightConfig(
            criticality=_to_float(weights.get("criticality"), default=0.35),
            impact=_to_float(weights.get("impact"), default=0.30),
            efficiency=_to_float(weights.get("efficiency"), default=0.25),
            recency=_to_float(weights.get("recency"), default=0.10),
        )
    return WeightConfig()


def _weights_for_role(role: str | None) -> WeightConfig | None:
    if scoring_weights is None:
        return None
    if not role:
        return None
    try:
        cfg = scoring_weights.for_role(role)
    except Exception:
        return None
    return WeightConfig(
        criticality=cfg.criticality,
        impact=cfg.impact,
        efficiency=cfg.efficiency,
        recency=cfg.recency,
    )


def _recency_score(recency_months: int | None) -> float:
    if recency_months is None:
        return 0.5
    if recency_months <= 0:
        return 1.0
    if recency_months >= 24:
        return 0.0
    return round(1.0 - (recency_months / 24.0), 4)


def _safe_ratio(value: int, max_value: int) -> float:
    if max_value <= 0:
        return 0.0
    return _clamp01(value / max_value)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


__all__ = [
    "WeightConfig",
    "compute_composite_score",
    "score_skill",
    "score",
]


