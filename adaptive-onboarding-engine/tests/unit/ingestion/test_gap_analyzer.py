"""Unit tests for ingestion.gap_analyzer."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
APP_ROOT = PROJECT_ROOT / "app"
MODULES_ROOT = APP_ROOT / "modules"

for path in (str(APP_ROOT), str(MODULES_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

from ingestion.gap_analyzer import analyze_gaps  # noqa: E402


class TestGapAnalyzer(unittest.TestCase):
    """Starter coverage for gap classification and input handling."""

    def test_classifies_missing_weak_and_strong(self) -> None:
        payload = {
            "candidate_profile": {
                "skills": [
                    {"name": "Python", "score": 0.6, "confidence": 1.0},
                    {"name": "Docker", "score": 0.1, "confidence": 1.0},
                    {"name": "SQL", "score": 0.9, "confidence": 1.0},
                ]
            },
            "requirement_profile": {
                "skills": [
                    {"name": "Python", "score": 1.0, "confidence": 1.0},   # gap 0.4 -> weak
                    {"name": "Docker", "score": 0.7, "confidence": 1.0},   # gap 0.6 -> missing
                    {"name": "SQL", "score": 0.95, "confidence": 1.0},     # gap 0.05 -> strong
                ]
            },
        }

        result = analyze_gaps(payload)

        self.assertEqual([item["name"] for item in result["missing"]], ["Docker"])
        self.assertEqual([item["name"] for item in result["weak"]], ["Python"])
        self.assertEqual([item["name"] for item in result["strong"]], ["SQL"])

    def test_supports_split_signature_and_normalizes_skill_names(self) -> None:
        candidate_profile = {
            "skills": [
                {"name": "  PYTHON  ", "score": 0.2, "confidence": 1.0},
                {"name": "python", "score": 0.9, "confidence": 0.9},  # duplicate, higher effective
            ]
        }
        requirement_profile = {
            "skills": [
                {"name": "Python", "score": 0.7, "confidence": 1.0},
            ]
        }

        result = analyze_gaps(candidate_profile, requirement_profile)
        self.assertEqual(len(result["strong"]), 1)
        self.assertEqual(result["strong"][0]["name"], "Python")
        self.assertAlmostEqual(result["strong"][0]["effective_candidate"], 0.81, places=4)

    def test_handles_invalid_numbers_and_missing_lists(self) -> None:
        payload = {
            "candidate_profile": {
                "skills": [
                    {"name": "Kubernetes", "score": "bad", "confidence": 2.0},
                ]
            },
            "requirement_profile": {
                "skills": [
                    {"name": "Kubernetes", "score": 2.0, "confidence": 2.0},
                ]
            },
        }

        result = analyze_gaps(payload)
        self.assertEqual(len(result["missing"]), 1)
        self.assertEqual(result["missing"][0]["name"], "Kubernetes")
        self.assertAlmostEqual(result["missing"][0]["effective_candidate"], 0.0, places=4)
        self.assertAlmostEqual(result["missing"][0]["effective_required"], 1.0, places=4)

        empty_result = analyze_gaps({"candidate_profile": {}, "requirement_profile": {}})
        self.assertEqual(empty_result, {"missing": [], "weak": [], "strong": []})


if __name__ == "__main__":
    unittest.main()
