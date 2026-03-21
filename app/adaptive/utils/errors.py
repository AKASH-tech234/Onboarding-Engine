"""
utils/errors.py

Custom exception hierarchy for the graph engine pipeline.
All exceptions carry a machine-readable `code` attribute so the
API layer can map them to HTTP status codes without string matching.
"""


class GraphEngineError(Exception):
    """Base class for all graph engine errors."""
    code: str = "GRAPH_ENGINE_ERROR"


class GraphLoadError(GraphEngineError):
    """
    Raised when the graph file cannot be read, is malformed,
    contains duplicate nodes, has invalid edge references, or
    contains a cycle that was not resolved before load.
    """
    code = "GRAPH_LOAD_ERROR"


class GraphNotLoadedError(GraphEngineError):
    """Raised when a graph operation is called before loadGraph()."""
    code = "GRAPH_NOT_LOADED"


class CircularDependencyError(GraphEngineError):
    """
    Raised when a cycle is detected in graph data that cannot
    be automatically resolved (e.g. all edges are mandatory weight 1.0).
    """
    code = "CIRCULAR_DEPENDENCY"

    def __init__(self, message: str, cycle: list[str] | None = None):
        super().__init__(message)
        self.cycle = cycle or []


class TopologicalSortError(GraphEngineError):
    """
    Raised by topological_sort() when the input subgraph still contains
    a cycle after Kahn's algorithm finishes â€” output is shorter than input.
    """
    code = "TOPOLOGICAL_SORT_ERROR"

    def __init__(self, message: str, unprocessed_nodes: list[str] | None = None):
        super().__init__(message)
        self.unprocessed_nodes = unprocessed_nodes or []

