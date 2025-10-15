from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal


def _getenv_str(key: str, default: str) -> str:
    v = os.getenv(key)
    return v if v is not None and v != "" else default


def _getenv_int(key: str, default: int) -> int:
    v = os.getenv(key)
    try:
        return int(v) if v is not None and v != "" else default
    except Exception:
        return default


def _getenv_float(key: str, default: float) -> float:
    v = os.getenv(key)
    try:
        return float(v) if v is not None and v != "" else default
    except Exception:
        return default


def _getenv_bool(key: str, default: bool) -> bool:
    v = os.getenv(key)
    if v is None or v == "":
        return default
    return str(v).lower() in ("1", "true", "yes", "y", "on")


@dataclass(frozen=True)
class Settings:
    app_env: Literal["dev", "prod", "test"] = "dev"
    port: int = 8000

    # LLM
    llm_provider: Literal["openai", "anthropic"] = "openai"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    anthropic_model: str = "claude-3-5-sonnet-20240620"

    # Scraping
    mercari_base_url: str = "https://jp.mercari.com/search"
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    accept_language: str = "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7"

    http_timeout: float = 15.0
    http_max_retries: int = 3
    http_backoff_seconds: float = 0.5

    # Cache
    cache_dir: str = "/app/data/cache"
    requests_cache_expire_seconds: int = 3600

    # Playwright
    playwright_browsers_path: str = "/ms-playwright"
    playwright_headless: bool = True

    # Proxy (optional)
    http_proxy: str = ""
    https_proxy: str = ""
    no_proxy: str = "localhost,127.0.0.1"


_settings: Settings | None = None


def get_settings() -> Settings:
    """Env → Settings. 첫 호출 시만 생성(간단한 싱글톤)."""
    global _settings
    if _settings is not None:
        return _settings

    s = Settings(
        app_env=_getenv_str("APP_ENV", "dev"),  # type: ignore[arg-type]
        port=_getenv_int("PORT", 8000),
        llm_provider=_getenv_str("LLM_PROVIDER", "openai"),  # type: ignore[arg-type]
        openai_api_key=_getenv_str("OPENAI_API_KEY", ""),
        anthropic_api_key=_getenv_str("ANTHROPIC_API_KEY", ""),
        openai_model=_getenv_str("OPENAI_MODEL", "gpt-4o-mini"),
        anthropic_model=_getenv_str("ANTHROPIC_MODEL", "claude-3-5-sonnet-20240620"),
        mercari_base_url=_getenv_str("MERCARI_BASE_URL", "https://jp.mercari.com/search"),
        user_agent=_getenv_str("USER_AGENT", Settings.user_agent),
        accept_language=_getenv_str("ACCEPT_LANGUAGE", Settings.accept_language),
        http_timeout=_getenv_float("HTTP_TIMEOUT", 15.0),
        http_max_retries=_getenv_int("HTTP_MAX_RETRIES", 3),
        http_backoff_seconds=_getenv_float("HTTP_BACKOFF_SECONDS", 0.5),
        cache_dir=_getenv_str("CACHE_DIR", "/app/data/cache"),
        requests_cache_expire_seconds=_getenv_int("REQUESTS_CACHE_EXPIRE_SECONDS", 3600),
        playwright_browsers_path=_getenv_str("PLAYWRIGHT_BROWSERS_PATH", "/ms-playwright"),
        playwright_headless=_getenv_bool("PLAYWRIGHT_HEADLESS", True),
        http_proxy=_getenv_str("HTTP_PROXY", ""),
        https_proxy=_getenv_str("HTTPS_PROXY", ""),
        no_proxy=_getenv_str("NO_PROXY", "localhost,127.0.0.1"),
    )
    _settings = s
    return s
