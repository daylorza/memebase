"""Shared helpers for third-party API clients: gap rate-limiting."""

import asyncio
import time


class GapLimiter:
    """Enforce a minimum gap between calls to one source (asyncio-safe)."""

    def __init__(self, min_gap: float) -> None:
        self._min_gap = min_gap
        self._lock = asyncio.Lock()
        self._last = 0.0

    async def wait(self) -> None:
        async with self._lock:
            now = time.monotonic()
            delay = self._min_gap - (now - self._last)
            if delay > 0:
                await asyncio.sleep(delay)
            self._last = time.monotonic()
