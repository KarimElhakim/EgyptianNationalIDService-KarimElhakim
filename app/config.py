"""Application configuration module."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Tuple


def _parse_default_api_keys(value: str | None) -> List[Tuple[str, str]]:
    """Parse the DEFAULT_API_KEYS environment variable.

    The format is a comma-separated list of items in the form ``key:owner``.
    When the owner is omitted, ``"default"`` is used instead.
    """

    if not value:
        return [("demo-key-123", "Demo account")]

    result: List[Tuple[str, str]] = []
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        if ":" in item:
            key, owner = item.split(":", 1)
            result.append((key.strip(), owner.strip() or "default"))
        else:
            result.append((item, "default"))
    return result or [("demo-key-123", "Demo account")]


@dataclass(slots=True)
class Settings:
    """Runtime settings sourced from environment variables."""

    api_rate_limit_per_minute: int = int(os.getenv("API_RATE_LIMIT_PER_MINUTE", "60"))
    default_api_keys: List[Tuple[str, str]] = _parse_default_api_keys(
        os.getenv("DEFAULT_API_KEYS")
    )
    database_path: str = os.getenv("DATABASE_PATH", "data/app.db")


settings = Settings()
