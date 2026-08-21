"""
In-process async event bus backing the SSE stream.

The previous SSE endpoint emitted a synthetic heartbeat on a timer and nothing
else. This bus lets any request handler publish a real domain event (conflict
detected, conflict resolved, notice generated, mesh edit issued) that every
connected browser receives immediately.

Subscribers get bounded queues: a slow client drops its oldest events rather
than growing memory without limit or blocking the publisher.
"""

from __future__ import annotations

import asyncio
import contextlib
from typing import Any, AsyncIterator, Optional

from diya_core.models import utcnow_iso

MAX_QUEUED_EVENTS = 100


class EventBus:
    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[dict[str, Any]]] = set()
        self._history: list[dict[str, Any]] = []

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)

    def recent(self, limit: int = 20) -> list[dict[str, Any]]:
        return self._history[-limit:]

    async def publish(self, event_type: str, payload: Optional[dict] = None) -> dict:
        event = {
            "type": event_type,
            "timestamp": utcnow_iso(),
            **(payload or {}),
        }
        self._history.append(event)
        del self._history[:-200]

        for queue in list(self._subscribers):
            if queue.full():
                with contextlib.suppress(asyncio.QueueEmpty):
                    queue.get_nowait()
            with contextlib.suppress(asyncio.QueueFull):
                queue.put_nowait(event)

        return event

    @contextlib.asynccontextmanager
    async def subscribe(self) -> AsyncIterator[asyncio.Queue[dict[str, Any]]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=MAX_QUEUED_EVENTS)
        self._subscribers.add(queue)
        try:
            yield queue
        finally:
            self._subscribers.discard(queue)


event_bus = EventBus()
