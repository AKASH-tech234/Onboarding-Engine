"""
app/utils/retry.py

Retry helpers for transient operations.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, TypeVar
from collections.abc import Awaitable, Callable


T = TypeVar("T")


def with_retry(
    fn: Callable[[], T],
    *,
    max_attempts: int = 3,
    initial_delay_seconds: float = 0.25,
    backoff_multiplier: float = 2.0,
    retry_on: tuple[type[Exception], ...] = (Exception,),
) -> T:
    """
    Retry a synchronous callable with exponential backoff.
    """
    attempts = max(1, int(max_attempts))
    delay = max(0.0, float(initial_delay_seconds))

    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except retry_on as error:  # type: ignore[misc]
            last_error = error
            if attempt >= attempts:
                break
            if delay > 0:
                time.sleep(delay)
            delay *= max(1.0, float(backoff_multiplier))

    assert last_error is not None
    raise last_error


async def awith_retry(
    fn: Callable[[], Awaitable[T]],
    *,
    max_attempts: int = 3,
    initial_delay_seconds: float = 0.25,
    backoff_multiplier: float = 2.0,
    retry_on: tuple[type[Exception], ...] = (Exception,),
) -> T:
    """
    Retry an async callable with exponential backoff.
    """
    attempts = max(1, int(max_attempts))
    delay = max(0.0, float(initial_delay_seconds))

    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return await fn()
        except retry_on as error:  # type: ignore[misc]
            last_error = error
            if attempt >= attempts:
                break
            if delay > 0:
                await asyncio.sleep(delay)
            delay *= max(1.0, float(backoff_multiplier))

    assert last_error is not None
    raise last_error


def retry(
    *,
    max_attempts: int = 3,
    initial_delay_seconds: float = 0.25,
    backoff_multiplier: float = 2.0,
    retry_on: tuple[type[Exception], ...] = (Exception,),
):
    """
    Decorator for synchronous callables.
    """

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        def wrapped(*args: Any, **kwargs: Any) -> T:
            return with_retry(
                lambda: fn(*args, **kwargs),
                max_attempts=max_attempts,
                initial_delay_seconds=initial_delay_seconds,
                backoff_multiplier=backoff_multiplier,
                retry_on=retry_on,
            )

        return wrapped

    return decorator


def aretry(
    *,
    max_attempts: int = 3,
    initial_delay_seconds: float = 0.25,
    backoff_multiplier: float = 2.0,
    retry_on: tuple[type[Exception], ...] = (Exception,),
):
    """
    Decorator for async callables.
    """

    def decorator(fn: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        async def wrapped(*args: Any, **kwargs: Any) -> T:
            return await awith_retry(
                lambda: fn(*args, **kwargs),
                max_attempts=max_attempts,
                initial_delay_seconds=initial_delay_seconds,
                backoff_multiplier=backoff_multiplier,
                retry_on=retry_on,
            )

        return wrapped

    return decorator


__all__ = ["with_retry", "awith_retry", "retry", "aretry"]


