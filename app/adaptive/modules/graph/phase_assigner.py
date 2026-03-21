"""
graph/phase_assigner.py

Group the pruned + sorted skill list into discrete learning phases.

Three-stage process:

  Stage 1 â€” Critical level bucketing (HARD constraint)
    Skills are grouped by their critical level (longest prerequisite chain
    depth). A skill at critical level N can NEVER share a phase with a
    dependency at critical level â‰¥ N. This is the fundamental ordering
    correctness guarantee.

  Stage 2 â€” Domain clustering (soft heuristic)
    Within each critical level group, same-domain skills are clustered
    together before switching domains. Keeps related content cohesive:
    "all Docker content before all Kubernetes content" rather than
    interleaving unrelated topics.

  Stage 3 â€” Phase packing (capacity constraints)
    Items are greedily packed into phases. A new phase opens when:
      a) Adding the next item would exceed max_days_per_phase (effort cap), OR
      b) The current phase already has max_items_per_phase items (count cap), OR
      c) The next item is at a HIGHER critical level (hard dependency boundary).

validate_phase_order() performs a post-hoc correctness check:
  For every edge (prereq â†’ dependent) in the subgraph, verify that
  prereq.phase < dependent.phase. Used in CI and after any pathway mutation.
"""

from __future__ import annotations

import logging
from collections import Counter

try:
    from app.adaptive.modules.graph.models import LearningMode, Phase, PhaseValidationResult, PrunedItem, SkillEdge
    from app.adaptive.modules.graph.topological_sort import compute_critical_levels
except ImportError:  # pragma: no cover - alternate package root
    from app.adaptive.modules.graph.models import LearningMode, Phase, PhaseValidationResult, PrunedItem, SkillEdge
    from app.adaptive.modules.graph.topological_sort import compute_critical_levels

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_MAX_DAYS_PER_PHASE  = 7
DEFAULT_MAX_ITEMS_PER_PHASE = 5


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def assign_phases(
    items:         list[PrunedItem],
    edges:         list[SkillEdge],
    *,
    max_days_per_phase:  int          = DEFAULT_MAX_DAYS_PER_PHASE,
    max_items_per_phase: int          = DEFAULT_MAX_ITEMS_PER_PHASE,
    group_by_domain:     bool         = True,
    learning_mode:       LearningMode = LearningMode.DEEP_LEARNING,
) -> list[Phase]:
    """
    Assign pruned skill items into ordered learning phases.

    Args:
        items:               PrunedItems in topological order (output of prune_and_compress).
        edges:               Subgraph edges (used to compute critical levels).
        max_days_per_phase:  Soft effort cap per phase.
        max_items_per_phase: Soft item count cap per phase.
        group_by_domain:     If True, cluster same-domain skills within a critical level.
        learning_mode:       FAST_TRACK uses tighter phase caps.

    Returns:
        List of Phase objects, 1-indexed.
    """
    if not items:
        return []

    # Adjust caps for fast_track
    if learning_mode == LearningMode.FAST_TRACK:
        max_days_per_phase  = math.ceil(max_days_per_phase  * 0.7)
        max_items_per_phase = math.ceil(max_items_per_phase * 1.3)

    # â”€â”€ Stage 1: compute critical levels and annotate items
    topo_order   = [i.skill_id for i in items]
    crit_levels  = compute_critical_levels(topo_order, edges)

    annotated = [
        (item, crit_levels.get(item.skill_id, 0))
        for item in items
    ]

    # â”€â”€ Stage 2: group by critical level
    level_groups = _group_by_critical_level(annotated)

    # â”€â”€ Stage 2b: domain clustering within each group
    ordered_items = _apply_domain_clustering(level_groups) if group_by_domain else [
        item for group in level_groups for item, _ in group
    ]

    # â”€â”€ Stage 3: pack into phases
    phases = _pack_into_phases(
        items=ordered_items,
        crit_levels=crit_levels,
        max_days=max_days_per_phase,
        max_items=max_items_per_phase,
    )

    logger.debug(
        "phase_assigner: input_items=%d phases=%d max_days=%d",
        len(items), len(phases), max_days_per_phase,
    )

    return phases


def validate_phase_order(
    phases: list[Phase],
    edges:  list[SkillEdge],
) -> PhaseValidationResult:
    """
    Verify that no phase contains a skill whose prerequisite is in the
    same or a later phase.

    Args:
        phases: Output of assign_phases().
        edges:  Subgraph edges.

    Returns:
        PhaseValidationResult with .valid and .violations list.
        Each violation is a dict with keys: skill, prereq, phase_a, phase_b.
    """
    # Build skill â†’ phase_number lookup
    phase_of: dict[str, int] = {}
    for phase in phases:
        for skill_id in phase.skill_ids:
            phase_of[skill_id] = phase.phase_number

    violations = []
    for edge in edges:
        prereq_phase = phase_of.get(edge.from_id)
        dep_phase    = phase_of.get(edge.to_id)

        if prereq_phase is None or dep_phase is None:
            continue

        if prereq_phase >= dep_phase:
            violations.append({
                "skill":   edge.to_id,
                "prereq":  edge.from_id,
                "phase_a": prereq_phase,
                "phase_b": dep_phase,
            })

    return PhaseValidationResult(valid=len(violations) == 0, violations=violations)


# ---------------------------------------------------------------------------
# Stage 1: critical level grouping
# ---------------------------------------------------------------------------

def _group_by_critical_level(
    annotated: list[tuple[PrunedItem, int]],
) -> list[list[tuple[PrunedItem, int]]]:
    """
    Group annotated items by critical level.
    Returns list of groups sorted by level ascending.
    Each group is a list of (PrunedItem, critical_level) tuples.
    """
    groups: dict[int, list[tuple[PrunedItem, int]]] = {}
    for item, level in annotated:
        groups.setdefault(level, []).append((item, level))

    return [groups[lvl] for lvl in sorted(groups.keys())]


# ---------------------------------------------------------------------------
# Stage 2: domain clustering
# ---------------------------------------------------------------------------

def _apply_domain_clustering(
    level_groups: list[list[tuple[PrunedItem, int]]],
) -> list[PrunedItem]:
    """
    Within each critical level group, cluster same-domain skills together.
    Domain ordering follows first-appearance in the topological sequence
    (preserves topo order's implicit priority signal).

    Returns:
        Flat list of PrunedItems with domain-clustered ordering within each level.
    """
    result: list[PrunedItem] = []

    for group in level_groups:
        # Determine domain order by first appearance
        seen_domains: list[str]             = []
        by_domain:    dict[str, list[PrunedItem]] = {}

        for item, _ in group:
            if item.domain not in by_domain:
                seen_domains.append(item.domain)
                by_domain[item.domain] = []
            by_domain[item.domain].append(item)

        for domain in seen_domains:
            result.extend(by_domain[domain])

    return result


# ---------------------------------------------------------------------------
# Stage 3: phase packing
# ---------------------------------------------------------------------------

def _pack_into_phases(
    items:       list[PrunedItem],
    crit_levels: dict[str, int],
    max_days:    int,
    max_items:   int,
) -> list[Phase]:
    """
    Greedily pack items into phases.

    A new phase opens when:
      - Adding next item would exceed max_days AND current phase is non-empty
      - Current phase already has max_items items
      - Next item is at a strictly HIGHER critical level than any item in the
        current phase (hard dependency boundary â€” always triggers a new phase)

    Single-skill phases are allowed: a skill that exceeds max_days by itself
    still forms its own phase (we never drop a skill to fit a budget here â€”
    that is pruning_engine's job).
    """
    phases:          list[Phase] = []
    current_ids:     list[str]   = []
    current_effort:  int         = 0
    current_domains: list[str]   = []
    current_max_lvl: int         = -1

    def _flush(phase_number: int) -> Phase:
        focus = _dominant_domain(current_domains)
        return Phase(
            phase_number=phase_number,
            focus_domain=focus,
            total_effort_days=current_effort,
            skill_ids=list(current_ids),
            min_critical_level=min(crit_levels.get(s, 0) for s in current_ids),
            max_critical_level=max(crit_levels.get(s, 0) for s in current_ids),
        )

    for item in items:
        item_level = crit_levels.get(item.skill_id, 0)

        would_exceed_days  = (current_effort + item.adjusted_effort_days > max_days
                              and len(current_ids) > 0)
        would_exceed_items = len(current_ids) >= max_items
        crosses_level      = (item_level > current_max_lvl and len(current_ids) > 0)

        if would_exceed_days or would_exceed_items or crosses_level:
            phases.append(_flush(len(phases) + 1))
            current_ids     = []
            current_effort  = 0
            current_domains = []
            current_max_lvl = -1

        current_ids.append(item.skill_id)
        current_effort += item.adjusted_effort_days
        current_domains.append(item.domain)
        current_max_lvl = max(current_max_lvl, item_level)

    if current_ids:
        phases.append(_flush(len(phases) + 1))

    return phases


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _dominant_domain(domains: list[str]) -> str:
    """Return the most frequent domain in the list. Ties broken alphabetically."""
    if not domains:
        return "general"
    counter = Counter(domains)
    return min(
        (d for d in counter if counter[d] == counter.most_common(1)[0][1]),
        key=lambda d: (-counter[d], d),
    )


# ---------------------------------------------------------------------------
# math import needed for fast_track ceiling
# ---------------------------------------------------------------------------
import math


