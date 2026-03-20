"""
graph/models.py

Dataclasses for every type flowing through the graph engine pipeline.
Using dataclasses (not Pydantic) to keep the graph layer free of
web-framework dependencies — Pydantic validation lives in the API layer.

Immutable where possible: frozen=True prevents accidental mutation
of nodes/edges that are shared across multiple subgraph extractions.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Importance(str, Enum):
    MANDATORY    = "mandatory"
    RECOMMENDED  = "recommended"


class ProficiencyStatus(str, Enum):
    MISSING = "missing"
    WEAK    = "weak"
    MET     = "met"


class LearningMode(str, Enum):
    FAST_TRACK    = "fast_track"
    DEEP_LEARNING = "deep_learning"


# ---------------------------------------------------------------------------
# Graph primitives
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SkillNode:
    """
    A canonical skill in the dependency graph.
    `source` distinguishes curated nodes from LLM-generated expansions.
    """
    id:               str
    label:            str
    domain:           str
    base_effort_days: int
    difficulty:       int           # 1–5
    tags:             tuple[str, ...] = field(default_factory=tuple)
    source:           str = "curated"   # "curated" | "llm_generated"

    def __post_init__(self):
        if not self.id:
            raise ValueError("SkillNode.id cannot be empty")
        if not (1 <= self.difficulty <= 5):
            raise ValueError(f"difficulty must be 1–5, got {self.difficulty}")
        if self.base_effort_days < 0:
            raise ValueError("base_effort_days cannot be negative")


@dataclass(frozen=True)
class SkillEdge:
    """
    A directed dependency edge: `from_id` → `to_id` means
    `to_id` requires `from_id` as a prerequisite.
    """
    from_id:    str
    to_id:      str
    importance: Importance
    weight:     float   # 0.0–1.0; lower weight = breakable under time constraints

    def __post_init__(self):
        if self.from_id == self.to_id:
            raise ValueError(f"Self-loop on node '{self.from_id}'")
        if not (0.0 <= self.weight <= 1.0):
            raise ValueError(f"weight must be 0.0–1.0, got {self.weight}")


# ---------------------------------------------------------------------------
# Gap analysis inputs
# ---------------------------------------------------------------------------

@dataclass
class CandidateSkillLevel:
    """
    The candidate's current proficiency for one skill versus what the role requires.
    Produced by gapAnalyzer and consumed by pruningEngine.
    """
    canonical_id:    str
    candidate_level: float   # 0.0–1.0
    required_level:  float   # 0.0–1.0

    @property
    def delta(self) -> float:
        return max(0.0, self.required_level - self.candidate_level)


# ---------------------------------------------------------------------------
# Pruning engine output
# ---------------------------------------------------------------------------

@dataclass
class PrunedItem:
    """
    A single skill that requires actual learning effort.
    Met skills never appear here — they are in PruneResult.pruned_ids.
    """
    skill_id:             str
    skill_label:          str
    domain:               str
    proficiency_status:   ProficiencyStatus
    current_proficiency:  float
    required_proficiency: float
    delta:                float
    base_effort_days:     int
    adjusted_effort_days: int    # after compression for weak skills
    difficulty:           int
    topo_order:           int    # position in sorted list (0-based)


@dataclass
class PruneResult:
    items:             list[PrunedItem]
    pruned_ids:        list[str]    # skills removed because candidate already knows them
    trimmed_ids:       list[str]    # skills cut due to time budget
    total_effort_days: int


# ---------------------------------------------------------------------------
# Subgraph extraction output
# ---------------------------------------------------------------------------

@dataclass
class SubgraphResult:
    nodes:          dict[str, SkillNode]   # id → node
    edges:          list[SkillEdge]
    unresolved_ids: list[str]              # skill IDs with no graph node found


# ---------------------------------------------------------------------------
# Phase assignment output
# ---------------------------------------------------------------------------

@dataclass
class Phase:
    phase_number:       int
    focus_domain:       str
    total_effort_days:  int
    skill_ids:          list[str]
    min_critical_level: int
    max_critical_level: int


@dataclass
class PhaseValidationResult:
    valid:      bool
    violations: list[dict]   # each: {skill, prereq, phase_a, phase_b}