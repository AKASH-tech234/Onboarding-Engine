"""Starter unit tests for scoring engine contract."""

from __future__ import annotations

import importlib
import unittest


class TestScoringEngineContract(unittest.TestCase):
    """
    Contract-focused starter tests.

    These tests are intentionally permissive while the module is still under
    active implementation.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.module = importlib.import_module("app.adaptive.modules.scoring.scoring_engine")

    def test_module_imports(self) -> None:
        self.assertIsNotNone(self.module)

    def test_core_callables_exist(self) -> None:
        for name in ("score", "score_skill", "compute_composite_score"):
            self.assertTrue(callable(getattr(self.module, name, None)), f"{name} should be callable")

    def test_compute_composite_score_returns_clamped_value(self) -> None:
        value = self.module.compute_composite_score(
            criticality=1.0,
            impact=0.5,
            efficiency=0.8,
            recency=0.2,
        )
        self.assertIsInstance(value, float)
        self.assertGreaterEqual(value, 0.0)
        self.assertLessEqual(value, 1.0)

    def test_score_skill_prefers_higher_impact_and_lower_effort(self) -> None:
        high_signal = self.module.score_skill(
            gap=0.8,
            unlock_count=10,
            effort_days=3,
            recency_months=1,
        )
        low_signal = self.module.score_skill(
            gap=0.8,
            unlock_count=1,
            effort_days=20,
            recency_months=18,
        )
        self.assertGreater(high_signal, low_signal)

    def test_score_dict_entrypoint(self) -> None:
        result = self.module.score(
            {
                "gap": 0.6,
                "unlock_count": 4,
                "effort_days": 5,
                "recency_months": 3,
            }
        )
        self.assertIsInstance(result, float)
        self.assertGreaterEqual(result, 0.0)
        self.assertLessEqual(result, 1.0)


if __name__ == "__main__":
    unittest.main()
