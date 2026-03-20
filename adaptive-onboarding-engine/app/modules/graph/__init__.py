"""
app/modules/graph/__init__.py

Minimal package exports for the graph module.

This file intentionally stays small so submodule imports like
`import graph.graph_engine` do not fail because of unrelated re-export
mismatches elsewhere in the package.
"""

from .graph_engine import (
    GraphEngine,
    SkillEdge,
    SkillNode,
    get_dependents,
    get_prerequisites,
    load_graph,
    load_graph_from_dict,
)

__all__ = [
    "GraphEngine",
    "SkillNode",
    "SkillEdge",
    "load_graph",
    "load_graph_from_dict",
    "get_prerequisites",
    "get_dependents",
]
