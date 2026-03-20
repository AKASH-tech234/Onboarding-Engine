"""
app/config/settings.py

Centralized application settings loaded from environment variables.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import os


@dataclass(frozen=True)
class Settings:
    environment: str = "development"
    log_level: str = "INFO"

    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False

    allowed_origins: tuple[str, ...] = field(default_factory=lambda: ("*",))

    graph_version: str = "v1"
    graph_data_dir: str | None = None

    api_auth_token: str | None = None
    auth_enabled: bool = False
    rate_limit_enabled: bool = False
    rate_limit_per_minute: int = 60

    redis_url: str | None = None

    supabase_url: str | None = None
    supabase_service_key: str | None = None

    anthropic_api_key: str | None = None
    anthropic_model: str = "mock-local"
    llm_timeout_seconds: float = 10.0
    llm_max_retries: int = 3

    @property
    def is_production(self) -> bool:
        return self.environment.strip().lower() == "production"

    @property
    def has_supabase(self) -> bool:
        return bool(self.supabase_url and self.supabase_service_key)

    @property
    def has_redis(self) -> bool:
        return bool(self.redis_url)


def load_settings() -> Settings:
    return Settings(
        environment=_env("ENVIRONMENT", "development"),
        log_level=_env("LOG_LEVEL", "INFO").upper(),
        host=_env("HOST", "0.0.0.0"),
        port=_to_int(_env("PORT", "8000"), 8000),
        reload=_to_bool(_env("RELOAD", "false"), default=False),
        allowed_origins=_split_csv(_env("ALLOWED_ORIGINS", "*")),
        graph_version=_env("GRAPH_VERSION", "v1"),
        graph_data_dir=_env_optional("GRAPH_DATA_DIR"),
        api_auth_token=_env_optional("API_AUTH_TOKEN") or _env_optional("JWT_SECRET"),
        auth_enabled=_to_bool(_env_optional("AUTH_ENABLED"), default=False),
        rate_limit_enabled=_to_bool(_env_optional("RATE_LIMIT_ENABLED"), default=False),
        rate_limit_per_minute=max(1, _to_int(_env_optional("RATE_LIMIT_PER_MINUTE"), 60)),
        redis_url=_env_optional("REDIS_URL"),
        supabase_url=_env_optional("SUPABASE_URL"),
        supabase_service_key=_env_optional("SUPABASE_SERVICE_KEY"),
        anthropic_api_key=_env_optional("ANTHROPIC_API_KEY"),
        anthropic_model=_env("ANTHROPIC_MODEL", "mock-local"),
        llm_timeout_seconds=_to_float(_env_optional("LLM_TIMEOUT_SECONDS"), 10.0),
        llm_max_retries=max(0, _to_int(_env_optional("LLM_MAX_RETRIES"), 3)),
    )


def _env(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None:
        return default
    cleaned = value.strip()
    return cleaned if cleaned else default


def _env_optional(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned if cleaned else None


def _split_csv(value: str) -> tuple[str, ...]:
    parts = [part.strip() for part in value.split(",") if part.strip()]
    return tuple(parts) if parts else ("*",)


def _to_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    lowered = str(value).strip().lower()
    if lowered in {"1", "true", "yes", "on"}:
        return True
    if lowered in {"0", "false", "no", "off"}:
        return False
    return default


def _to_int(value: str | None, default: int) -> int:
    try:
        return int(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def _to_float(value: str | None, default: float) -> float:
    try:
        return float(value) if value is not None else default
    except (TypeError, ValueError):
        return default


_SETTINGS = load_settings()


def get_settings() -> Settings:
    return _SETTINGS


def refresh_settings() -> Settings:
    global _SETTINGS
    _SETTINGS = load_settings()
    return _SETTINGS


__all__ = ["Settings", "get_settings", "load_settings", "refresh_settings"]
