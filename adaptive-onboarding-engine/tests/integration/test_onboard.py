"""Integration tests for onboarding controller flow."""

from __future__ import annotations

import asyncio
import importlib
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = PROJECT_ROOT / "app"
MODULES_ROOT = APP_ROOT / "modules"

for path in (str(APP_ROOT), str(MODULES_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)


def _sample_graph_dict() -> dict[str, object]:
    return {
        "version": "v1",
        "nodes": [
            {
                "id": "python",
                "label": "Python",
                "domain": "backend",
                "base_effort_days": 3,
                "difficulty": 2,
                "tags": [],
                "source": "curated",
            },
            {
                "id": "fastapi",
                "label": "FastAPI",
                "domain": "backend",
                "base_effort_days": 4,
                "difficulty": 3,
                "tags": [],
                "source": "curated",
            },
        ],
        "edges": [
            {"from": "python", "to": "fastapi", "importance": "mandatory", "weight": 1.0},
        ],
    }


def _sample_request() -> dict[str, object]:
    return {
        "request_id": "req-int-1",
        "candidate_profile": {
            "id": "cand-1",
            "skills": [
                {"name": "Python", "score": 0.7, "confidence": 0.9},
            ],
        },
        "requirement_profile": {
            "id": "job-1",
            "skills": [
                {"name": "Python", "score": 0.8, "confidence": 1.0},
                {"name": "FastAPI", "score": 0.9, "confidence": 1.0},
            ],
        },
        "options": {
            "role": "backend",
            "graph_version": "v1",
            "learning_mode": "deep_learning",
        },
    }


class TestOnboardIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.graph_engine = importlib.import_module("graph.graph_engine")
        cls.onboard_controller = importlib.import_module("api.controllers.onboard_controller")

    def setUp(self) -> None:
        self.graph_engine.reset_for_tests()
        self.graph_engine.load_graph_from_dict(_sample_graph_dict())

    def test_onboard_completes_and_returns_pathway_payload(self) -> None:
        response = asyncio.run(self.onboard_controller.onboard(_sample_request()))

        status = getattr(response.status, "value", response.status)
        self.assertEqual(status, "completed")
        self.assertIsNotNone(response.job_id)
        self.assertIsInstance(response.result, dict)
        self.assertIn("summary", response.result)
        self.assertIn("phases", response.result)
        self.assertGreaterEqual(response.result["summary"]["total_items"], 1)

    def test_preview_returns_estimated_gap_count(self) -> None:
        preview = asyncio.run(self.onboard_controller.preview(_sample_request()))
        self.assertTrue(preview.accepted)
        self.assertGreaterEqual(preview.estimated_gap_count, 1)

    def test_refresh_reruns_pipeline(self) -> None:
        first = asyncio.run(self.onboard_controller.onboard(_sample_request()))
        refreshed = asyncio.run(
            self.onboard_controller.refresh(
                _sample_request(),
                previous_job_id=first.job_id,
            )
        )

        first_status = getattr(first.status, "value", first.status)
        refresh_status = getattr(refreshed.status, "value", refreshed.status)
        self.assertEqual(first_status, "completed")
        self.assertEqual(refresh_status, "completed")
        self.assertNotEqual(first.job_id, refreshed.job_id)

    def test_onboard_requires_requirement_or_job_profile(self) -> None:
        bad_request = {
            "candidate_profile": {"id": "cand-x", "skills": []},
            "options": {},
        }
        with self.assertRaises(ValueError):
            asyncio.run(self.onboard_controller.onboard(bad_request))


if __name__ == "__main__":
    unittest.main()
