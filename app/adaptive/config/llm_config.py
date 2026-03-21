"""
app/config/llm_config.py

LLM runtime configuration sourced from environment variables.
"""

from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class LLMConfig:
    model: str = "mock-local"
    api_key: str | None = None
    timeout_seconds: float = 10.0
    max_retries: int = 3


def get_llm_config() -> LLMConfig:
    model = os.getenv("ANTHROPIC_MODEL", "mock-local")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    timeout_seconds = _to_float(os.getenv("LLM_TIMEOUT_SECONDS"), default=10.0)
    max_retries = max(0, int(_to_float(os.getenv("LLM_MAX_RETRIES"), default=3.0)))
    return LLMConfig(
        model=model,
        api_key=api_key,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
    )


def _to_float(value: str | None, default: float) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


__all__ = ["LLMConfig", "get_llm_config"]


