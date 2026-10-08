"""Asyncio-safe in-memory TTL cache.

Every read returns an envelope: {"data", "stale", "fetched_at"}.
Callers MUST surface `stale` to the frontend — stale flags over fake data.
"""

import asyncio
import time


class TTLCache:
    def __init__(self) -> None:
        self._store: dict[str, tuple[object, float]] = {}
        self._lock = asyncio.Lock()

    async def set(self, key: str, value: object) -> None:
        async with self._lock:
            self._store[key] = (value, time.time())

    async def peek(self, key: str):
        """Return the raw value or None. No staleness info — use read()."""
        async with self._lock:
            entry = self._store.get(key)
            return entry[0] if entry else None

    async def read(self, key: str, ttl: float) -> dict:
        async with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return {"data": None, "stale": True, "fetched_at": None}
            value, ts = entry
            return {
                "data": value,
                "stale": (time.time() - ts) > ttl,
                "fetched_at": ts,
            }
