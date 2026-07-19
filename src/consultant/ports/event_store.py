from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RunEvent:
    run_id: UUID
    sequence: int
    event_type: str
    payload: dict[str, Any]
    occurred_at: datetime

    @property
    def terminal(self) -> bool:
        return self.event_type in {"run.completed", "run.failed", "run.cancelled"}


class EventStore(Protocol):
    async def append(self, event: RunEvent) -> None: ...

    async def list_after(self, *, run_id: UUID, sequence: int) -> list[RunEvent]: ...

    def subscribe(self, *, run_id: UUID, after_sequence: int) -> AsyncIterator[RunEvent]: ...
