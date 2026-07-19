import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID

from redis.asyncio import Redis

from consultant.ports.event_store import RunEvent


class RedisStreamEventStore:
    def __init__(self, redis: Redis, *, prefix: str = "consultant:run-events") -> None:
        self._redis = redis
        self._prefix = prefix

    def _key(self, run_id: UUID) -> str:
        return f"{self._prefix}:{run_id}"

    async def append(self, event: RunEvent) -> None:
        await self._redis.xadd(
            self._key(event.run_id),
            {
                "sequence": str(event.sequence),
                "event_type": event.event_type,
                "payload": json.dumps(event.payload, ensure_ascii=False),
                "occurred_at": event.occurred_at.isoformat(),
            },
            maxlen=2000,
            approximate=True,
        )

    async def list_after(self, *, run_id: UUID, sequence: int) -> list[RunEvent]:
        rows = cast(
            list[tuple[bytes, dict[bytes, bytes]]],
            await self._redis.xrange(self._key(run_id)),
        )
        events = [self._decode(run_id, fields) for _, fields in rows]
        return [event for event in events if event.sequence > sequence]

    async def subscribe(self, *, run_id: UUID, after_sequence: int) -> AsyncIterator[RunEvent]:
        cursor = after_sequence
        stream_id = "0-0"
        while True:
            existing = await self.list_after(run_id=run_id, sequence=cursor)
            for event in existing:
                cursor = event.sequence
                yield event
                if event.terminal:
                    return
            response: Any = await self._redis.xread({self._key(run_id): stream_id}, block=15000)
            if response:
                stream_id = response[0][1][-1][0].decode()

    @staticmethod
    def _decode(run_id: UUID, fields: dict[bytes, bytes]) -> RunEvent:
        return RunEvent(
            run_id=run_id,
            sequence=int(fields[b"sequence"]),
            event_type=fields[b"event_type"].decode(),
            payload=json.loads(fields[b"payload"]),
            occurred_at=datetime.fromisoformat(fields[b"occurred_at"].decode()).astimezone(UTC),
        )
