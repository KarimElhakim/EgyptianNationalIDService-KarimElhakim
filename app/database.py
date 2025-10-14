"""Database utilities for API key management and usage tracking."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from threading import Lock
from typing import Dict, Iterable, Optional

from .config import settings


class Database:
    """Lightweight wrapper around SQLite for API key metadata."""

    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        self._lock = Lock()

    def _get_connection(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialise(self, default_keys: Iterable[tuple[str, str]], rate_limit: int) -> None:
        """Create the schema and insert default API keys when missing."""

        with self._lock, self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS api_keys (
                    key TEXT PRIMARY KEY,
                    owner TEXT NOT NULL,
                    rate_limit INTEGER NOT NULL,
                    total_requests INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            for key_value, owner in default_keys:
                conn.execute(
                    """
                    INSERT INTO api_keys (key, owner, rate_limit)
                    VALUES (?, ?, ?)
                    ON CONFLICT(key) DO UPDATE SET owner=excluded.owner
                    """,
                    (key_value, owner, rate_limit),
                )

    def get_api_key(self, key: str) -> Optional[Dict[str, object]]:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT key, owner, rate_limit, total_requests FROM api_keys WHERE key = ?",
                (key,),
            ).fetchone()
            return dict(row) if row else None

    def increment_usage(self, key: str) -> None:
        with self._lock, self._get_connection() as conn:
            conn.execute(
                """
                UPDATE api_keys
                   SET total_requests = total_requests + 1,
                       updated_at = CURRENT_TIMESTAMP
                 WHERE key = ?
                """,
                (key,),
            )
            conn.commit()

    def get_usage(self, key: str) -> Optional[int]:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT total_requests FROM api_keys WHERE key = ?",
                (key,),
            ).fetchone()
            return int(row[0]) if row else None


database = Database(settings.database_path)
