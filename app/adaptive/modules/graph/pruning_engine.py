"""
graph/pruning_engine.py

Two-pass transformation of the topologically sorted skill list:

  Pass 1 â€” CLASSIFY + COMPRESS
    For each skill in topo order:
      - Met  (delta â‰¤ GAP_THRESHOLD):   remove entirely (candidate already knows it)
      - Weak (GAP_THRESHOLD < delta â‰¤ WEAK_THRESHOLD):
              keep, but reduce effort = base_effort Ã— delta
      - Missing (delta > WEAK_THRESHOLD):
              keep, full base effort (or 70% in fast_track mode)

  Pass 2 â€” TIME BUDGET TRIMMING
    If timeBudgetDays is set and total effort exceeds it:
      Sort remaining items by composite_score ASC (worst candidates first).
      Greedily remove items until the budget is met.
      NEVER remove a skill if a higher-scoring skill that depends on it
      is still in the retained set (orphan prevention).

Returns PruneResult with the final ordered list + audit lists for
pruned (met) and trimmed (budget) skill IDs.

Thresholds:
  GAP_THRESHOLD  = 0.10  (delta â‰¤ 0.10 â†’ met)
  WEAK_THRESHOLD = 0.30  (delta 0.10â€“0.30 â†’ weak; delta > 0.30 â†’ missing)
  MIN_EFFORT     = 1 day (floor for any compressed effort)
"""

from __future__ import annotations

import logging
import math
from dataclasses import replace

try:
    from app.adaptive.modules.graph import graph_engine as engine
    from app.adaptive.modules.graph.models import (
        CandidateSkillLevel,
        LearningMode,
        ProficiencyStatus,
        PruneResult,
        PrunedItem,
    )
except ImportError:  # pragma: no cover - alternate package root
    from app.adaptive.modules.graph import graph_engine as engine
    from app.adaptive.modules.graph.models import (
        CandidateSkillLevel,
        LearningMode,
        ProficiencyStatus,
        PruneResult,
        PrunedItem,
    )

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

GAP_THRESHOLD  = 0.10
WEAK_THRESHOLD = 0.30
MIN_EFFORT     = 1          # minimum days after compression


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def prune_and_compress(
    topo_order:       list[str],
    candidate_levels: list[CandidateSkillLevel],
    *,
    time_budget_days: int | None = None,
    scores:           dict[str, float] | None = None,
    learning_mode:    LearningMode = LearningMode.DEEP_LEARNING,
) -> PruneResult:
    """
    Prune and compress a topologically sorted skill list.

    Args:
        topo_order:       Skill IDs in topological order (output of topological_sort).
        candidate_levels: Proficiency records for all gap + met skills.
        time_budget_days: Optional cap on total adjusted effort.
                          If None, no trimming is applied.
        scores:           Composite score per skill (used for budget trimming priority).
                          Higher score = protected from trimming.
        learning_mode:    FAST_TRACK reduces effort estimates; DEEP_LEARNING uses full effort.

    Returns:
        PruneResult with .items (PrunedItem list in topo order), .pruned_ids,
        .trimmed_ids, .total_effort_days.
    """
    if not topo_order:
        return PruneResult(items=[], pruned_ids=[], trimmed_ids=[], total_effort_days=0)

    scores = scores or {}

    # Build O(1) lookup: canonical_id â†’ CandidateSkillLevel
    level_map: dict[str, CandidateSkillLevel] = {c.canonical_id: c for c in candidate_levels}

    items:      list[PrunedItem] = []
    pruned_ids: list[str]        = []

    # â”€â”€ Pass 1: classify and compute adjusted effort
    for index, skill_id in enumerate(topo_order):
        node = engine.resolve_node(skill_id)

        if node is None:
            # Staged node was removed between extraction and pruning
            logger.warning(
                "pruning_engine: '%s' not found in graph at prune time â€” skipping",
                skill_id,
            )
            pruned_ids.append(skill_id)
            continue

        candidate_level, required_level = _get_levels(skill_id, level_map, node.difficulty)

        # Edge case: required_level = 0 means the JD doesn't actually require
        # this skill â€” it is only in the subgraph as a structural ancestor.
        if required_level == 0.0:
            pruned_ids.append(skill_id)
            continue

        delta = max(0.0, required_level - candidate_level)

        # â”€â”€ Classify
        if delta <= GAP_THRESHOLD:
            pruned_ids.append(skill_id)
            continue

        status = (
            ProficiencyStatus.WEAK
            if delta <= WEAK_THRESHOLD
            else ProficiencyStatus.MISSING
        )

        adjusted_effort = compute_adjusted_effort(
            base_effort_days=node.base_effort_days,
            delta=delta,
            status=status,
            learning_mode=learning_mode,
        )

        items.append(
            PrunedItem(
                skill_id=skill_id,
                skill_label=node.label,
                domain=node.domain,
                proficiency_status=status,
                current_proficiency=round(candidate_level, 4),
                required_proficiency=round(required_level, 4),
                delta=round(delta, 4),
                base_effort_days=node.base_effort_days,
                adjusted_effort_days=adjusted_effort,
                difficulty=node.difficulty,
                topo_order=index,
            )
        )

    # â”€â”€ Pass 2: apply time budget
    if time_budget_days is not None:
        final_items, trimmed_ids = _apply_time_budget(items, time_budget_days, scores)
    else:
        final_items, trimmed_ids = items, []

    total = sum(i.adjusted_effort_days for i in final_items)

    logger.debug(
        "pruning_engine: input=%d pruned=%d trimmed=%d remaining=%d total_effort=%d",
        len(topo_order), len(pruned_ids), len(trimmed_ids), len(final_items), total,
    )

    return PruneResult(
        items=final_items,
        pruned_ids=pruned_ids,
        trimmed_ids=trimmed_ids,
        total_effort_days=total,
    )


# ---------------------------------------------------------------------------
# Effort computation
# ---------------------------------------------------------------------------

def compute_adjusted_effort(
    base_effort_days: int,
    delta:            float,
    status:           ProficiencyStatus,
    learning_mode:    LearningMode = LearningMode.DEEP_LEARNING,
) -> int:
    """
    Compute adjusted learning effort for a single skill.

    MISSING skills:
      deep_learning â†’ full base effort
      fast_track    â†’ 70% of base (crash-course assumption)

    WEAK skills:
      deep_learning â†’ base Ã— delta           (linear gap fraction)
      fast_track    â†’ base Ã— delta Ã— 0.60    (review mode â€” steeper discount)

    All results are clamped to MIN_EFFORT (1 day).

    Args:
        base_effort_days: Base effort from the graph node.
        delta:            required_level âˆ’ candidate_level (0.0â€“1.0).
        status:           MISSING or WEAK.
        learning_mode:    FAST_TRACK or DEEP_LEARNING.

    Returns:
        Adjusted effort in days (integer, minimum 1).
    """
    base = max(base_effort_days, MIN_EFFORT)

    if status == ProficiencyStatus.MISSING:
        multiplier = 0.70 if learning_mode == LearningMode.FAST_TRACK else 1.0
        adjusted   = math.ceil(base * multiplier)

    else:  # WEAK
        multiplier = 0.60 if learning_mode == LearningMode.FAST_TRACK else 1.0
        adjusted   = math.ceil(base * delta * multiplier)

    return max(adjusted, MIN_EFFORT)


# ---------------------------------------------------------------------------
# Time budget trimming
# ---------------------------------------------------------------------------

def _apply_time_budget(
    items:            list[PrunedItem],
    budget_days:      int,
    scores:           dict[str, float],
) -> tuple[list[PrunedItem], list[str]]:
    """
    Remove lowest-scoring items until total effort fits within budget_days.
    Preserves topological order in the returned list.

    Orphan prevention: never remove a skill if a higher-priority skill that
    depends on it is still in the retained set.

    Args:
        items:       PrunedItems in topological order.
        budget_days: Maximum total adjusted effort.
        scores:      composite_score per skill (0â€“1).

    Returns:
        (retained_items_in_topo_order, trimmed_ids)
    """
    total = sum(i.adjusted_effort_days for i in items)
    if total <= budget_days:
        return items, []

    item_ids   = {i.skill_id for i in items}
    retained   = set(item_ids)
    trimmed    = []

    # Build in-subgraph dependent map: skill_id â†’ set of IDs that depend on it
    dependents = _build_dependents_map(item_ids)

    # Sort by score ascending â€” lowest score trimmed first
    candidates = sorted(items, key=lambda i: (scores.get(i.skill_id, 0.0), i.topo_order))

    for candidate in candidates:
        if total <= budget_days:
            break

        sid = candidate.skill_id

        # Check if any retained item depends on this one
        deps_in_retained = dependents.get(sid, set()) & retained
        if deps_in_retained:
            logger.debug(
                "pruning_engine: cannot trim '%s' â€” retained dependents: %s",
                sid, deps_in_retained,
            )
            continue

        # Safe to trim
        retained.discard(sid)
        trimmed.append(sid)
        total -= candidate.adjusted_effort_days

    if total > budget_days:
        logger.warning(
            "pruning_engine: could not fit within budget=%d days "
            "(remaining=%d) without orphaning dependencies",
            budget_days, total,
        )

    # Rebuild in original topo order
    retained_items = [i for i in items if i.skill_id in retained]
    return retained_items, trimmed


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _get_levels(
    skill_id:   str,
    level_map:  dict[str, CandidateSkillLevel],
    difficulty: int,
) -> tuple[float, float]:
    """
    Return (candidate_level, required_level) for a skill.

    If the skill has no CandidateSkillLevel record (it is a structural ancestor
    not directly referenced in the JD), we conservatively assume:
      candidate_level = 0.0
      required_level  = implied from difficulty (0.4 for diff-1 â†’ 0.8 for diff-5)
    """
    record = level_map.get(skill_id)
    if record is not None:
        return record.candidate_level, record.required_level

    # Skill is an ancestor pulled into the subgraph â€” not directly in the JD.
    # Conservative assumption: candidate knows nothing, moderate requirement.
    implied_required = round(0.4 + (difficulty - 1) * 0.1, 2)   # diff 1â†’0.4, diff 5â†’0.8
    return 0.0, implied_required


def _build_dependents_map(node_ids: set[str]) -> dict[str, set[str]]:
    """
    Build a map of skill_id â†’ {skill IDs that depend on it} restricted to `node_ids`.
    Uses the global graph engine to find successors, then filters to the set.

    Args:
        node_ids: The IDs currently in the retained pruned set.

    Returns:
        Dict where dependents[x] = set of IDs in node_ids that have x as a prerequisite.
    """
    dependents: dict[str, set[str]] = {n: set() for n in node_ids}

    for node_id in node_ids:
        for successor_id in engine.get_successor_ids(node_id):
            if successor_id in node_ids:
                dependents[node_id].add(successor_id)

    return dependents


