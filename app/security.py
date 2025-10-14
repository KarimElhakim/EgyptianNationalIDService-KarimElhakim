"""Authentication and rate limiting helpers."""

from __future__ import annotations

import time
from dataclasses import dataclass
from threading import Lock
from typing import Callable, Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from .config import settings
from .database import database


@dataclass(slots=True)
class RateLimitState:
    start_time: float
    count: int


class RateLimitExceededError(Exception):
    """Raised when an API key has exhausted its rate limit."""


class RateLimiter:
    """In-memory fixed-window rate limiter."""

    def __init__(self, window_seconds: int = 60) -> None:
        self.window_seconds = window_seconds
        self._state: Dict[str, RateLimitState] = {}
        self._lock = Lock()

    def check(self, key: str, limit: int) -> None:
        now = time.monotonic()
        with self._lock:
            state = self._state.get(key)
            if state is None or now - state.start_time >= self.window_seconds:
                self._state[key] = RateLimitState(start_time=now, count=1)
                return

            if state.count >= limit:
                raise RateLimitExceededError()

            state.count += 1


rate_limiter = RateLimiter()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_current_api_key(*, increment_usage: bool = True) -> Callable[[str], dict[str, object]]:
    """Return a dependency that authenticates the request."""

    def dependency(api_key: str = Depends(api_key_header)) -> dict[str, object]:
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key"
            )

        record = database.get_api_key(api_key)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
            )

        limit = (
            int(record["rate_limit"])
            if record.get("rate_limit") is not None
            else settings.api_rate_limit_per_minute
        )

        try:
            rate_limiter.check(api_key, limit)
        except RateLimitExceededError as exc:  # pragma: no cover - FastAPI handles HTTPException
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
            ) from exc

        if increment_usage:
            database.increment_usage(api_key)

        return record

    return dependency
