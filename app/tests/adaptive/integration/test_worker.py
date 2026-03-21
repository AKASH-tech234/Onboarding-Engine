"""Integration tests for in-memory worker pipeline."""

from __future__ import annotations

import importlib
import unittest


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


def _sample_worker_request() -> dict[str, object]:
    return {
        "candidate_profile": {
            "id": "cand-worker-1",
            "skills": [{"name": "Python", "score": 0.7, "confidence": 0.9}],
        },
        "requirement_profile": {
            "id": "job-worker-1",
            "skills": [
                {"name": "Python", "score": 0.8, "confidence": 1.0},
                {"name": "FastAPI", "score": 0.9, "confidence": 1.0},
            ],
        },
        "options": {"role": "backend"},
    }


class TestWorkerIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.graph_engine = importlib.import_module("app.adaptive.modules.graph.graph_engine")
        cls.pathway_worker = importlib.import_module("app.adaptive.workers.pathway_worker")
        cls.trace_worker = importlib.import_module("app.adaptive.workers.trace_worker")
        cls.expansion_worker = importlib.import_module("app.adaptive.workers.expansion_worker")

        cls.job_manager = cls.pathway_worker.job_manager
        cls.job_queue = cls.pathway_worker.job_queue

    def setUp(self) -> None:
        self.graph_engine.reset_for_tests()
        self.graph_engine.load_graph_from_dict(_sample_graph_dict())
        self.job_queue.clear_queue()

    def test_pathway_worker_processes_queue_and_updates_job(self) -> None:
        job = self.job_manager.create_job(candidate_id="cand-worker-1", job_profile_id="job-worker-1")

        self.pathway_worker.enqueue_pathway_task(
            _sample_worker_request(),
            job_id=job.job_id,
        )
        result = self.pathway_worker.run_once()

        self.assertIsNotNone(result)
        self.assertTrue(result["ok"])
        updated = self.job_manager.get_job_status(job.job_id)
        self.assertIsNotNone(updated)
        updated_status = getattr(updated.status, "value", updated.status)
        self.assertEqual(updated_status, "completed")
        self.assertIsInstance(updated.result, dict)
        self.assertIn("summary", updated.result)

    def test_trace_worker_appends_reasoning_trace(self) -> None:
        job = self.job_manager.create_job(candidate_id="cand-trace-1", job_profile_id="job-trace-1")
        self.job_manager.update_job(
            job.job_id,
            status="completed",
            result={
                "summary": {
                    "total_items": 2,
                    "total_phases": 1,
                    "total_effort_days": 4,
                    "unresolved_count": 0,
                }
            },
        )

        self.trace_worker.enqueue_trace_task(job_id=job.job_id)
        result = self.trace_worker.run_once()

        self.assertIsNotNone(result)
        self.assertTrue(result["ok"])
        updated = self.job_manager.get_job_status(job.job_id)
        self.assertIsNotNone(updated)
        self.assertIn("reasoning_trace", updated.result)
        self.assertIn("raw", updated.result["reasoning_trace"])

    def test_expansion_worker_stages_new_skill(self) -> None:
        self.expansion_worker.enqueue_expansion_task("GraphQL", domain_hint="backend")
        result = self.expansion_worker.run_once()

        self.assertIsNotNone(result)
        self.assertTrue(result["ok"])
        self.assertTrue(result["staged"])
        staged = self.graph_engine.get_staged_node("graphql")
        self.assertIsNotNone(staged)
        self.assertEqual(staged.domain, "backend")

    def test_run_once_returns_none_when_queue_empty(self) -> None:
        self.assertIsNone(self.pathway_worker.run_once())
        self.assertIsNone(self.trace_worker.run_once())
        self.assertIsNone(self.expansion_worker.run_once())


if __name__ == "__main__":
    unittest.main()
