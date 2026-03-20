"""
app/db/supabase_client.py

Supabase client singleton with safe local fallback.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Any

try:
    from config.settings import get_settings
except ImportError:  # pragma: no cover - alternate package root
    from app.config.settings import get_settings


@dataclass
class _InMemoryTable:
    name: str
    _rows: list[dict[str, Any]] = field(default_factory=list)
    _pending_insert: list[dict[str, Any]] | None = None
    _pending_filters: dict[str, Any] = field(default_factory=dict)
    _pending_select_columns: str | None = None

    def insert(self, payload: dict[str, Any] | list[dict[str, Any]]):
        if isinstance(payload, list):
            self._pending_insert = [dict(item) for item in payload]
        else:
            self._pending_insert = [dict(payload)]
        return self

    def select(self, columns: str = "*"):
        self._pending_select_columns = columns
        return self

    def eq(self, column: str, value: Any):
        self._pending_filters[column] = value
        return self

    def single(self):
        data, error = self.execute()
        if error is not None:
            return {"data": None, "error": error}
        if not data:
            return {"data": None, "error": {"message": "No rows"}}
        return {"data": data[0], "error": None}

    def execute(self):
        if self._pending_insert is not None:
            self._rows.extend(self._pending_insert)
            inserted = self._pending_insert
            self._pending_insert = None
            return inserted, None

        rows = list(self._rows)
        for key, value in self._pending_filters.items():
            rows = [row for row in rows if row.get(key) == value]

        self._pending_filters = {}
        return rows, None


@dataclass
class _InMemorySupabase:
    _tables: dict[str, _InMemoryTable] = field(default_factory=dict)

    def table(self, name: str) -> _InMemoryTable:
        if name not in self._tables:
            self._tables[name] = _InMemoryTable(name=name)
        return self._tables[name]

    # Common API alias in supabase-py
    from_ = table


_LOCK = Lock()
_CLIENT: Any = None


def get_client():
    global _CLIENT
    if _CLIENT is not None:
        return _CLIENT

    with _LOCK:
        if _CLIENT is not None:
            return _CLIENT

        settings = get_settings()
        if settings.has_supabase:
            try:
                from supabase import create_client  # type: ignore

                _CLIENT = create_client(settings.supabase_url, settings.supabase_service_key)
                return _CLIENT
            except Exception:
                pass

        _CLIENT = _InMemorySupabase()
        return _CLIENT


def reset_client_for_tests() -> None:
    global _CLIENT
    with _LOCK:
        _CLIENT = None


__all__ = ["get_client", "reset_client_for_tests"]
