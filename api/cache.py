"""Simple time-based cache for read-heavy API responses."""
from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any


class TTLCache:
    """Thread-safe(ish) single-value TTL cache for async context (single-process)."""

    def __init__(self, ttl_seconds: int) -> None:
        self._ttl = ttl_seconds
        self._value: Any = None
        self._ts: float = 0.0

    def get(self) -> Any:
        if self._value is not None and (time.monotonic() - self._ts) < self._ttl:
            return self._value
        return None

    def set(self, value: Any) -> None:
        self._value = value
        self._ts = time.monotonic()

    def invalidate(self) -> None:
        self._value = None
        self._ts = 0.0