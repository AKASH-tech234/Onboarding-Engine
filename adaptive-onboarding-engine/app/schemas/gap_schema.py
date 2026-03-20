"""
app/schemas/gap_schema.py

All dataclasses / enums that gap_analyzer.py produces and downstream
modules consume (pruning_engine, pathway_builder, API response builder).

Design rules:
  - Pure data containers. No logic, no validation side-effects.
  - Frozen where the object must not be mutated after creation.
  - Mutable only where downstream code legitimately needs to patch fields
    (e.g. pathway_builder annotates GapItem with a reasoning trace later).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class GapCategory(str, Enum):
    """
    Three-tier classification based on effective gap magnitude.

      MISSING → gap > 0.40   Candidate lacks the skill or is far below target.
      WEAK    → 0.10 < gap ≤ 0.40   Partial knowledge; needs targeted upskilling.
      STRONG  → gap ≤ 0.10   Candidate meets or is near the requirement.
    """
    MISSING = "missing"
    WEAK    = "weak"
    STRONG  = "strong"


class GapSeverity(str, Enum):
    """
    Operational urgency label derived from both gap magnitude and importance.
    Used by scoring_engine to weight pathway item priority.

      CRITICAL  → large gap on a high-importance skill
      HIGH      → large gap on medium-importance OR medium gap on high-importance
      MEDIUM    → moderate gap or moderate importance
      LOW       → small gap or low-importance optional skill
    """
    CRITICAL = "critical"
    HIGH     = "high"
    MEDIUM   = "medium"
    LOW      = "low"


class SignalInfluence(str, Enum):
    """
    How signals (years_experience, recency, project_complexity, …) adjusted
    the raw score. Surfaced in the reasoning trace for explainability.
    """
    BOOSTED   = "boosted"    # signals pushed effective score UP
    PENALISED = "penalised"  # signals pulled effective score DOWN
    NEUTRAL   = "neutral"    # signals had no net effect


# ---------------------------------------------------------------------------
# Per-skill gap record
# ---------------------------------------------------------------------------

@dataclass
class SignalSummary:
    """
    Compact record of how signals contributed to the final effective score.
    Stored on GapItem for the AI reasoning trace to reference.
    """
    raw_score:          float   # candidate skill score before signal adjustment
    confidence:         float   # confidence in the score (0–1)
    signal_adjustment:  float   # total additive delta applied by signals
    effective_score:    float   # raw_score × confidence + signal_adjustment
    influence:          SignalInfluence
    signal_detail:      dict[str, float] = field(default_factory=dict)
    # e.g. {"years_experience": +0.05, "recency_penalty": -0.03}


@dataclass
class GapItem:
    """
    The gap analysis result for a single (candidate-skill, job-requirement) pair.

    Fields
    ------
    canonical_id        Normalised skill identifier (e.g. "kubernetes").
    label               Human-readable skill name.
    category            MISSING / WEAK / STRONG.
    severity            CRITICAL / HIGH / MEDIUM / LOW.
    effective_candidate Candidate's adjusted proficiency (0–1).
    effective_required  Job's effective requirement (0–1) after importance weighting.
    raw_gap             effective_required − effective_candidate (clamped ≥ 0).
    importance          Original importance weight from the job profile (0–1).
    required_score      Original required_score from the job profile (0–1).
    signal_summary      How signals shaped the candidate's effective score.
    is_preferred        True if this skill is "preferred" (not required) in the JD.
    matched             True if a candidate skill was found for this requirement.
                        False means the skill was entirely absent from the candidate profile.
    notes               Free-text list — populated by higher layers (reasoning trace etc.).
    """
    canonical_id:        str
    label:               str
    category:            GapCategory
    severity:            GapSeverity
    effective_candidate: float
    effective_required:  float
    raw_gap:             float
    importance:          float
    required_score:      float
    signal_summary:      SignalSummary
    is_preferred:        bool = False
    matched:             bool = True
    notes:               list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Aggregate analysis object
# ---------------------------------------------------------------------------

@dataclass
class GapAnalysis:
    """
    Complete gap analysis for one (candidate, job) pair.

    Fields
    ------
    candidate_id        Identifier from the candidate profile (may be None for anonymous).
    job_id              Identifier from the job profile (may be None).
    items               All GapItem records — one per required/preferred skill.
    missing             Subset where category == MISSING.
    weak                Subset where category == WEAK.
    strong              Subset where category == STRONG.
    unmatched_ids       Skill IDs present on candidate profile but not required by job
                        (not gaps — used for "extra skills" display).
    overall_gap_score   Weighted aggregate gap across all required skills (0–1).
                        0 = perfect match, 1 = all skills entirely missing.
    pathway_type        "targeted" if overall_gap_score ≤ 0.60,
                        "career_transition" if overall_gap_score > 0.60.
    critical_count      Number of CRITICAL-severity items.
    high_count          Number of HIGH-severity items.
    metadata            Arbitrary key/value store for pipeline metadata
                        (graph_version, timestamp, model_version, etc.).
    """
    candidate_id:       str | None
    job_id:             str | None
    items:              list[GapItem]
    missing:            list[GapItem]
    weak:               list[GapItem]
    strong:             list[GapItem]
    unmatched_ids:      list[str]
    overall_gap_score:  float
    pathway_type:       str
    critical_count:     int
    high_count:         int
    metadata:           dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Convenience accessors
    # ------------------------------------------------------------------

    @property
    def requires_learning(self) -> list[GapItem]:
        """Items that need active learning (missing + weak)."""
        return self.missing + self.weak

    @property
    def gap_skill_ids(self) -> list[str]:
        """Canonical IDs of all skills requiring learning. Used by graph engine."""
        return [item.canonical_id for item in self.requires_learning]

    @property
    def met_skill_ids(self) -> list[str]:
        """Canonical IDs of strong (met) skills. Passed to pruning_engine."""
        return [item.canonical_id for item in self.strong]

    def get_item(self, canonical_id: str) -> GapItem | None:
        """O(n) lookup by canonical_id. Sufficient for typical gap sizes (< 50 items)."""
        for item in self.items:
            if item.canonical_id == canonical_id:
                return item
        return None