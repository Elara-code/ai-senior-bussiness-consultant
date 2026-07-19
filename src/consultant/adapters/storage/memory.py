from collections.abc import AsyncIterator

from consultant.domain.common import NotFound


class InMemoryObjectStore:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.content_types: dict[str, str] = {}

    async def put_stream(
        self, *, key: str, stream: AsyncIterator[bytes], content_type: str
    ) -> None:
        parts = [part async for part in stream]
        self.objects[key] = b"".join(parts)
        self.content_types[key] = content_type

    async def get_stream(self, *, key: str) -> AsyncIterator[bytes]:
        try:
            payload = self.objects[key]
        except KeyError as error:
            raise NotFound("Object not found") from error
        yield payload

    async def delete(self, *, key: str) -> None:
        self.objects.pop(key, None)
        self.content_types.pop(key, None)
