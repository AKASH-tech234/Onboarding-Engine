"""Stable topological sort for extracted subgraphs."""

from __future__ import annotations


def topo_sort(nodes: list[str], edges: list[tuple[str, str]]) -> list[str]:
    node_set = set(nodes)
    indegree = {node: 0 for node in node_set}
    adjacency: dict[str, set[str]] = {node: set() for node in node_set}

    for source, target in edges:
        if source not in node_set or target not in node_set:
            continue
        if target not in adjacency[source]:
            adjacency[source].add(target)
            indegree[target] += 1

    queue = sorted([node for node in node_set if indegree[node] == 0])
    result: list[str] = []

    while queue:
        node = queue.pop(0)
        result.append(node)

        for child in sorted(adjacency[node]):
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
        queue.sort()

    if len(result) != len(node_set):
        raise ValueError("Subgraph contains a cycle")

    return result
