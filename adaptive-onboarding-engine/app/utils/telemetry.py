"""
app/utils/telemetry.py

Minimal no-op telemetry helpers for local development and tests.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any

try:
    from utils.logger import get_logger
except ImportError:  # pragma: no cover - alternate package root
    from app.utils.logger import get_logger


logger = get_logger(__name__)


@dataclass
class Span:
    name: str
    attributes: dict[str, Any] = field(default_factory=dict)
    started_at: float = field(default_factory=perf_counter)
    finished_at: float | None = None
    error: str | None = None

    @property
    def duration_ms(self) -> float | None:
        if self.finished_at is None:
            return None
        return round((self.finished_at - self.started_at) * 1000.0, 3)


@contextmanager
def trace_span(name: str, **attributes: Any):
    span = Span(name=name, attributes=dict(attributes))
    try:
        yield span
    except Exception as error:
        span.error = str(error)
        raise
    finally:
        span.finished_at = perf_counter()
        logger.debug(
            "span=%s duration_ms=%s error=%s attrs=%s",
            span.name,
            span.duration_ms,
            span.error,
            span.attributes,
        )


def emit_event(name: str, **attributes: Any) -> None:
    logger.info("event=%s attrs=%s", name, attributes)


__all__ = ["Span", "trace_span", "emit_event"]
