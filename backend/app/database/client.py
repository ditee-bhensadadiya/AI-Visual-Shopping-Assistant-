"""Configuration and construction for the server-side Supabase client."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any
from urllib.parse import urlparse


@dataclass(frozen=True)
class SupabaseSettings:
    """Credentials for trusted backend access; never use these in a browser."""

    url: str
    service_role_key: str

    @classmethod
    def from_env(cls) -> "SupabaseSettings":
        url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        if not url or not key:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be configured"
            )
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("SUPABASE_URL must be an absolute HTTP(S) URL")
        return cls(url=url, service_role_key=key)


@lru_cache(maxsize=1)
def get_supabase_client() -> Any:
    """Return the cached official Supabase client, importing its SDK on demand."""
    settings = SupabaseSettings.from_env()
    try:
        from supabase import create_client
    except ImportError as exc:
        raise RuntimeError(
            "Supabase SDK is missing; install backend/requirements.txt"
        ) from exc
    return create_client(settings.url, settings.service_role_key)


def reset_supabase_client_cache() -> None:
    """Clear the cached client (useful after environment changes and in tests)."""
    get_supabase_client.cache_clear()
