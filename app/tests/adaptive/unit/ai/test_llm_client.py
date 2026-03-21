"""Starter unit tests for AI LLM client contract."""

from __future__ import annotations

import importlib
import unittest


class TestLLMClientContract(unittest.TestCase):
    """Contract checks that stay green while implementation is in progress."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.module = importlib.import_module("app.adaptive.modules.ai.llm_client")

    def test_module_imports(self) -> None:
        self.assertIsNotNone(self.module)

    def test_expected_client_entrypoints_exist(self) -> None:
        self.assertIsNotNone(getattr(self.module, "LLMClient", None))
        for name in ("complete", "generate", "chat"):
            self.assertTrue(callable(getattr(self.module, name, None)), f"{name} should be callable")

    def test_class_and_module_entrypoints_return_text(self) -> None:
        client = self.module.LLMClient(model="test-local")
        direct = client.complete("Hello world")
        via_module = self.module.complete("Hello world")
        self.assertIsInstance(direct, str)
        self.assertTrue(direct)
        self.assertIsInstance(via_module, str)
        self.assertTrue(via_module)

    def test_generate_is_alias_of_complete(self) -> None:
        client = self.module.LLMClient(model="alias-check")
        a = client.complete("A short prompt")
        b = client.generate("A short prompt")
        self.assertEqual(a, b)

    def test_chat_accepts_message_list(self) -> None:
        output = self.module.chat(
            [
                {"role": "system", "content": "You are concise"},
                {"role": "user", "content": "Summarize testing"},
            ]
        )
        self.assertIsInstance(output, str)
        self.assertTrue(output)


if __name__ == "__main__":
    unittest.main()
