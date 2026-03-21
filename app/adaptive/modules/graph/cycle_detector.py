"""
graph/cycle_detector.py

Cycle detection and resolution for the skill dependency DAG.

Two algorithms:
  1. detect()           â€” fast single-cycle detection via DFS 3-colour marking.
  2. find_all_cycles()  â€” find every cycle via NetworkX simple_cycles().
  3. find_edge_to_break() â€” pick the weakest edge in a cycle to remove.
  4. resolve_all_cycles() â€” iteratively break edges until the graph is a DAG.

All functions that modify graph structure operate on COPIES â€” the original
NetworkX DiGraph is never mutated. Callers receive the modified copy and a
log of broken edges, then decide whether to apply the changes.

Used in two contexts:
  - At load time: graph_engine raises GraphLoadError if cycles exist.
    The graph admin must fix graph-data source files.
  - At runtime: when LLM-generated staged nodes are added, resolve_all_cycles()
    is run on the expanded subgraph before pathway generation proceeds.
"""

from __future__ import annotations

import logging
from enum import IntEnum

import networkx as nx

try:
    from app.adaptive.modules.graph.models import SkillEdge
    from app.adaptive.utils.errors import CircularDependencyError
except ImportError:  # pragma: no cover - alternate package root
    from app.adaptive.modules.graph.models import SkillEdge
    from app.adaptive.utils.errors import CircularDependencyError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# DFS colour constants
# ---------------------------------------------------------------------------

class _Colour(IntEnum):
    WHITE = 0   # not yet visited
    GREY  = 1   # currently in DFS path (in the stack)
    BLACK = 2   # fully processed â€” no unvisited successor


# ---------------------------------------------------------------------------
# 1. Single-cycle detection â€” fast, iterative DFS
# ---------------------------------------------------------------------------

def detect(g: nx.DiGraph) -> tuple[bool, list[str]]:
    """
    Detect whether `g` contains at least one cycle.

    Uses iterative DFS with 3-colour marking to avoid Python's recursion limit
    on large graphs. Returns on the first cycle found.

    Args:
        g: A NetworkX DiGraph (need not be the singleton â€” works on any DiGraph).

    Returns:
        (has_cycle, cycle) where cycle is a list of node IDs forming the cycle,
        e.g. ["docker", "kubernetes", "docker"].
        cycle is [] if has_cycle is False.
    """
    colour  = {node: _Colour.WHITE for node in g.nodes}
    parent  = {}                    # node â†’ node (DFS tree parent)

    for start in g.nodes:
        if colour[start] != _Colour.WHITE:
            continue

        result = _dfs_iterative(start, colour, parent, g)
        if result[0]:
            return result

    return False, []


def _dfs_iterative(
    start:  str,
    colour: dict[str, _Colour],
    parent: dict[str, str],
    g:      nx.DiGraph,
) -> tuple[bool, list[str]]:
    """
    Run iterative DFS from `start`. Returns (has_cycle, cycle_path).
    Mutates `colour` and `parent` in place (shared with the outer loop).
    """
    # Stack holds (node_id, neighbour_iterator)
    colour[start] = _Colour.GREY
    stack = [(start, iter(g.successors(start)))]

    while stack:
        node, neighbours = stack[-1]

        try:
            neighbour = next(neighbours)

            if colour[neighbour] == _Colour.GREY:
                # Back edge â†’ cycle confirmed
                cycle = _reconstruct_cycle(node, neighbour, parent)
                return True, cycle

            if colour[neighbour] == _Colour.WHITE:
                colour[neighbour] = _Colour.GREY
                parent[neighbour] = node
                stack.append((neighbour, iter(g.successors(neighbour))))

        except StopIteration:
            # All neighbours of `node` processed
            colour[node] = _Colour.BLACK
            stack.pop()

    return False, []


def _reconstruct_cycle(from_id: str, to_id: str, parent: dict[str, str]) -> list[str]:
    """
    Reconstruct the cycle path given the back-edge from_id â†’ to_id.
    Walks parent pointers from from_id back to to_id, then reverses
    to produce a forward-edge-order list: [to_id, ..., from_id, to_id].

    Args:
        from_id: Node where the back edge originates.
        to_id:   Node where the back edge points (an ancestor in DFS tree).
        parent:  DFS parent map.

    Returns:
        List of node IDs forming the cycle, closed at both ends.
    """
    middle:  list[str] = []
    current: str | None = from_id
    visited: set[str]   = {to_id}

    while current != to_id:
        if current is None or current in visited:
            break   # safety: broken parent chain
        visited.add(current)
        middle.append(current)
        current = parent.get(current)

    # middle = [from_id, ..., child_of_to_id] â€” reverse for forward order
    middle.reverse()
    return [to_id] + middle + [to_id]


# ---------------------------------------------------------------------------
# 2. Find ALL cycles
# ---------------------------------------------------------------------------

def find_all_cycles(g: nx.DiGraph) -> list[list[str]]:
    """
    Return every simple cycle in `g` using NetworkX's implementation of
    Johnson's algorithm (polynomial time, practical for graphs < 500 nodes).

    Each cycle is returned as a closed list: [a, b, c, a].

    Args:
        g: A NetworkX DiGraph.

    Returns:
        List of cycles; each cycle is a list of node IDs.
        Empty list if the graph is acyclic.
    """
    simple_cycles = list(nx.simple_cycles(g))
    # nx.simple_cycles returns [a, b, c] (open) â€” close each one
    return [cycle + [cycle[0]] for cycle in simple_cycles]


# ---------------------------------------------------------------------------
# 3. Edge selection for breaking a cycle
# ---------------------------------------------------------------------------

def find_edge_to_break(
    cycle: list[str],
    g:     nx.DiGraph,
) -> dict | None:
    """
    Given a closed cycle path [a, b, c, a], return the edge that should be
    removed to break the cycle. Strategy: remove the edge with the lowest
    breakability score, defined as:

        score = weight Ã— importance_multiplier
        importance_multiplier = 2.0 for mandatory, 1.0 for recommended

    Recommended edges (low importance_multiplier) break before mandatory ones.
    Among equal scores, lower weight wins.

    Args:
        cycle: Closed list of node IDs, e.g. ["a", "b", "c", "a"].
        g:     NetworkX DiGraph carrying SkillEdge objects on edges.

    Returns:
        dict {"from_id": str, "to_id": str, "edge": SkillEdge} for the edge
        to remove, or None if no edge was found (malformed cycle).
    """
    best_candidate  = None
    best_score      = float("inf")

    # Iterate consecutive pairs: (cycle[0], cycle[1]), ..., (cycle[-2], cycle[-1])
    for from_id, to_id in zip(cycle[:-1], cycle[1:]):
        if not g.has_edge(from_id, to_id):
            continue

        edge: SkillEdge = g.edges[from_id, to_id]["skill_edge"]
        importance_mult = 2.0 if edge.importance.value == "mandatory" else 1.0
        score           = edge.weight * importance_mult

        if score < best_score:
            best_score      = score
            best_candidate  = {"from_id": from_id, "to_id": to_id, "edge": edge}

    return best_candidate


# ---------------------------------------------------------------------------
# 4. Iterative cycle resolution
# ---------------------------------------------------------------------------

def resolve_all_cycles(g: nx.DiGraph) -> tuple[nx.DiGraph, list[dict]]:
    """
    Iteratively detect and break cycles until the graph is a DAG.
    Operates on a COPY of `g` â€” the original is never mutated.

    Each iteration:
      1. Find the first cycle via detect().
      2. Find the weakest edge in that cycle via find_edge_to_break().
      3. Remove the edge from the copy.
      4. Record the broken edge for audit logging.

    Args:
        g: Input NetworkX DiGraph (may contain cycles).

    Returns:
        (dag_copy, broken_edges) where:
          dag_copy is a cycle-free copy of g,
          broken_edges is a list of {"from_id", "to_id", "edge"} dicts.

    Raises:
        CircularDependencyError: If a cycle cannot be resolved because no
            breakable edge is found (e.g. malformed cycle path).
    """
    dag = g.copy()
    broken_edges: list[dict] = []

    # Safety cap: a DAG needs at most (E - V + 1) edge removals.
    max_iterations = max(dag.number_of_edges(), 1)

    for _ in range(max_iterations):
        has_cycle, cycle = detect(dag)
        if not has_cycle:
            break

        candidate = find_edge_to_break(cycle, dag)
        if candidate is None:
            raise CircularDependencyError(
                f"Cannot resolve cycle [{' â†’ '.join(cycle)}]. "
                "No breakable edge found â€” inspect graph-data source.",
                cycle=cycle,
            )

        dag.remove_edge(candidate["from_id"], candidate["to_id"])
        broken_edges.append(candidate)
        logger.warning(
            "cycle_detector: broke edge %s â†’ %s (weight=%.2f, importance=%s)",
            candidate["from_id"], candidate["to_id"],
            candidate["edge"].weight, candidate["edge"].importance.value,
        )

    return dag, broken_edges


