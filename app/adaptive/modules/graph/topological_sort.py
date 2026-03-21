"""
app/modules/graph/topological_sort.py

Topological sorting helpers for adjacency-list graphs.

Graph convention:
  graph["a"] = ["b", "c"]

This means there are directed edges:
  a -> b
  a -> c

In other words, "b" and "c" depend on "a", so "a" must appear earlier
in the topological order.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import heapq
from collections.abc import Iterable, Mapping, Sequence


class CycleError(ValueError):
    """Raised when the graph contains a cycle and cannot be topologically sorted."""

    def __init__(self, message: str, cycle_nodes: list[str] | None = None):
        super().__init__(message)
        self.cycle_nodes = cycle_nodes or []


@dataclass(frozen=True)
class SortResult:
    """Optional richer result wrapper for callers that want cycle metadata."""

    order: list[str] = field(default_factory=list)
    has_cycle: bool = False
    cycle_nodes: list[str] = field(default_factory=list)


def topological_sort(graph: Mapping[str, Iterable[str]] | None) -> list[str]:
    """
    Return a topological ordering of an adjacency-list graph using Kahn's algorithm.

    Args:
        graph: Mapping of node -> iterable of outgoing neighbors.

    Returns:
        Ordered list of nodes where every node appears before its dependents.

    Raises:
        CycleError: If the graph contains a cycle.
    """
    adjacency = _normalize_graph(graph)
    if not adjacency:
        return []

    in_degree = _compute_in_degree(adjacency)
    ready = [node for node, degree in in_degree.items() if degree == 0]
    heapq.heapify(ready)

    ordered: list[str] = []

    while ready:
        node = heapq.heappop(ready)
        ordered.append(node)

        for neighbor in adjacency[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                heapq.heappush(ready, neighbor)

    if len(ordered) != len(adjacency):
        cycle_nodes = sorted(node for node in adjacency if node not in set(ordered))
        raise CycleError(
            "Cycle detected: graph cannot be topologically sorted.",
            cycle_nodes=cycle_nodes,
        )

    return ordered


def detect_cycle(graph: Mapping[str, Iterable[str]] | None) -> bool:
    """
    Return True if the graph contains a cycle, otherwise False.
    """
    try:
        topological_sort(graph)
    except CycleError:
        return True
    return False


def topological_sort_all(graph: Mapping[str, Iterable[str]] | None) -> SortResult:
    """
    Convenience wrapper that returns either the order or cycle details.
    """
    try:
        return SortResult(order=topological_sort(graph), has_cycle=False, cycle_nodes=[])
    except CycleError as error:
        return SortResult(order=[], has_cycle=True, cycle_nodes=error.cycle_nodes)


def compute_critical_levels(topo_order: list[str], edges: Sequence[object]) -> dict[str, int]:
    """
    Compute longest prerequisite-chain level for each node.

    Level 0 means no in-subgraph prerequisites.
    Level N means this node has a longest prerequisite chain of length N.
    """
    levels: dict[str, int] = {node_id: 0 for node_id in topo_order}
    if not topo_order:
        return levels

    predecessors: dict[str, list[str]] = {node_id: [] for node_id in topo_order}
    node_set = set(topo_order)

    for edge in edges:
        from_id = getattr(edge, "from_id", None)
        to_id = getattr(edge, "to_id", None)
        if from_id in node_set and to_id in node_set:
            predecessors[to_id].append(from_id)

    for node_id in topo_order:
        preds = predecessors.get(node_id, [])
        if preds:
            levels[node_id] = max(levels.get(pred, 0) for pred in preds) + 1

    return levels


def transitive_prerequisites(
    graph: Mapping[str, Iterable[str]] | None,
    target: str,
) -> set[str]:
    """
    Return all prerequisite nodes that must come before `target`.
    """
    adjacency = _normalize_graph(graph)
    if target not in adjacency:
        return set()

    reverse_graph = _build_reverse_graph(adjacency)
    prerequisites: set[str] = set()
    stack = list(reverse_graph.get(target, []))

    while stack:
        node = stack.pop()
        if node in prerequisites:
            continue
        prerequisites.add(node)
        stack.extend(reverse_graph.get(node, []))

    return prerequisites


def example_graph() -> dict[str, list[str]]:
    """
    Example DAG for local testing and documentation.
    """
    return {
        "programming_basics": ["python"],
        "python": ["fastapi", "pandas"],
        "git": ["ci_cd"],
        "linux": ["docker"],
        "docker": ["kubernetes"],
        "fastapi": [],
        "pandas": [],
        "ci_cd": [],
        "kubernetes": [],
    }


def test_topological_sort() -> None:
    """
    Small self-contained test suite using plain assertions.
    """
    graph = example_graph()
    ordered = topological_sort(graph)

    assert len(ordered) == len(_normalize_graph(graph))
    _assert_before(ordered, "programming_basics", "python")
    _assert_before(ordered, "python", "fastapi")
    _assert_before(ordered, "python", "pandas")
    _assert_before(ordered, "linux", "docker")
    _assert_before(ordered, "docker", "kubernetes")
    _assert_before(ordered, "git", "ci_cd")
    assert detect_cycle(graph) is False

    prerequisites = transitive_prerequisites(graph, "kubernetes")
    assert prerequisites == {"linux", "docker"}

    cycle_graph = {
        "a": ["b"],
        "b": ["c"],
        "c": ["a"],
    }
    assert detect_cycle(cycle_graph) is True

    try:
        topological_sort(cycle_graph)
    except CycleError as error:
        assert set(error.cycle_nodes) == {"a", "b", "c"}
    else:
        raise AssertionError("Expected CycleError for cyclic graph")


def _normalize_graph(graph: Mapping[str, Iterable[str]] | None) -> dict[str, list[str]]:
    """
    Normalize an adjacency-list graph into a clean dict[str, list[str]].

    - Missing graph becomes an empty graph.
    - Neighbor-only nodes are added automatically.
    - Duplicate edges are removed while preserving neighbor order.
    """
    if not isinstance(graph, Mapping):
        return {}

    normalized: dict[str, list[str]] = {}

    for raw_node, raw_neighbors in graph.items():
        node = _normalize_node(raw_node)
        if not node:
            continue

        neighbors = _coerce_neighbors(raw_neighbors)
        cleaned_neighbors: list[str] = []
        seen: set[str] = set()

        for raw_neighbor in neighbors:
            neighbor = _normalize_node(raw_neighbor)
            if not neighbor or neighbor in seen:
                continue
            seen.add(neighbor)
            cleaned_neighbors.append(neighbor)

        normalized[node] = cleaned_neighbors

    for neighbors in list(normalized.values()):
        for neighbor in neighbors:
            normalized.setdefault(neighbor, [])

    return normalized


def _compute_in_degree(graph: Mapping[str, Iterable[str]]) -> dict[str, int]:
    """Compute in-degree for each node in the graph."""
    in_degree = {node: 0 for node in graph}

    for neighbors in graph.values():
        for neighbor in neighbors:
            in_degree[neighbor] += 1

    return in_degree


def _build_reverse_graph(graph: Mapping[str, Iterable[str]]) -> dict[str, list[str]]:
    """Build a reverse adjacency list for prerequisite lookup."""
    reverse_graph = {node: [] for node in graph}

    for node, neighbors in graph.items():
        for neighbor in neighbors:
            reverse_graph[neighbor].append(node)

    return reverse_graph


def _coerce_neighbors(raw_neighbors: Iterable[str] | None) -> list[str]:
    """Convert a neighbor collection into a list."""
    if raw_neighbors is None:
        return []
    if isinstance(raw_neighbors, str):
        return [raw_neighbors]
    try:
        return list(raw_neighbors)
    except TypeError:
        return []


def _normalize_node(node: object) -> str:
    """Normalize a node value into a non-empty string identifier."""
    if not isinstance(node, str):
        return ""
    return " ".join(node.split())


def _assert_before(order: list[str], earlier: str, later: str) -> None:
    """Assert that one node appears before another in a topological order."""
    positions = {node: index for index, node in enumerate(order)}
    assert positions[earlier] < positions[later], (
        f"Expected '{earlier}' before '{later}' in {order}"
    )


if __name__ == "__main__":
    sample_graph = example_graph()
    print("Example graph:", sample_graph)
    print("Topological order:", topological_sort(sample_graph))
    test_topological_sort()
    print("All tests passed.")


