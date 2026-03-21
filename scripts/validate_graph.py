from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = REPO_ROOT / "app"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from modules.graph.cycle_detector import detect_cycle
from modules.graph.graph_engine import load_graph_with_diagnostics


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate skill graph data")
    parser.add_argument("--path", default="", help="Explicit graph path")
    parser.add_argument("--version", default="v1", help="Graph version suffix")
    args = parser.parse_args()

    graph_path = args.path if args.path else None
    graph, diagnostics = load_graph_with_diagnostics(path=graph_path, version=args.version)
    has_cycle, cycle_path = detect_cycle(graph)

    report = {
        "version": diagnostics.version,
        "nodes": len(graph.nodes),
        "edges": len(graph.edges),
        "duplicate_edges": diagnostics.duplicate_edges,
        "self_loops": diagnostics.self_loops,
        "unknown_edges": diagnostics.unknown_edges,
        "orphan_nodes": diagnostics.orphan_nodes,
        "has_cycle": has_cycle,
        "cycle_path": cycle_path,
    }
    print(json.dumps(report, indent=2))

    if has_cycle:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
