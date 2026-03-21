"""
app/utils/logger.py

Small logging helper with consistent formatting and request-id support.
"""

from __future__ import annotations

import logging
from contextvars import ContextVar

from app.adaptive.config.settings import get_settings


_REQUEST_ID: ContextVar[str | None] = ContextVar("request_id", default=None)
_CONFIGURED = False


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _REQUEST_ID.get() or "-"
        return True


def configure_logging(level: str | None = None) -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    settings = get_settings()
    resolved_level = (level or settings.log_level or "INFO").upper()

    root_logger = logging.getLogger()
    root_logger.setLevel(resolved_level)

    if not root_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s %(levelname)s [req:%(request_id)s] %(name)s - %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
        )
        root_logger.addHandler(handler)

    request_filter = RequestIdFilter()
    for handler in root_logger.handlers:
        handler.addFilter(request_filter)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)


def set_request_id(request_id: str | None) -> None:
    cleaned = (request_id or "").strip()
    _REQUEST_ID.set(cleaned or None)


def get_request_id() -> str | None:
    return _REQUEST_ID.get()


def clear_request_id() -> None:
    _REQUEST_ID.set(None)


__all__ = [
    "configure_logging",
    "get_logger",
    "set_request_id",
    "get_request_id",
    "clear_request_id",
]


