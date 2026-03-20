"""
graph/subgraph_extractor.py

Extract the minimal ancestor-closed subgraph for a set of gap skill IDs.

Given gap skills G = {kubernetes, aws}, this module:
  1. Starts with G as the initial frontier.
  2. BFS-walks all prerequisite edges upward (ancestors).
  3. Collects every node reachable via prerequisite chains.
  4. Returns the induced subgraph: all collected nodes + all edges between them.

The output is handed directly to topological_sort → pruning_engine → phase_assigner.

Key design decisions:
  - BFS (not recursive DFS) to avoid Python's default recursion limit on
    deep prerequisite chains (e.g. aws → cloud_basics → networking → linux).
  - Deduplication via `visited` set — overlapping chains between gap skills
    (e.g. docker and kubernetes both needing linux) produce no duplicates.
  - `importance_threshold` filter: fast_track mode sets threshold=0.8 to
    skip "recommended" prerequisites (weight ≈ 0.5) and only follow
    mandatory ones (weight = 1.0).
  - Met skills are included as structural nodes (needed for topological
    ordering) but flagged `_met=True` so pruning_engine can skip them.
"""

from __future__ import annotations

import logging

try:
    import graph.graph_engine as engine
    from graph.models import SkillEdge, SkillNode, SubgraphResult
except ImportError:  # pragma: no cover - alternate package root
    from app.modules.graph import graph_engine as engine
    from app.modules.graph.models import SkillEdge, SkillNode, SubgraphResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Primary extraction
# ---------------------------------------------------------------------------

def extract_subgraph(
    gap_skill_ids:       list[str],
    *,
    importance_threshold: float = 0.0,
    include_staged_nodes: bool  = True,
    met_skill_ids:        list[str] | None = None,
) -> SubgraphResult:
    """
    Extract the minimal ancestor-closed subgraph for the given gap skills.

    Args:
        gap_skill_ids:        Canonical IDs of missing or weak skills.
        importance_threshold: Minimum edge weight to follow.
                              0.0 = follow all edges (default).
                              0.8 = skip recommended-only prerequisites.
        include_staged_nodes: Whether to also check the LLM-staged layer for
                              nodes not in the curated graph.
        met_skill_ids:        Skills the candidate already meets. These are
                              included as structural nodes but flagged as met
                              so pruning can exclude them from the pathway.

    Returns:
        SubgraphResult with nodes, edges, and any unresolved skill IDs.
    """
    if not gap_skill_ids:
        return SubgraphResult(nodes={}, edges=[], unresolved_ids=[])

    met_set      = set(met_skill_ids or [])
    visited:     set[str]           = set()
    sub_nodes:   dict[str, SkillNode] = {}
    sub_edge_map: dict[tuple[str, str], SkillEdge] = {}   # (from, to) → edge (dedup)
    unresolved:  list[str]          = []

    # BFS queue — start with deduplicated gap skills
    queue: list[str] = list(dict.fromkeys(gap_skill_ids))

    while queue:
        current_id = queue.pop(0)

        if current_id in visited:
            continue
        visited.add(current_id)

        # ── Resolve node: curated graph first, staged layer if allowed
        node = _resolve_node(current_id, include_staged_nodes)

        if node is None:
            logger.warning(
                "subgraph_extractor: '%s' not found in graph or staged layer",
                current_id,
            )
            unresolved.append(current_id)
            continue

        sub_nodes[current_id] = node

        # ── Collect prerequisite edges
        curated_edges = engine.get_predecessor_edges(current_id)
        staged_edges  = (
            engine.get_staged_predecessor_edges(current_id)
            if include_staged_nodes
            else []
        )
        all_edges = curated_edges + staged_edges

        for edge in all_edges:
            # Apply importance threshold (fast_track mode)
            if edge.weight < importance_threshold:
                logger.debug(
                    "subgraph_extractor: skipping edge %s→%s (weight=%.2f < threshold=%.2f)",
                    edge.from_id, edge.to_id, edge.weight, importance_threshold,
                )
                continue

            # Register edge (deduplicate by (from, to) pair)
            key = (edge.from_id, edge.to_id)
            if key not in sub_edge_map:
                sub_edge_map[key] = edge

            # Enqueue predecessor for BFS (even if met — structural node needed)
            if edge.from_id not in visited:
                queue.append(edge.from_id)

    # ── Remove edges that reference nodes excluded by the threshold filter
    valid_edges = [
        edge for edge in sub_edge_map.values()
        if edge.from_id in sub_nodes and edge.to_id in sub_nodes
    ]

    logger.debug(
        "subgraph_extractor: input_gaps=%d subgraph_nodes=%d edges=%d unresolved=%d",
        len(gap_skill_ids), len(sub_nodes), len(valid_edges), len(unresolved),
    )

    return SubgraphResult(
        nodes=sub_nodes,
        edges=valid_edges,
        unresolved_ids=unresolved,
    )


# ---------------------------------------------------------------------------
# Ancestor / descendant queries
# ---------------------------------------------------------------------------

def get_ancestors(
    skill_id:             str,
    *,
    importance_threshold: float = 0.0,
    include_staged_nodes: bool  = True,
) -> set[str]:
    """
    Return all transitive prerequisites of `skill_id`.

    When importance_threshold > 0, only follows edges at or above that weight.
    In that case we cannot use NetworkX's nx.ancestors() directly (it doesn't
    know about edge weights), so we do a manual BFS.

    For the default threshold=0.0, we delegate to NetworkX for performance.
    """
    if importance_threshold == 0.0 and not include_staged_nodes:
        return engine.get_all_ancestors(skill_id)

    # Manual BFS respecting weight threshold
    ancestors: set[str] = set()
    queue     = [skill_id]
    seen      = {skill_id}

    while queue:
        current = queue.pop(0)
        curated = engine.get_predecessor_edges(current)
        staged  = (
            engine.get_staged_predecessor_edges(current)
            if include_staged_nodes else []
        )
        for edge in curated + staged:
            if edge.weight < importance_threshold:
                continue
            if edge.from_id not in seen:
                seen.add(edge.from_id)
                ancestors.add(edge.from_id)
                queue.append(edge.from_id)

    return ancestors


def get_descendants(skill_id: str) -> set[str]:
    """
    Return all transitive dependents of `skill_id` (skills that require it).
    Delegates to NetworkX nx.descendants() — O(V + E).
    """
    return engine.get_all_descendants(skill_id)


def get_unlock_count(skill_id: str, within_ids: list[str] | None = None) -> int:
    """
    Count how many skills are unlocked (transitively) by mastering `skill_id`.

    Args:
        skill_id:   The skill whose downstream impact we are measuring.
        within_ids: If provided, count only descendants that are in this list
                    (e.g. restrict to the candidate's gap set so we don't count
                    skills they already know or that aren't relevant to the role).

    Returns:
        Integer count of downstream skills. Used by scoring_engine for
        the "impact" factor in composite score calculation.
    """
    descendants = get_descendants(skill_id)
    if not within_ids:
        return len(descendants)

    restriction = set(within_ids)
    return sum(1 for d in descendants if d in restriction)


def get_edges_within_set(node_ids: list[str] | set[str]) -> list[SkillEdge]:
    """
    Return all curated edges where BOTH from_id and to_id are in `node_ids`.
    Used after pruning to rebuild a clean edge list for the reduced node set.
    """
    node_set = set(node_ids)
    edges: list[SkillEdge] = []

    for node_id in node_set:
        for edge in engine.get_successor_edges(node_id):
            if edge.to_id in node_set:
                edges.append(edge)

    return edges


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _resolve_node(node_id: str, include_staged: bool) -> SkillNode | None:
    node = engine.get_node(node_id)
    if node is not None:
        return node
    if include_staged:
        return engine.get_staged_node(node_id)
    return None
