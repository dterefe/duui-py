from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import AsyncIterator

from duui_py.logging.core import get_event_logger_or_none


class Metrics:
    async def count(self, name: str, value: float = 1, **tags: str) -> None:
        await self.emit("processing", name, value, "count", tags=tags)

    async def gauge(self, name: str, value: float, unit: str = "value", **tags: str) -> None:
        await self.emit("processing", name, value, unit, tags=tags)

    async def timing(self, name: str, elapsed_ms: int, **tags: str) -> None:
        await self.emit("processing", name, elapsed_ms, "milliseconds", interval_ms=elapsed_ms, tags=tags)

    async def emit(
        self,
        category: str,
        name: str,
        value: float,
        unit: str,
        *,
        interval_ms: int = 0,
        tags: dict[str, str] | None = None,
    ) -> None:
        logger = get_event_logger_or_none()
        if logger is None:
            return
        await logger.metric(category, name, value, unit, interval_ms, tags or {})

    @asynccontextmanager
    async def timer(self, name: str, **tags: str) -> AsyncIterator[None]:
        started = time.perf_counter()
        try:
            yield
        finally:
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            await self.timing(name, elapsed_ms, **tags)


metrics = Metrics()
