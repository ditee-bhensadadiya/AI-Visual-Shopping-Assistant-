"""Environment-backed settings for the Phase 2 API foundation."""
from dataclasses import dataclass
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)


@dataclass(frozen=True)
class Settings:
    cors_origins: tuple[str, ...]
    log_level: int

    @classmethod
    def from_env(cls) -> "Settings":
        raw_origins = os.getenv(
            "BACKEND_CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        )
        origins = tuple(origin.strip().rstrip("/") for origin in raw_origins.split(",") if origin.strip())
        raw_level = os.getenv("LOG_LEVEL", "INFO").upper()
        level = getattr(logging, raw_level, None)
        if not isinstance(level, int):
            raise ValueError("LOG_LEVEL must be a valid Python logging level")
        return cls(cors_origins=origins, log_level=level)

