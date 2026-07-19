import asyncio
from collections.abc import AsyncIterator
from uuid import UUID

from consultant.ports.event_store import RunEvent


class InMemoryEventStore:
    def __init__(self) -> None:
        self._events: dict[UUID, list[RunEvent]] = {}
        self._conditions: dict[UUID, asyncio.Condition] = {}

    async def append(self, event: RunEvent) -> None:
        events = self._events.setdefault(event.run_id, [])
        if events and event.sequence <= events[-1].sequence:
            raise ValueError("Event sequence must be strictly increasing")
        events.append(event)
        condition = self._conditions.setdefault(event.run_id, asyncio.Condition())
        async with condition:
            condition.notify_all()

    async def list_after(self, *, run_id: UUID, sequence: int) -> list[RunEvent]:
        return [event for event in self._events.get(run_id, []) if event.sequence > sequence]

    async def subscribe(self, *, run_id: UUID, after_sequence: int) -> AsyncIterator[RunEvent]:
        cursor = after_sequence
        condition = self._conditions.setdefault(run_id, asyncio.Condition())
        while True:
            available = await self.list_after(run_id=run_id, sequence=cursor)
            for event in available:
                cursor = event.sequence
                yield event
                if event.terminal:
                    return
            async with condition:
                await condition.wait()
