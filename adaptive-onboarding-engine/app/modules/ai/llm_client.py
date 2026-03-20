"""
app/modules/ai/llm_client.py

Lightweight LLM client wrapper with safe local fallback behavior.

This module intentionally does not require any external SDK at import time.
If no provider is configured, it returns deterministic mock text so the rest
of the pipeline can continue in local/dev/test environments.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from collections.abc import Mapping, Sequence

try:
    from config.llm_config import get_llm_config
except ImportError:  # pragma: no cover - alternate package root
    from app.config.llm_config import get_llm_config


@dataclass
class LLMClient:
    """Simple model client wrapper with deterministic fallback responses."""

    model: str = "mock-local"
    api_key: str | None = None
    timeout_seconds: float = 10.0
    max_retries: int = 0

    def complete(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        max_tokens: int = 512,
        temperature: float = 0.0,
    ) -> str:
        """
        Generate a completion for a prompt.
        """
        _ = max_tokens
        _ = temperature

        if not isinstance(prompt, str) or not prompt.strip():
            return ""

        if self.api_key:
            return self._provider_completion(prompt=prompt, system_prompt=system_prompt)

        return self._mock_completion(prompt=prompt, system_prompt=system_prompt)

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Alias for complete()."""
        return self.complete(prompt, **kwargs)

    def chat(
        self,
        messages: Sequence[Mapping[str, Any]],
        *,
        system_prompt: str | None = None,
        max_tokens: int = 512,
        temperature: float = 0.0,
    ) -> str:
        """
        Chat-style interface that maps messages to a plain completion.
        """
        prompt = _messages_to_prompt(messages)
        return self.complete(
            prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    async def acomplete(self, prompt: str, **kwargs: Any) -> str:
        """Async convenience wrapper for complete()."""
        return self.complete(prompt, **kwargs)

    async def agenerate(self, prompt: str, **kwargs: Any) -> str:
        """Async convenience wrapper for generate()."""
        return self.generate(prompt, **kwargs)

    async def achat(self, messages: Sequence[Mapping[str, Any]], **kwargs: Any) -> str:
        """Async convenience wrapper for chat()."""
        return self.chat(messages, **kwargs)

    def _provider_completion(self, *, prompt: str, system_prompt: str | None) -> str:
        """
        Placeholder provider behavior.

        In this scaffold we keep provider calls deterministic and side-effect
        free. Wire your SDK call here when infrastructure config is ready.
        """
        return self._mock_completion(prompt=prompt, system_prompt=system_prompt)

    def _mock_completion(self, *, prompt: str, system_prompt: str | None) -> str:
        prefix = f"[{self.model}]"
        if system_prompt and system_prompt.strip():
            prefix = f"{prefix} {system_prompt.strip()[:40]}"
        return f"{prefix} {prompt.strip()[:240]}".strip()


def _build_default_client() -> LLMClient:
    cfg = get_llm_config()
    return LLMClient(
        model=cfg.model,
        api_key=cfg.api_key,
        timeout_seconds=cfg.timeout_seconds,
        max_retries=cfg.max_retries,
    )


_DEFAULT_CLIENT = _build_default_client()


def set_default_client(client: LLMClient) -> None:
    global _DEFAULT_CLIENT
    _DEFAULT_CLIENT = client


def get_default_client() -> LLMClient:
    return _DEFAULT_CLIENT


def complete(prompt: str, **kwargs: Any) -> str:
    return _DEFAULT_CLIENT.complete(prompt, **kwargs)


def generate(prompt: str, **kwargs: Any) -> str:
    return _DEFAULT_CLIENT.generate(prompt, **kwargs)


def chat(messages: Sequence[Mapping[str, Any]], **kwargs: Any) -> str:
    return _DEFAULT_CLIENT.chat(messages, **kwargs)


def _messages_to_prompt(messages: Sequence[Mapping[str, Any]]) -> str:
    if not messages:
        return ""

    lines: list[str] = []
    for message in messages:
        role = str(message.get("role", "user")).strip().lower()
        content = str(message.get("content", "")).strip()
        if not content:
            continue
        lines.append(f"{role}: {content}")

    if not lines:
        return ""
    return "\n".join(lines)


__all__ = [
    "LLMClient",
    "set_default_client",
    "get_default_client",
    "complete",
    "generate",
    "chat",
]
