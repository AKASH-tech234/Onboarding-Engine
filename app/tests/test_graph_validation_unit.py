import json
import subprocess
import sys
from pathlib import Path


def _script_path() -> str:
    return str(Path(__file__).resolve().parents[2] / "scripts" / "validate_graph.py")


def _write_graph(tmp_path, payload: dict) -> str:
    path = tmp_path / "graph.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


def test_validate_graph_script_success(tmp_path) -> None:
    graph = {
        "version": "v1",
        "nodes": [{"id": "python"}, {"id": "ml"}],
        "edges": [{"from": "python", "to": "ml"}],
    }
    graph_path = _write_graph(tmp_path, graph)

    result = subprocess.run(
        [sys.executable, _script_path(), "--path", graph_path],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert report["has_cycle"] is False
    assert report["nodes"] == 2


def test_validate_graph_script_cycle_fails(tmp_path) -> None:
    graph = {
        "version": "v1",
        "nodes": [{"id": "a"}, {"id": "b"}],
        "edges": [{"from": "a", "to": "b"}, {"from": "b", "to": "a"}],
    }
    graph_path = _write_graph(tmp_path, graph)

    result = subprocess.run(
        [sys.executable, _script_path(), "--path", graph_path],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report["has_cycle"] is True
    assert report["cycle_path"]
